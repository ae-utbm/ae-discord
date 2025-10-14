from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING
from urllib.parse import urljoin

from discord import Colour, Embed

if TYPE_CHECKING:
    from src.client import NewsDateSchema, NewsSchema
    from src.main import AeBot


class NewsService:
    def __init__(self, bot: AeBot):
        self._client = bot.client
        self._bot = bot

    async def get_upcoming_news(self, *, nb_days: int = 3) -> list[NewsDateSchema]:
        """Fetch news of the next following days from the sith."""
        today = datetime.now(tz=UTC)
        three_days_later = (today + timedelta(days=nb_days)).replace(hour=23, minute=59)
        news = await self._client.search_news(after=today, before=three_days_later)
        return news or []

    def embed(self, news: NewsSchema) -> Embed:
        """Return a discord embed with infos about this news date."""
        embed = Embed(
            title=news.title,
            description=news.summary,
            url=urljoin(str(self._client._base_url), news.club.logo),
            colour=Colour.blue(),
        )
        embed.set_author(
            name=news.club.name, url=urljoin(str(self._client._base_url), news.club.url)
        )
        if news.club.logo:
            embed = embed.set_thumbnail(
                url=urljoin(str(self._client._base_url), news.club.logo)
            )
        return embed
