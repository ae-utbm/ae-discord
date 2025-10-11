from __future__ import annotations

import asyncio
import logging
from datetime import datetime
from logging import handlers
from typing import TYPE_CHECKING

from discord import Guild, Intents, Interaction
from discord.ext import commands
from discord.utils import setup_logging

from src.client import SithClient
from src.commands.admin import AdminCog
from src.commands.club import ClubCog
from src.commands.misc import MiscCog
from src.settings import BASE_DIR, Settings

if TYPE_CHECKING:
    from discord.app_commands import Command
    from discord.ext.commands import Context


class AeBot(commands.Bot):
    watched_guild: Guild

    def __init__(self, client: SithClient):
        self.settings = Settings()
        self.logger = logging.getLogger("discord")
        self.client = client
        super().__init__(
            command_prefix=self.settings.bot.command_prefix, intents=Intents.all()
        )

    async def setup_hook(self):
        await self.add_cog(ClubCog(self.client, self))
        await self.add_cog(AdminCog(self))
        await self.add_cog(MiscCog())

    async def on_ready(self):
        await self.wait_until_ready()
        self.watched_guild = self.get_guild(self.settings.guild.id)
        self.logger.info(f"Bot ready to act on {self.watched_guild.name}")

    async def on_command(self, ctx: Context):
        start = ctx.message.created_at
        duration = datetime.now(tz=start.tzinfo) - start
        self.logger.info(
            f"Command `{ctx.command.name}` called by {ctx.author.name} "
            f"[{duration.total_seconds():.6f}sec]"
        )

    async def on_app_command_completion(
        self, interaction: Interaction, command: Command
    ):
        start = interaction.created_at
        duration = datetime.now(tz=start.tzinfo) - start
        cmd_name = (
            f"{command.parent.name} {command.name}" if command.parent else command.name
        )
        self.logger.info(
            f"Slash command `{cmd_name}` "
            f"called by {interaction.user.name} in {interaction.channel.name} "
            f"[{duration.total_seconds():.6f}sec]"
        )


async def main():
    async with SithClient() as client:
        bot = AeBot(client)
        # Setup the logging (stream handler and file handler)
        setup_logging()
        (BASE_DIR / "data").mkdir(exist_ok=True)
        (BASE_DIR / "log").mkdir(exist_ok=True)
        handler = handlers.RotatingFileHandler(
            filename=BASE_DIR / "log/bot.log",
            maxBytes=10485760,  # 10Mo
            backupCount=5,
        )
        formatter = logging.Formatter(
            "[{asctime}] [{levelname:<8}] {name}: {message}",
            "%Y-%m-%d %H:%M:%S",
            style="{",
        )
        setup_logging(handler=handler, formatter=formatter)

        await bot.start(bot.settings.bot.token.get_secret_value())


if __name__ == "__main__":
    asyncio.run(main())
