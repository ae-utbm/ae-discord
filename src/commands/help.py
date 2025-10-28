from __future__ import annotations

from typing import TYPE_CHECKING

from discord import Color, Embed, Interaction, app_commands
from discord.ext import commands

if TYPE_CHECKING:
    from src.main import AeBot


class HelpCog(commands.GroupCog, group_name="help"):
    def __init__(self, bot: AeBot):
        self.bot = bot

    @app_commands.command(
        name="help",
        description=(
            "Affiche la liste des commandes avec"
            " leurs sous-commandes et leurs description"
        ),
    )
    async def help(self, interaction: Interaction):
        embed = Embed(title="Aide du bot", color=Color.blue())

        for command in self.bot.tree.get_commands():
            if isinstance(command, app_commands.Group) and command.commands:
                subcommands = "\n".join(
                    f"  /{command.name} {sub.name} - {sub.description}"
                    for sub in command.commands
                )
                embed.add_field(
                    name=f"/{command.name} (groupe)", value=subcommands, inline=False
                )
            else:
                embed.add_field(
                    name=f"/{command.name}",
                    value=command.description or "Pas de description.",
                    inline=False,
                )

        await interaction.response.send_message(embed=embed, ephemeral=True)
