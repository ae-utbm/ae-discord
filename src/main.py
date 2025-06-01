import asyncio
import logging

from discord import Guild, Intents
from discord.ext import commands
from discord.utils import setup_logging

from src.client import SithClient
from src.commands.admin import AdminCog
from src.commands.club import ClubCog
from src.commands.misc import MiscCog
from src.settings import Settings


class AeBot(commands.Bot):
    watched_guild: Guild

    def __init__(self, client: SithClient):
        self.settings = Settings()
        self.logger = logging.getLogger("discord")
        self.client = client
        super().__init__(command_prefix="?", intents=Intents.all())

    async def setup_hook(self):
        await self.add_cog(ClubCog(self.client, self))
        await self.add_cog(AdminCog(self))
        await self.add_cog(MiscCog())

    async def on_ready(self):
        await self.wait_until_ready()
        self.watched_guild = self.get_guild(self.settings.guild.id)
        self.logger.info(f"Bot ready to act on {self.watched_guild.name}")


async def main():
    async with SithClient() as client:
        bot = AeBot(client)
        setup_logging()
        await bot.start(bot.settings.bot.token.get_secret_value())


if __name__ == "__main__":
    asyncio.run(main())
