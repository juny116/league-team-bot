import discord
import random


##### Pick user #####
class UserPickButton(discord.ui.Button):
    def __init__(self, name, include=False, style=discord.ButtonStyle.grey):
        super().__init__(label=name, style=style)
        self.include = include

    async def callback(self, interaction):
        if self.include:
            self.style = discord.ButtonStyle.grey
            self.include = False
            interaction.client.include_list.remove(self.label)
        else:
            self.style = discord.ButtonStyle.green
            self.include = True
            interaction.client.include_list.append(self.label)
        await interaction.response.edit_message(view=self.view)
        # await interaction.followup.send(self.label, ephemeral=True)


class MakeButton(discord.ui.Button):
    def __init__(self):
        super().__init__(label="MakeTeam!", style=discord.ButtonStyle.grey, emoji="👍")

    async def callback(self, interaction):
        # make team based on ELO
        content = ""
        if len(interaction.client.include_list) != 10:
            content = "*** Include 10 users! ***"
            await interaction.response.edit_message(content=content, view=self.view)
        else:
            min_diff = interaction.client.make_team()
            team1 = interaction.client.team1
            team2 = interaction.client.team2
            await interaction.response.edit_message(
                content=f"*** ELO difference: {min_diff} ***",
                view=TeamView(team1, team2),
            )


class SelectMemberView(discord.ui.View):
    def __init__(self, user_list, include_list):
        super().__init__()
        self.user_list = user_list
        for user in self.user_list:
            if user in include_list:
                self.add_item(
                    UserPickButton(
                        user,
                        include=True,
                        style=discord.ButtonStyle.green,
                    )
                )
            else:
                self.add_item(
                    UserPickButton(
                        user,
                        include=False,
                    )
                )
        self.add_item(MakeButton())
        self.add_item(CancelButton())


##### Pick team #####
class UserTeamButton(discord.ui.Button):
    def __init__(self, name, team=None, disabled=False, style=discord.ButtonStyle.grey):
        self.team = team
        if self.team == 1:
            style = discord.ButtonStyle.blurple
        elif self.team == 2:
            style = discord.ButtonStyle.red
        super().__init__(label=name, style=style, disabled=disabled)

    async def callback(self, interaction):
        if self.team == 1:
            self.style = discord.ButtonStyle.red
            self.team = 2
        elif self.team == 2:
            self.style = discord.ButtonStyle.blurple
            self.team = 1
        await interaction.response.edit_message(view=self.view)
        # await interaction.followup.send(self.label, ephemeral=True)


class StartButton(discord.ui.Button):
    def __init__(self):
        super().__init__(label="Start!", style=discord.ButtonStyle.grey, emoji="👍")

    async def callback(self, interaction):
        # update team
        team1 = []
        team2 = []
        for item in self.view.children:
            if isinstance(item, UserTeamButton):
                if item.team == 1:
                    team1.append(item.label)
                elif item.team == 2:
                    team2.append(item.label)
        if len(team1) != 5 or len(team2) != 5:
            await interaction.response.edit_message(
                content="*** Include 5 users in each team! ***", view=self.view
            )
        else:
            interaction.client.team1 = team1
            interaction.client.team2 = team2
            content = "*** Pick the team that won the game! ***"
            await interaction.response.edit_message(
                content=content, view=WinView(team1, team2)
            )


class CancelButton(discord.ui.Button):
    def __init__(self):
        super().__init__(label="Cancel!", style=discord.ButtonStyle.grey, emoji="👎")

    async def callback(self, interaction):
        await interaction.response.edit_message(content="*** Canceled ***", view=None)


class TeamView(discord.ui.View):
    def __init__(self, team1=None, team2=None):
        super().__init__()
        for user in team1:
            self.add_item(UserTeamButton(user, team=1))
        for user in team2:
            self.add_item(UserTeamButton(user, team=2))
        self.add_item(StartButton())
        self.add_item(CancelButton())


##### Pick win #####
class WinTeamButton(discord.ui.Button):
    def __init__(self, name, style=discord.ButtonStyle.grey):
        super().__init__(label=name, style=style)
        self.name = name

    async def callback(self, interaction):
        for item in self.view.children:
            if isinstance(item, WinTeamButton):
                item.style = discord.ButtonStyle.grey
        if self.view.win == self.name:
            self.view.win = None
        else:
            self.style = discord.ButtonStyle.green
            self.view.win = self.name
        await interaction.response.edit_message(view=self.view)


class ConfirmButton(discord.ui.Button):
    def __init__(self):
        super().__init__(label="Confirm!", style=discord.ButtonStyle.grey, emoji="👍")

    async def callback(self, interaction):
        updated_users = interaction.client.end_match(self.view.win)
        # edit message to show result
        content = ""
        for user in updated_users:
            content += (
                f"{user['name']} ELO: {user['elo']} ({user['win']}/{user['lose']})\n"
            )
        await interaction.response.edit_message(content=content, view=None)
        # await interaction.response.edit_message(content="Confirm!", view=None)


class WinView(discord.ui.View):
    def __init__(self, team1=None, team2=None):
        super().__init__()
        self.win = None
        for user in team1:
            self.add_item(UserTeamButton(user, team=1, disabled=True))
        for user in team2:
            self.add_item(UserTeamButton(user, team=2, disabled=True))
        self.add_item(WinTeamButton("BlueTeam"))
        self.add_item(WinTeamButton("RedTeam"))
        self.add_item(ConfirmButton())
        self.add_item(CancelButton())


# class TeamSelect(discord.ui.Select):
#     def __init__(self, values=None):
#         super().__init__(placeholder="Select team", min_values=1, max_values=2)
#         self.add_option(label="Team1", value="Team1")
#         self.add_option(label="Team2", value="Team2")

#     async def callback(self, interaction):
#         await interaction.response.edit_message(view=TeamView())
