from __future__ import annotations
from typing import TYPE_CHECKING

from discord import app_commands, Interaction
from discord.ext import commands

if TYPE_CHECKING:
    from src.main import AeBot


class MiscCog(commands.Cog):
    @app_commands.command(name="ping")
    async def sync_commands(self, interaction: Interaction[AeBot]):
        await interaction.response.send_message("pong")
