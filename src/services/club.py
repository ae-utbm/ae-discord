from __future__ import annotations

import json
import os
from typing import TYPE_CHECKING
from urllib.parse import urljoin

import discord
from discord import Embed

from src.settings import BASE_DIR, Settings

if TYPE_CHECKING:
    from src.client import ClubSchema, SimpleClubSchema, SithClient
    from src.main import AeBot

PATH = os.path.dirname(__file__)


class ClubDiscord:
    def __init__(
        self,
        id_,
        Name,
        id_role_pres,
        id_role_treso,
        id_role_membre,
    ):
        self.id = id_
        self.name = Name
        self.id_role_pres = id_role_pres
        self.id_pres = None
        self.id_role_treso = id_role_treso
        self.id_treso = None
        self.id_role_membre = id_role_membre
        self.id_membre = []

    def dico(self):
        return {
            "id": self.id,
            "name": self.name,
            "id_role_pres": self.id_role_pres,
            "id_pres": self.id_pres,
            "id_role_treso": self.id_role_treso,
            "id_treso": self.id_treso,
            "id_role_membre": self.id_role_membre,
            "id_membre": self.id_membre,
        }


class ClubDiscord:
    def __init__(
        self,
        id_,
        Name,
        id_role_pres,
        id_role_treso,
        id_role_membre,
    ):
        self.id = id_
        self.name = Name
        self.id_role_pres = id_role_pres
        self.id_pres = None
        self.id_role_treso = id_role_treso
        self.id_treso = None
        self.id_role_membre = id_role_membre
        self.id_membre = []

    def dico(self):
        return {
            "id": self.id,
            "name": self.name,
            "id_role_pres": self.id_role_pres,
            "id_pres": self.id_pres,
            "id_role_treso": self.id_role_treso,
            "id_treso": self.id_treso,
            "id_role_membre": self.id_role_membre,
            "id_membre": self.id_membre,
        }


class ClubService:
    """Manage features directly related to clubs."""

    def __init__(self, client: SithClient, bot: AeBot):
        with open(BASE_DIR / "data/club.json") as f:
            data = json.load(f)
        self._config = Settings()
        self._client = client
        self._club_cache = {}
        self._bot = bot
        self.club_discord = data

    async def search_club(self, current: str) -> list[SimpleClubSchema]:
        clubs = await self._client.search_clubs(current)
        return clubs if clubs is not None else []

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
        # create the role for member, presidence and treasurer
        president = await serv.create_role(name=f"Président {club_name}")
        tresorier = await serv.create_role(name=f"Trésorier {club_name}")
        membre = await serv.create_role(name=f"Membre {club_name}", mentionable=True)

        # create the clubs category
        overwrites = {
            serv.default_role: discord.PermissionOverwrite(read_messages=False),
            president: discord.PermissionOverwrite(
                read_messages=True, manage_channels=True
            ),
            membre: discord.PermissionOverwrite(read_messages=True),
            tresorier: discord.PermissionOverwrite(read_messages=True),
        }

        categorie = await serv.create_category(club_name, overwrites=overwrites)

        # create default channel
        await serv.create_text_channel(f"Général-{club_name}", category=categorie)
        await serv.create_voice_channel(f"Général-{club_name}", category=categorie)
        # store the new club into the JSON file
        new_club = ClubDiscord(
            self.club_discord["id_max"],
            club_name,
            president.id,
            tresorier.id,
            membre.id,
        )
        self.club_discord[club_name] = new_club.dico()
        self.club_discord["id_max"] += 1

        with open(PATH + "/club.json", "w") as f:
            json.dump(self.club_discord, f)

    async def add_member(self, club: dict, role, member):
        self.club_discord[club["name"]]["id_membre"].append(member.id)
        await member.add_roles(role)
        with open(PATH + "/club.json", "w") as f:
            json.dump(self.club_discord, f)
