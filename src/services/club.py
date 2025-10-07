from __future__ import annotations

from typing import TYPE_CHECKING
from urllib.parse import urljoin

import discord
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
        return [club for club in clubs if club.id in self._config.guild.clubs]

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

    async def create_club(self, club_name: str, serv):
        # region create the role for member, presidence and treasurer
        president = await serv.create_role(
            name=f"Président {club_name}", color=discord.Color.from_str("#FFFFFF")
        )
        tresorier = await serv.create_role(
            name=f"Trésorier {club_name}", color=discord.Color.from_str("#FFFFFF")
        )
        membre = await serv.create_role(
            name=f"Membre {club_name}",
            color=discord.Color.from_str("#FFFFFF"),
            mentionable=True,
        )
        # endregion

        # region create the clubs category
        overwrites = {
            serv.default_role: discord.PermissionOverwrite(read_messages=False),
            president: discord.PermissionOverwrite(
                read_messages=True, manage_channels=True
            ),
            membre: discord.PermissionOverwrite(read_messages=True),
            tresorier: discord.PermissionOverwrite(read_messages=True),
        }

        categorie = await serv.create_category(club_name, overwrites=overwrites)
        # enderegion

        # region create default channel
        await serv.create_text_channel(f"Général-{club_name}", category=categorie)
        await serv.create_voice_channel(f"Général-{club_name}", category=categorie)
        # endregion
