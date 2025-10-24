from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING
from urllib.parse import urljoin

from discord import CategoryChannel, Embed, PermissionOverwrite, utils

from src.db.models import Club
from src.settings import Settings

if TYPE_CHECKING:
    from discord import Guild, Member, Message

    from src.client import ClubSchema, SimpleClubSchema
    from src.main import AeBot


class ClubError(Exception):
    """Errors related to operations on clubs"""


class ClubExists(ClubError):
    """Trying to create a club that already exists"""


class ClubDoesNotExist(ClubError):
    """Trying to use a club that does not exist"""


class ClubService:
    """Manage features directly related to clubs."""

    def __init__(self, bot: AeBot):
        self._config = Settings()
        self._client = bot.client
        self._club_cache = {}
        self._bot = bot
        self._background_tasks = set()

    async def search_club(
        self, current: str, *, only_existing: bool
    ) -> list[SimpleClubSchema]:
        clubs = await self._client.search_clubs(current)
        if clubs and only_existing:
            clubs_ids = [c[0] for c in Club.select(Club.sith_id).tuples()]
            clubs = [c for c in clubs if c.id in clubs_ids]
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

    async def create_club(self, club: ClubSchema, guild: Guild, mess: Message):
        if Club.filter(Club.sith_id == club.id).exists():
            raise ClubExists
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
            president: PermissionOverwrite(
                read_messages=True, manage_channels=True, manage_permissions=True
            ),
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
        await self.move_to_bottom(category)
        await category.create_text_channel(
            f"Annonces-{club.name}", overwrites=news_overwrite, news=True, position=0
        )
        await category.create_text_channel(f"Général-{club.name}")
        await category.create_voice_channel(f"Général-{club.name}")
        await self.move_to_bottom(category)
        Club.create(
            name=club.name,
            category_id=category.id,
            sith_id=club.id,
            president_role_id=president.id,
            treasurer_role_id=treasurer.id,
            member_role_id=member.id,
            former_member_role_id=former_member.id,
            message_autorole_id=mess.id,
        )

    async def add_member(self, club: Club, member: Member):
        role = utils.get(member.guild.roles, id=club.member_role_id)
        former = utils.get(member.guild.roles, id=club.former_member_role_id)
        if former in member.roles:
            await member.remove_roles(
                former, reason=f"{member.name} joined club {club.name}"
            )
        await member.add_roles(role, reason=f"{member.name} joined club {club.name}")

    async def remove_member(
        self, club: Club, member: Member, *, make_former: bool = True
    ):
        """Remove a member from the club.

        Args:
            club: The club to remove the user from
            member: The member to remove
            make_former:
                if True, the member will receive
                a role indicating its former club membership
        """
        await self.remove_members(club, [member], make_former=make_former)

    async def remove_members(
        self,
        club: Club,
        members: list[Member] | tuple[Member] | set[Member],
        *,
        make_former: bool = True,
    ):
        """Remove multiple members from a club.

        Args:
            club: The club to remove the user from
            members: The members to remove
            make_former:
                if True, the member will receive
                a role indicating its former club membership

        Warnings:
            This method sleeps for two seconds between each member
            (in order to avoid rate-limit), so it may be a bad idea
            to await it.
            Favour an execution inside a detached async Task.
        """
        role_ids = [club.member_role_id, club.president_role_id, club.treasurer_role_id]
        roles = [self._bot.watched_guild.get_role(r) for r in role_ids]
        former = self._bot.watched_guild.get_role(club.former_member_role_id)
        for member in members:
            if len(members) > 1:
                # if there is more than one member,
                # sleep a little bit to avoid rate limit
                await asyncio.sleep(2)
            await member.remove_roles(
                *roles, reason=f"{member.name} left club {club.name}"
            )
            if make_former:
                await member.add_roles(
                    former, reason=f"{member.name} left club {club.name}"
                )

    async def handover(
        self, club: ClubSchema, new_pres: Member, new_treso: Member, guild: Guild
    ):
        club = Club.get_or_none(Club.sith_id == club.id)

        # removing former president and treasurer
        role_pres = utils.get(guild.roles, id=club.president_role_id)
        role_treso = utils.get(guild.roles, id=club.treasurer_role_id)
        former = utils.get(guild.roles, id=club.former_member_role_id)
        old_board = {*role_pres.members, *role_treso.members}
        for member in old_board:
            await member.remove_roles(
                role_pres, role_treso, reason=f"Passation du club : {club.name}"
            )
            await member.add_roles(former, reason=f"Passation du club : {club.name}")

        # add new president and treasurer
        for new_member in [new_pres, new_treso]:
            if former in new_member.roles:
                await new_member.remove_roles(
                    former, reason=f"{new_pres.name} joined club {club.name}"
                )
        await new_pres.add_roles(role_pres, reason=f"Passation du club : {club.name}")
        await new_treso.add_roles(role_treso, reason=f"Passation du club : {club.name}")
        category = utils.get(guild.categories, id=club.category_id)
        if category.name.endswith("[inactif]"):
            await category.edit(name=club.name)
            await self.move_to_bottom(category)

    async def stop_club(self, club: Club, guild: Guild):
        role_pres = utils.get(guild.roles, id=club.president_role_id)
        role_treso = utils.get(guild.roles, id=club.treasurer_role_id)
        role_member = utils.get(guild.roles, id=club.member_role_id)
        old_members = {*role_pres.members, *role_treso.members, *role_member.members}
        category = utils.get(guild.categories, id=club.category_id)
        await self.move_to_bottom(category)
        await category.edit(name=club.name + " [inactif]")
        # see https://docs.python.org/3/library/asyncio-task.html#creating-tasks
        task = asyncio.create_task(
            self.remove_members(club, old_members, make_former=True)
        )
        self._background_tasks.add(task)
        task.add_done_callback(self._background_tasks.discard)

    @staticmethod
    async def move_to_bottom(category: CategoryChannel):
        """Move this category after the last category belong to an active club.

        Warnings:
            This method seems to have a high cost on discord's side.
            Using it a little bit too much is likely to end in rate-limit.
        """
        guild = category.guild
        inactives = [c for c in guild.categories if c.name.endswith("[inactif]")]
        if not inactives:
            await category.move(end=True)
            return
        other = min(inactives, key=lambda c: c.position)
        if (category.position - other.position) <= 1:
            # the category is already at the bottom of the list, there is nothing to do
            return
        await category.move(before=other)
