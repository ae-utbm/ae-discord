from __future__ import annotations

import json
from typing import TYPE_CHECKING, Self
from urllib.parse import urljoin

from discord import Embed, PermissionOverwrite, utils
from pydantic import BaseModel

from src.settings import BASE_DIR, Settings

if TYPE_CHECKING:
    from discord import Guild, Member

    from src.client import ClubSchema, SimpleClubSchema, SithClient
    from src.main import AeBot


class DiscordClub(BaseModel):
    """Pydantic model representing data about a club on the discord guild.

    It can also manage interaction with the internal data cache.
    """

    name: str
    sith_id: int
    category_id: int
    president_role_id: int
    president_sith_id: int | None = None
    treasurer_role_id: int
    treasurer_sith_id: int | None = None
    member_role_id: int
    member_sith_id: int | None = None
    former_member_role_id: int

    @classmethod
    def load_all(cls) -> dict[str, dict]:
        return json.loads((BASE_DIR / "data/club.json").read_text())

    @classmethod
    def load(cls, club_id: int) -> Self | None:
        club = cls.load_all().get(str(club_id))
        return cls.model_validate(club) if club is not None else club

    def save(self):
        all_clubs = self.load_all()
        all_clubs[str(self.sith_id)] = self.model_dump()
        (BASE_DIR / "data/club.json").write_text(json.dumps(all_clubs))


class ClubService:
    """Manage features directly related to clubs."""

    def __init__(self, client: SithClient, bot: AeBot):
        self._config = Settings()
        self._client = client
        self._club_cache = {}
        self._bot = bot

    async def search_club(
        self, current: str, *, only_existing: bool
    ) -> list[SimpleClubSchema]:
        clubs = await self._client.search_clubs(current)
        if clubs and only_existing:
            clubs = [c for c in clubs if str(c.id) in DiscordClub.load_all()]
        return clubs if clubs is not None else []

    async def get_club(self, club_id: int) -> ClubSchema | None:
        if club_id not in self._club_cache:
            self._club_cache[club_id] = await self._client.get_club(club_id)
        return self._club_cache[club_id]

    async def get_channel(self, guild: Guild, category_id: int, name: str):
        category = utils.get(guild.categories, id=category_id)
        channels_in_category = category.channels
        for channel in channels_in_category:
            channel_name = channel.name.lower().replace("-", " ")
            name = name.lower().replace("'", "")
            if channel_name == name:
                return channel

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

    async def create_club(self, club: ClubSchema, guild: Guild):
        # create the role for member, presidence and treasurer
        president = await guild.create_role(name=f"Responsable {club.name}")
        treasurer = await guild.create_role(name=f"Trésorier {club.name}")
        member = await guild.create_role(name=f"Membre {club.name}", mentionable=True)
        former_member = await guild.create_role(
            name=f"Ancien membre {club.name}", mentionable=True
        )

        # create the clubs category
        overwrites = {
            guild.default_role: PermissionOverwrite(read_messages=False),
            president: PermissionOverwrite(read_messages=True, manage_channels=True),
            member: PermissionOverwrite(read_messages=True),
            treasurer: PermissionOverwrite(read_messages=True),
            former_member: PermissionOverwrite(read_messages=True),
        }
        news_overwrite = {
            former_member: PermissionOverwrite(send_messages=False),
            member: PermissionOverwrite(send_messages=False),
            treasurer: PermissionOverwrite(send_messages=False),
            president: PermissionOverwrite(send_messages=True),
        }

        category = await guild.create_category(club.name, overwrites=overwrites)
        await category.create_text_channel(
            f"Annonces-{club.name}", overwrites=news_overwrite, news=True, position=0
        )
        await category.create_text_channel(f"Général-{club.name}")
        await category.create_voice_channel(f"Général-{club.name}")
        new_club = DiscordClub(
            sith_id=club.id,
            name=club.name,
            president_role_id=president.id,
            treasurer_role_id=treasurer.id,
            member_role_id=member.id,
            former_member_role_id=former_member.id,
            category_id=category.id,
        )
        new_club.save()

    async def add_member(self, club: DiscordClub, member: Member):
        role = utils.get(member.guild.roles, id=club.member_role_id)
        former = utils.get(member.guild.roles, id=club.former_member_role_id)
        if former in member.roles:
            await member.remove_roles(
                former, reason=f"{member.name} joined club {club.name}"
            )
        await member.add_roles(role, reason=f"{member.name} joined club {club.name}")
        club.save()

    async def remove_member(self, club: DiscordClub, member: Member):
        role = utils.get(member.guild.roles, id=club.member_role_id)
        former = utils.get(member.guild.roles, id=club.former_member_role_id)
        await member.remove_roles(role, reason=f"{member.name} leaved club {club.name}")
        await member.add_roles(former, reason=f"{member.name} leaved club {club.name}")
        club.save()

    async def handover(
        self, club: ClubSchema, new_pres: Member, new_treso: Member, guild: Guild
    ):
        club = DiscordClub.load(club.id)

        # removing former presidence and treasurer
        role_pres = utils.get(guild.roles, id=club.president_role_id)
        role_treso = utils.get(guild.roles, id=club.treasurer_role_id)
        former = utils.get(guild.roles, id=club.former_member_role_id)
        old_board = {*role_pres.members, *role_treso.members}
        for member in old_board:
            await member.remove_roles(
                role_pres, role_treso, reason=f"Passation du club : {club.name}"
            )
            await member.add_roles(former, reason=f"Passation du club : {club.name}")

        # add new presidence and treasurer
        for new_member in [new_pres, new_treso]:
            if former in new_member.roles:
                await new_member.remove_roles(
                    former, reason=f"{new_pres.name} joined club {club.name}"
                )
        await new_pres.add_roles(role_pres, reason=f"Passation du club : {club.name}")
        await new_treso.add_roles(role_treso, reason=f"Passation du club : {club.name}")
