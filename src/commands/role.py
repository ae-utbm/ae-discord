from __future__ import annotations

from typing import TYPE_CHECKING

from discord.ext import commands

from src.client import ClubSchema  # noqa TC001
from src.db.models import Club
from src.services.club import ClubService
from src.settings import Settings

if TYPE_CHECKING:
    from src.main import AeBot


class RoleCog(commands.GroupCog, group_name="role"):
    def __init__(self, bot: AeBot):
        self.settings = Settings()
        self.club_service = ClubService(bot)
        self.bot = bot

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        if payload.guild_id is None:
            return

        guild = self.bot.get_guild(payload.guild_id)
        member = guild.get_member(payload.user_id)
        channel = self.bot.get_channel(payload.channel_id)
        message = await channel.fetch_message(payload.message_id)
        emoji = str(payload.emoji)
        db_club = Club.get(Club.message_autorole_id == message.id)

        if not db_club:
            return

        elif emoji != "✅":
            await message.remove_reaction(payload.emoji, member)

        await self.club_service.add_member(db_club, member)

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        if payload.guild_id is None:
            return

        guild = self.bot.get_guild(payload.guild_id)
        member = guild.get_member(payload.user_id)
        channel = self.bot.get_channel(payload.channel_id)
        message = await channel.fetch_message(payload.message_id)
        emoji = str(payload.emoji)

        db_club = Club.get_or_none(Club.message_autorole_id, message.id)

        if not db_club or emoji != "✅":
            await member.send("nonon")
            return

        await self.club_service.remove_member(db_club, member, _former=0)
