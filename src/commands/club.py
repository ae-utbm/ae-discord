from __future__ import annotations

from typing import TYPE_CHECKING

import discord
from discord import Interaction, Member, app_commands
from discord.app_commands import Choice, Transform, Transformer
from discord.ext import commands
from discord.ext.commands import BadArgument

from src.client import ClubSchema  # noqa TC001
from src.services.club import ClubService
from src.settings import Settings

if TYPE_CHECKING:
    from src.client import SithClient
    from src.main import AeBot


class ClubTransformer(Transformer):
    async def transform(
        self, interaction: Interaction[AeBot], value: int
    ) -> ClubSchema:
        club = await interaction.client.client.get_club(value)
        if not club:
            raise BadArgument("Ce club n'existe pas")
        return club


class ClubCog(commands.GroupCog, group_name="club"):
    def __init__(self, client: SithClient, bot: AeBot):
        self.club_service = ClubService(client, bot)
        self.settings = Settings()

    async def autocomplete_club(
        self, _interaction: Interaction, current: str
    ) -> list[Choice]:
        """Autocompletion for clubs."""
        return [
            Choice(name=club.name, value=str(club.id))
            for club in await self.club_service.search_club(current)
        ]

    @app_commands.command(name="infos")
    @app_commands.autocomplete(club=autocomplete_club)
    async def club_infos(
        self, interaction: Interaction, club: Transform[ClubSchema, ClubTransformer]
    ):
        await interaction.response.defer(thinking=True)
        await interaction.followup.send(embed=self.club_service.embed(club))

    @app_commands.command(name="add_member")
    @app_commands.autocomplete(club=autocomplete_club)
    async def add_club_member(
        self,
        interaction: Interaction,
        club: int,
        member: Member,
    ):
        await interaction.response.defer(thinking=True)
        club = next(
            (c for _id, c in self.settings.guild.clubs.items() if _id == club), None
        )
        if not club:
            await interaction.followup.send("Ce club n'a pas été trouvé")
            return
        if not interaction.user.get_role(club.president_role_id):
            await interaction.followup.send(
                "Seul le président du club peut utiliser cette commande"
            )
            return
        await member.add_roles(interaction.guild.get_role(club.member_role_id))
        await interaction.followup.send("Rôle attribué :thumbs_up:")

    @app_commands.command(name="create")
    @app_commands.autocomplete(club=autocomplete_club)
    async def create_club(self, interaction: Interaction, club: int):
        await interaction.response.defer(thinking=True)
        serv = interaction.guild
        clu = await self.club_service.get_club(club)
        if clu is None:
            await interaction.followup.send("Erreur : Club introuvable.")
            return
        club_name = clu.name

        # region create the role for member, presidence and treasurer
        await serv.create_role(
            name=f"Président {club_name}", color=discord.Color.from_str("#FFFFFF")
        )
        await serv.create_role(
            name=f"Trésorier {club_name}", color=discord.Color.from_str("#FFFFFF")
        )
        await serv.create_role(
            name=f"Membre {club_name}", color=discord.Color.from_str("#FFFFFF")
        )
        # endregion

        # region create the clubs category
        """keep in memory roles for the club"""
        president = discord.utils.get(serv.roles, name=f"Président {club_name}")
        membre = discord.utils.get(serv.roles, name=f"Membre {club_name}")
        tresorier = discord.utils.get(serv.roles, name=f"Trésorier {club_name}")

        overwrites = {
            serv.default_role: discord.PermissionOverwrite(read_messages=False),
            president: discord.PermissionOverwrite(
                read_messages=True, manage_channels=True
            ),
            membre: discord.PermissionOverwrite(read_messages=True),
            tresorier: discord.PermissionOverwrite(read_messages=True),
        }

        await serv.create_category(club_name, overwrites=overwrites)
        # enderegion

        # region create default channel
        categorie = discord.utils.get(serv.categories, name=club_name)
        await serv.create_text_channel(f"Général-{club_name}", category=categorie)
        await serv.create_voice_channel(f"Général-{club_name}", category=categorie)

        await interaction.followup.send(club_name)
        # endregion
