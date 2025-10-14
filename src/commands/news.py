from __future__ import annotations

import datetime
from typing import TYPE_CHECKING

import pytz
from discord.ext import commands, tasks

from src.services.news import NewsService

if TYPE_CHECKING:
    from discord import Role, TextChannel

    from src.main import AeBot


class NewsCog(commands.Cog):
    news_channel: TextChannel
    news_role: Role

    def __init__(self, bot: AeBot):
        self.bot = bot
        self.news_service = NewsService(bot)

    @commands.Cog.listener(name="on_ready")
    async def on_ready(self):
        news_channel_id = self.bot.settings.guild.news_channel_id
        news_role_id = self.bot.settings.guild.news_role_id
        if not news_channel_id:
            # If no news channel id is given in the config,
            # the feature of automatic news post is disabled.
            return
        self.news_channel = self.bot.get_channel(news_channel_id)
        self.news_role = self.bot.watched_guild.get_role(news_role_id)
        await self.bot.wait_until_ready()
        self.post_news.start()

    @tasks.loop(
        time=datetime.time(hour=9, minute=30, tzinfo=pytz.timezone("Europe/Paris"))
    )
    async def post_news(self):
        news_dates = await self.news_service.get_upcoming_news()
        if not news_dates:
            return
        embeds = [self.news_service.embed(n.news) for n in news_dates]
        content = "## Événements dans les prochains jours"
        if self.news_role:
            content += f"\n{self.news_role.mention}"
        await self.news_channel.send(content, embeds=embeds)
