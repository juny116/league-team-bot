import discord
import requests
from discord.utils import escape_mentions, remove_markdown
import json
from league_team_bot.configuration import configured
from omegaconf import DictConfig
from league_team_bot.player_store import LOLDatabase
from league_team_bot.team_selection_views import *
from multi_elo import EloPlayer, calc_elo
from time import sleep
import itertools
import asyncio
from .riot_client import RiotClient


class LOLBot(discord.Client):
    def __init__(self, config, intents):
        super().__init__(intents=intents)
        self.config = config
        self.include_list = []
        self.team1 = []
        self.team2 = []
        self.db = LOLDatabase(self.config["mongo"])
        self.k = 16

    async def on_ready(self):
        print("Logged on as {0}!".format(self.user))
        await self.change_presence(
            status=discord.Status.online, activity=discord.Game("대기중")
        )

    async def on_message(self, message):
        # Do not respond to ourselves
        if message.author == self.user:
            return
        # Do not respond to other system messages
        if message.content.startswith("***"):
            return
        # In case where command is sent
        elif message.content.startswith("!"):
            # Only respond to the command if it is sent to the bot by mentioning
            if message.content.startswith("!recent "):
                riot_id = message.content[len("!recent "):].strip()
                if "#" not in riot_id:
                    await message.channel.send("Usage: !recent game name#tag")
                    return
                name, tag = riot_id.rsplit("#", 1)
                try:
                    result = await asyncio.to_thread(RiotClient().recent_win_rate, name, tag)
                    await message.channel.send(f"Recent matches: {result['wins']}/{result['played']} wins")
                except (ValueError, requests.RequestException, KeyError):
                    await message.channel.send("Riot lookup unavailable. Check account, API key, or service status.")
                return
            if message.content.startswith("!make_team"):
                view = SelectMemberView(self.db.get_all_user_name(), self.include_list)
                await message.channel.send(view=view)
            if message.content.startswith("!members"):
                content = ""
                for user in self.db.get_all_user():
                    content += f"{user['name']} ELO: {user['elo']} ({user['win']}/{user['lose']})\n"
                await message.channel.send(content)
            if message.content.startswith("!add_user"):
                user_name = message.content.split()[1]
                name = self.db.add_user(user_name)
                await message.channel.send(name)
            if message.content.startswith("!include"):
                await message.channel.send(self.include_list)
            if message.content.startswith("!remove_last"):
                self.db.remove_last_match()
                await message.channel.send("*** Last match removed ***")
            if message.content.startswith("!set_k"):
                k = message.content.split()[1]
                self.k = int(k)
                await message.channel.send(f"*** k factor is set to {self.k} ***")
            if message.content.startswith("!recalc"):
                # k = message.content.split()[1]
                self.recalcuate_everything()
                await message.channel.send(
                    "*** Recalcuate everything based on match log ***"
                )
            if self.user.mentioned_in(message):
                # remove mention from the message to get the command
                return

    def make_team(self):
        # make team based on ELO
        user_list = []
        for user in self.include_list:
            user_list.append(self.db.get_user(user))
        user_name_list = [user["name"] for user in user_list]
        # create user_dict
        user_dict = {user["name"]: user for user in user_list}
        # user_list.sort(key=lambda x: x["elo"], reverse=True)
        # for all possible combination of splits, calculate the elo difference
        min_diff = 1000000
        for iter in itertools.combinations(user_name_list, 5):
            team1 = list(iter)
            team2 = list(set(user_name_list) - set(iter))
            # calculate elo difference
            team1_elo = sum([user_dict[user]["elo"] for user in team1])
            team2_elo = sum([user_dict[user]["elo"] for user in team2])
            diff = abs(team1_elo - team2_elo)
            if diff < min_diff:
                min_diff = diff
                self.team1 = team1
                self.team2 = team2

        return min_diff

    def end_match(self, win_team):
        if win_team == "BlueTeam":
            win = 0
        else:
            win = 1
        user_dict = {}
        for user in self.team1 + self.team2:
            user_dict[user] = self.db.get_user(user)
        new_elos = self.calculate_elo(user_dict, self.team1, self.team2, win, self.k)
        # update elo and win/lose
        for i, user in enumerate(self.team1):
            self.db.update_user(
                user,
                user_dict[user]["win"] + (1 - win),
                user_dict[user]["lose"] + win,
                new_elos[i],
            )

        for i, user in enumerate(self.team2):
            self.db.update_user(
                user,
                user_dict[user]["win"] + win,
                user_dict[user]["lose"] + (1 - win),
                new_elos[i + len(self.team1)],
            )

        # add match
        self.db.add_match(self.team1, self.team2, win_team)
        updated_user = self.db.get_all_user()
        return updated_user

    def calculate_elo(self, user_dict, team1, team2, win, k=4):
        players = []

        for user in team1:
            players.append(EloPlayer(place=win, elo=user_dict[user]["elo"]))
        for user in team2:
            players.append(EloPlayer(place=1 - win, elo=user_dict[user]["elo"]))

        new_elos = calc_elo(players, k)
        return new_elos

    def recalcuate_everything(self):
        # ret users from database
        self.db.reset_user()
        # recalculate based on match history
        matches = self.db.get_all_match()
        for match in matches:
            # get all users
            users = self.db.get_all_user()
            # create user_dict
            user_dict = {user["name"]: user for user in users}
            if match["win"] == "BlueTeam":
                win = 0
            else:
                win = 1
            new_elos = self.calculate_elo(
                user_dict, match["team1"], match["team2"], win, self.k
            )
            # update elo and win/lose
            for i, user in enumerate(match["team1"]):
                self.db.update_user(
                    user,
                    user_dict[user]["win"] + (1 - win),
                    user_dict[user]["lose"] + win,
                    new_elos[i],
                )
            for i, user in enumerate(match["team2"]):
                self.db.update_user(
                    user,
                    user_dict[user]["win"] + win,
                    user_dict[user]["lose"] + (1 - win),
                    new_elos[i + len(match["team1"])],
                )


@configured
def main(config: DictConfig) -> None:
    intents = discord.Intents.all()
    client = LOLBot(config=config, intents=intents)
    client.run(config["discord"]["token"])


if __name__ == "__main__":
    main()
