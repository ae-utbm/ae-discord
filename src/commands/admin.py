from __future__ import annotations

from typing import TYPE_CHECKING

from discord.ext import commands

if TYPE_CHECKING:
    from discord.app_commands import AppCommand
    from discord.ext.commands import Context

    from src.main import AeBot


class AdminCog(commands.Cog):
    def __init__(self, bot: AeBot):
        self._bot = bot

    @commands.command(name="sync")
    async def sync_commands(self, ctx: Context):
        """Actualise les commandes du bot."""
        synced: list[AppCommand] = await self._bot.tree.sync()
        await self._bot.tree.sync(guild=ctx.guild)
        cmd_list = "\n".join([f"- {cmd.name}" for cmd in synced])
        msg = f"Commandes synchronisées :\n{cmd_list}"
        await ctx.reply(msg)
