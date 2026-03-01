from __future__ import annotations

from typing import TYPE_CHECKING

import discord.ui
from discord import Interaction, app_commands
from discord.ext.commands import GroupCog

from src.ui.auth import AuthInteractionButton

if TYPE_CHECKING:
    from src.main import AeBot


@app_commands.guild_only
@app_commands.default_permissions(administrator=True)
class AuthCog(GroupCog, name="auth"):
    def __init__(self, bot: AeBot):
        self.bot = bot

    @app_commands.command(
        name="message",
        description=(
            "Envoie dans ce salon un message avec lequel "
            "les utilisateurs pourront interagir pour s'authentifier"
        ),
    )
    async def post_auth_message(self, interaction: Interaction[AeBot]):
        channel = interaction.channel
        view = discord.ui.View(timeout=None)
        view.add_item(AuthInteractionButton(channel.id))
        await channel.send(view=view)
        await interaction.response.send_message("Message envoyé", ephemeral=True)
