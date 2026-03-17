from __future__ import annotations

import hmac
from typing import TYPE_CHECKING
from urllib.parse import urlencode

import discord.ui
from discord import Member

from src.settings import Settings

if TYPE_CHECKING:
    import re

    from src.main import AeBot


class EmbedChangeButtons(discord.ui.ActionRow):
    def __init__(self, view: EmbedLikeView, auth_url: str) -> None:
        self.__view = view
        super().__init__()
        self.add_item(discord.ui.Button(label="Poursuivre", url=auth_url))

    @discord.ui.button(label="Annuler")
    async def cancel(
        self, interaction: discord.Interaction[AeBot], button: discord.ui.Button
    ) -> None:
        self.__view.stop()
        await interaction.response.edit_message(delete_after=0)


class EmbedLikeView(discord.ui.LayoutView):
    def __init__(self, user: Member) -> None:
        super().__init__()

        disclaimer = discord.ui.TextDisplay(
            "## Authentification par le site AE\n"
            "Vous allez être redirigé vers le site AE "
            "pour lier votre compte AE à ce serveur.\n"
            "Dans ce cadre, les informations suivantes seront récupérées :\n"
            "- votre nom, prénom et surnom\n"
            "- les clubs auxquels vous appartenez\n"
            "Les informations recueillies font l'objet "
            "d'un traitement informatique par l'[AE UTBM](https://ae.utbm.fr) "
            "pour permettre l'organisation (attribution de rôles et pseudo) "
            "d'un serveur Discord.\n\n"
            "Dans le cadre de leur traitement, ces informations "
            "peuvent être transmises à Discord Inc, dont la "
            "[politique de confidentialité](https://discord.com/privacy) "
            "prévaut dès l'envoi du formulaire."
        )
        thumbnail = discord.ui.Thumbnail(
            media="https://ae.utbm.fr/data/club_logos/LogoAE_classique.png"
        )
        data = {
            "client_id": 1,
            "third_party_app": "discord",
            "privacy_link": "https://discord.com/privacy/",
            "username": user.global_name,
            "callback_url": f"http://127.0.0.1:8001/callback/{user.id}/",
        }
        key = Settings().sith_api.hmac_key.get_secret_value()
        signature = hmac.digest(key.encode(), urlencode(data).encode(), "sha512").hex()
        data["signature"] = signature
        section = discord.ui.Section(disclaimer, accessory=thumbnail)
        buttons = EmbedChangeButtons(
            self, f"{Settings().sith_api.url}api-link/auth/?{urlencode(data)}"
        )
        self.add_item(
            discord.ui.Container(
                section, buttons, accent_color=discord.Color.from_str("#3b69c4")
            )
        )


class AuthInteractionButton(
    discord.ui.DynamicItem[discord.ui.Button], template=r"button:channel:(?P<id>\d+)"
):
    def __init__(self, channel_id: int):
        super().__init__(
            discord.ui.Button(
                label="Authentification site AE",
                style=discord.ButtonStyle.blurple,
                custom_id=f"button:channel:{channel_id}",
                emoji="🔐",
            )
        )
        self.channel_id = channel_id

    # This is called when the button is clicked and the custom_id matches the template.
    @classmethod
    async def from_custom_id(
        cls,
        interaction: discord.Interaction,
        item: discord.ui.Button,
        match: re.Match[str],
        /,
    ):
        channel_id = int(match["id"])
        return cls(channel_id)

    async def callback(self, interaction: discord.Interaction) -> None:
        await interaction.response.send_message(
            view=EmbedLikeView(interaction.user), ephemeral=True
        )
