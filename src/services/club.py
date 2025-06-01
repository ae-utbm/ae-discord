from __future__ import annotations

from typing import TYPE_CHECKING
from urllib.parse import urljoin

from discord import Embed

from src.settings import Settings

if TYPE_CHECKING:
    from src.client import ClubSchema, SimpleClubSchema, SithClient
    from src.main import AeBot


class ClubService:
    """Manage features directly related to clubs."""

    def __init__(self, client: SithClient, bot: AeBot):
        self._config = Settings()
        self._client = client
        self._club_cache = {}
        self._bot = bot

    async def search_club(self, current: str) -> list[SimpleClubSchema]:
        clubs = await self._client.search_clubs(current)
        if clubs is None:
            return []
        return [club for club in clubs if club.id in self._config.guild.club_ids]

    async def get_club(self, club_id: int) -> ClubSchema | None:
        if club_id not in self._club_cache:
            self._club_cache[club_id] = await self._client.get_club(club_id)
        return self._club_cache[club_id]

    def embed(self, club: ClubSchema) -> Embed:
        """Return an discord embed with infos about this club."""
        embed = Embed(title=club.name, description=club.short_description)
        for role_id, role_name in [(10, "Président(e)"), (7, "Trésorier(e)")]:
            user = next(
                (member.user for member in club.members if member.role == role_id), None
            )
            if user:
                username = f"{user.first_name} {user.last_name}"
                if user.nick_name:
                    username += f" - {user.nick_name}"
                embed.add_field(name=role_name, value=username)
        if club.logo:
            embed = embed.set_thumbnail(
                url=urljoin(str(self._client._base_url), club.logo)
            )
        return embed
