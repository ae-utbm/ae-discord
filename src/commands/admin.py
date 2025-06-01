from __future__ import annotations
from typing import TYPE_CHECKING

from discord.app_commands import AppCommand
from discord.ext import commands
from discord.ext.commands import Context

if TYPE_CHECKING:
    from src.main import AeBot


class AdminCog(commands.Cog):
    def __init__(self, bot: AeBot):
        self._bot = bot

    @commands.command(name="sync")
    async def sync_commands(self, ctx: Context):
        """Actualise les commandes du bot."""
        synced: list[AppCommand] = await self._bot.tree.sync()
        msg = "\n".join([f"- {cmd.name}" for cmd in synced])
        await ctx.reply(msg)
