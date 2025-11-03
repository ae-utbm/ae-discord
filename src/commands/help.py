from __future__ import annotations

from typing import TYPE_CHECKING

from discord import Color, Embed, Interaction, app_commands
from discord.ext import commands

if TYPE_CHECKING:
    from src.main import AeBot


class HelpCog(commands.Cog):
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

        pres_commande = ["remove_member", "add_member"]
        admin_commande = ["passation", "arret", "create"]

        roles = interaction.user.roles
        n = len(roles)
        i = 0
        loop = True
        grade = 2  # 0 for admin 1 for presidence of clubs and 2 for member
        while i < n and loop:
            if roles[i].name == "Présidence AE":
                grade = 0
                loop = False
            elif roles[i].name.startswith("Responsable"):
                grade = 1
                loop = False
            else:
                pass
            i += 1

        for command in self.bot.tree.get_commands():
            if isinstance(command, app_commands.Group) and command.commands:
                for sub in command.commands:
                    if not (
                        (sub.name in pres_commande and grade > 1)
                        or (sub.name in admin_commande and grade != 0)
                    ):
                        subcommands = f"  {sub.description}\n"
                        embed.add_field(
                            name=f"/{command.name} {sub.name}",
                            value=subcommands,
                            inline=False,
                        )

            elif command.name != "role":
                embed.add_field(
                    name=f"/{command.name}",
                    value=command.description or "",
                    inline=False,
                )

        await interaction.response.send_message(embed=embed, ephemeral=True)
