from __future__ import annotations

from typing import TYPE_CHECKING

from discord.ext import commands

from src.client import ClubSchema  # noqa TC001
from src.db.models import Club
from src.services.club import ClubService
from src.settings import Settings

if TYPE_CHECKING:
    from discord import RawReactionActionEvent

    from src.main import AeBot


class RoleCog(commands.GroupCog, group_name="role"):
    def __init__(self, bot: AeBot):
        self.settings = Settings()
        self.club_service = ClubService(bot)
        self.bot = bot

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: RawReactionActionEvent):
        member = self.bot.watched_guild.get_member(payload.user_id)
        if payload.guild_id is None or member == self.bot.user:
            return

        db_club = Club.get_or_none(Club.message_autorole_id == payload.message_id)
        if not db_club:
            return

        channel = self.bot.get_channel(payload.channel_id)
        message = await channel.fetch_message(payload.message_id)
        if str(payload.emoji) != "✅":
            await message.remove_reaction(payload.emoji, member)

        await self.club_service.add_member(db_club, member)

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload: RawReactionActionEvent):
        member = self.bot.watched_guild.get_member(payload.user_id)
        if payload.guild_id is None or member == self.bot.user:
            return

        db_club = Club.get_or_none(Club.message_autorole_id == payload.message_id)
        if not db_club or str(payload.emoji) != "✅":
            return

        await self.club_service.remove_member(db_club, member, make_former=False)
