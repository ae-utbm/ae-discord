from __future__ import annotations

from typing import TYPE_CHECKING

from discord import Interaction, app_commands
from discord.app_commands import Choice
from discord.ext import commands

from src.services.club import ClubService
from src.settings import Settings

if TYPE_CHECKING:
    from src.client import ClubSchema, SithClient
    from src.main import AeBot


class ClubCog(commands.GroupCog, group_name="club"):
    def __init__(self, client: SithClient, bot: "AeBot"):
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
    async def club_infos(self, interaction: Interaction, club: int):
        await interaction.response.defer(thinking=True)
        club: ClubSchema = await self.club_service.get_club(club)
        if club is None:
            await interaction.followup.send("Ce club n'a pas été trouvé.")
            return
        await interaction.followup.send(embed=self.club_service.embed(club))
