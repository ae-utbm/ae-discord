from discord import Member, Role

from src.client import SithClient, UserSchema
from src.db.models import Club, User
from src.main import AeBot


class MemberNotFound(Exception): ...


class AuthService:
    def __init__(self, bot: AeBot, client: SithClient):
        self.bot = bot
        self.client = client

    async def get_member_roles(
        self, member: Member, sith_user: UserSchema
    ) -> set[Role]:
        memberships = await self.client.get_user_clubs(sith_user.id)
        if not memberships:
            return set()
        club_ids = {m.club.id for m in memberships}
        qs = Club.select(
            Club.member_role_id, Club.treasurer_role_id, Club.president_role_id
        ).where(Club.sith_id.not_in(club_ids))
        roles_to_remove = {
            self.bot.watched_guild.get_role(i) for ids in qs.tuples() for i in ids
        }

        roles_to_add = set()
        db_new_clubs: dict[int, Club] = {
            club.sith_id: club
            for club in Club.select().where(Club.sith_id.in_(club_ids))
        }
        for membership in memberships:
            roles_to_add.add(db_new_clubs[membership.club.id].member_role_id)
            if membership.role == 7:
                roles_to_add.add(db_new_clubs[membership.club.id].treasurer_role_id)
            if membership.role == 10:
                roles_to_add.add(db_new_clubs[membership.club.id].president_role_id)
        roles_to_add = {self.bot.watched_guild.get_role(i) for i in roles_to_add}

        return set(member.roles).difference(roles_to_remove).union(roles_to_add)

    async def sync_user(self, user_id: int, data: UserSchema):
        member = self.bot.watched_guild.get_member(user_id)
        if not member:
            raise MemberNotFound
        User.get_or_create(
            discord_id=user_id,
            defaults={"sith_id": data.id, "username": member.name},
        )
        await member.edit(roles=await self.get_member_roles(member, data))
        await member.send(
            "Vos rôles sur le serveur ont été synchronisés avec le site AE."
        )
