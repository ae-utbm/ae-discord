from __future__ import annotations

from typing import TYPE_CHECKING

from discord import Interaction, Member, app_commands, utils
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
        clubs = await self.club_service.search_club(current)
        clubs = clubs[:25]  # discord autocomplete can have at most 25 items
        return [Choice(name=club.name, value=str(club.id)) for club in clubs]

    @app_commands.command(name="infos")
    @app_commands.autocomplete(club=autocomplete_club)
    async def club_infos(
        self, interaction: Interaction, club: Transform[ClubSchema, ClubTransformer]
    ):
        await interaction.response.defer(thinking=True)
        await interaction.followup.send(embed=self.club_service.embed(club))

    @app_commands.command(name="remove_member")
    @app_commands.autocomplete(club=autocomplete_club)
    async def remove_club_member(
        self,
        interaction: Interaction,
        club: Transform[ClubSchema, ClubTransformer],
        member: Member,
    ):
        await interaction.response.defer(thinking=True)
        # look if the club exist in the JSON file
        if club.name in self.club_service.club_discord:
            club_ = self.club_service.club_discord[club.name]
            is_pres = interaction.user.get_role(club_["id_role_pres"])
            if is_pres is not None:  # look if the user is the president of the club
                role = utils.get(member.guild.roles, id=club_["id_role_membre"])
                if role in member.roles:
                    await self.club_service.remove_member(club_, role, member)
                    await interaction.followup.send("Rôle supprimée :thumbs_up:")

                else:
                    await interaction.followup.send(
                        "Cet utilisateur n'est pas dans le club"
                    )

            else:
                await interaction.followup.send(
                    "Seul le président du club peut ajouter un membre"
                )
        else:
            await interaction.followup.send(f"Le club : {club.name} n'existe pas")

    @app_commands.command(name="add_member")
    @app_commands.autocomplete(club=autocomplete_club)
    async def add_club_member(
        self,
        interaction: Interaction,
        club: Transform[ClubSchema, ClubTransformer],
        member: Member,
    ):
        await interaction.response.defer(thinking=True)
        # look if the club exist in the JSON file
        if club.name in self.club_service.club_discord:
            club_ = self.club_service.club_discord[club.name]
            is_pres = interaction.user.get_role(club_["id_role_pres"])
            if is_pres is not None:  # look if the user is the president of the club
                role = utils.get(member.guild.roles, id=club_["id_role_membre"])
                await self.club_service.add_member(club_, role, member)
                await interaction.followup.send("Rôle attribué :thumbs_up:")

            else:
                await interaction.followup.send(
                    "Seul le président du club peut ajouter un membre"
                )
        else:
            await interaction.followup.send(f"Le club : {club.name} n'existe pas")

    @app_commands.command(name="create")
    @app_commands.autocomplete(club=autocomplete_club)
    async def create_club(
        self, interaction: Interaction, club: Transform[ClubSchema, ClubTransformer]
    ):
        await interaction.response.defer(thinking=True)
        serv = interaction.guild

        # look if the club is already create
        if club.name not in self.club_service.club_discord:
            await self.club_service.create_club(club.name, serv)
            await interaction.followup.send(f"Le club : {club.name} à été créé")

        else:
            await interaction.followup.send(f"Le club : {club.name} existe déjà...")
