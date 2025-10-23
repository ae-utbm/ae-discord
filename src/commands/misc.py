from __future__ import annotations

from typing import TYPE_CHECKING

from discord import Interaction, app_commands
from discord.ext import commands

if TYPE_CHECKING:
    from src.main import AeBot


class MiscCog(commands.Cog):
    @app_commands.command(name="ping", description="Ping le bot")
    async def ping(self, interaction: Interaction[AeBot]):
        await interaction.response.send_message("pong", ephemeral=True)
