from __future__ import annotations

from typing import TYPE_CHECKING

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
            Choice(name=club.name, value=club.id)
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
