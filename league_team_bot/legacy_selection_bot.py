import discord
import requests
from discord.utils import escape_mentions, remove_markdown
import json
from league_team_bot.configuration import configured
from omegaconf import DictConfig


class CalculatorButton(discord.ui.Button):
    def __init__(self, name, include=False, style=discord.ButtonStyle.red):
        super().__init__(label=name, style=style)
        self.include = include

    async def callback(self, interaction):
        if self.include:
            self.style = discord.ButtonStyle.red
            self.include = False
            interaction.client.include_list.remove(self.label)
        else:
            self.style = discord.ButtonStyle.green
            self.include = True
            interaction.client.include_list.append(self.label)
        await interaction.response.edit_message(view=self.view)
        # await interaction.followup.send(self.label, ephemeral=True)


class SimpleView(discord.ui.View):
    def __init__(self, user_list, include_list):
        super().__init__()
        self.user_list = user_list
        for user in self.user_list:
            if user in include_list:
                self.add_item(
                    CalculatorButton(
                        user,
                        include=True,
                        style=discord.ButtonStyle.green,
                    )
                )
            else:
                self.add_item(
                    CalculatorButton(
                        user,
                        include=False,
                    )
                )


class LOLBot(discord.Client):
    def __init__(self, config, intents):
        super().__init__(intents=intents)
        self.config = config
        self.user_list = self.config["riot"]["user_list"]
        self.include_list = []

    async def on_ready(self):
        print("Logged on as {0}!".format(self.user))
        print("User list: ", self.user_list)
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
            if message.content.startswith("!members"):
                view = SimpleView(self.user_list, self.include_list)
                await message.channel.send(view=view)
            if message.content.startswith("!include"):
                await message.channel.send(self.include_list)
            if self.user.mentioned_in(message):
                # remove mention from the message to get the command
                return


@configured
def main(config: DictConfig) -> None:
    intents = discord.Intents.all()
    client = LOLBot(config=config, intents=intents)
    client.run(config["discord"]["token"])


if __name__ == "__main__":
    main()
