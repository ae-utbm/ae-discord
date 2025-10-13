from __future__ import annotations

from typing import TYPE_CHECKING

from discord import Interaction, Member, app_commands
from discord.app_commands import Choice, Transform, Transformer
from discord.ext import commands
from discord.ext.commands import BadArgument

from src.client import ClubSchema  # noqa TC001
from src.services.club import ClubService, DiscordClub
from src.settings import Settings

if TYPE_CHECKING:
    from src.client import SithClient
    from src.main import AeBot


class ClubTransformer(Transformer):
    async def transform(
        self, interaction: Interaction[AeBot], value: int
    ) -> ClubSchema:
        club = await interaction.client.client.get_club(value)
        if not club:
            raise BadArgument("Ce club n'existe pas")
        return club


class ClubCog(commands.GroupCog, group_name="club"):
    def __init__(self, client: SithClient, bot: AeBot):
        self.club_service = ClubService(client, bot)
        self.settings = Settings()

    async def autocomplete_club(
        self, _interaction: Interaction, current: str
    ) -> list[Choice]:
        """Autocompletion for clubs."""
        clubs = await self.club_service.search_club(current, only_existing=False)
        clubs = clubs[:25]  # discord autocomplete can have at most 25 items
        return [Choice(name=club.name, value=str(club.id)) for club in clubs]

    async def autocomplete_existing_club(
        self, _interaction: Interaction, current: str
    ) -> list[Choice]:
        """Autocompletion for clubs that have a channel in the guild"""
        clubs = await self.club_service.search_club(current, only_existing=True)
        clubs = clubs[:25]  # discord autocomplete can have at most 25 items
        return [Choice(name=club.name, value=str(club.id)) for club in clubs]

    @app_commands.command(name="infos")
    @app_commands.autocomplete(club=autocomplete_club)
    async def club_infos(
        self, interaction: Interaction, club: Transform[ClubSchema, ClubTransformer]
    ):
        await interaction.response.defer(thinking=True)
        await interaction.followup.send(embed=self.club_service.embed(club))

    @app_commands.command(name="remove_member")
    @app_commands.autocomplete(club=autocomplete_existing_club)
    async def remove_club_member(
        self,
        interaction: Interaction,
        club: Transform[ClubSchema, ClubTransformer],
        member: Member,
    ):
        await interaction.response.defer(thinking=True)
        discord_club = DiscordClub.load(club.id)
        if not discord_club:
            await interaction.followup.send(f"Le club : {club.name} n'existe pas")
            return
        if (
            not interaction.user.guild_permissions.manage_roles
            and not interaction.user.get_role(discord_club.president_role_id)
        ):
            await interaction.followup.send(
                "Seul le président du club et les admins peuvent retirer un membre"
            )
            return
        if member.id not in discord_club.members:
            await interaction.followup.send("Cet utilisateur n'est pas dans le club")
            return
        await self.club_service.remove_member(discord_club, member)
        await interaction.followup.send(
            f"{member.name} a été retiré du club :thumbs_up:"
        )

    @app_commands.command(name="add_member")
    @app_commands.autocomplete(club=autocomplete_existing_club)
    async def add_club_member(
        self,
        interaction: Interaction,
        club: Transform[ClubSchema, ClubTransformer],
        member: Member,
    ):
        await interaction.response.defer(thinking=True)
        discord_club = DiscordClub.load(club.id)
        if not discord_club:
            await interaction.followup.send(f"Le club : {club.name} n'existe pas")
            return
        if (
            not interaction.user.guild_permissions.manage_roles
            and not interaction.user.get_role(discord_club.president_role_id)
        ):
            await interaction.followup.send(
                "Seul le président du club et les admins peuvent ajouter un membre"
            )
            return
        if member.id in discord_club.members:
            await interaction.followup.send("Cet utilisateur est déjà dans le club")
            return
        await self.club_service.add_member(discord_club, member)
        await interaction.followup.send(
            f"{member.name} a été ajouté au club :thumbs_up:"
        )

    @app_commands.command(name="create")
    @app_commands.autocomplete(club=autocomplete_club)
    @app_commands.checks.has_permissions(manage_guild=True)
    async def create_club(
        self, interaction: Interaction, club: Transform[ClubSchema, ClubTransformer]
    ):
        await interaction.response.defer(thinking=True)
        discord_club = DiscordClub.load(club.id)
        if discord_club is not None:
            await interaction.followup.send(f"Le club : {club.name} existe déjà...")
        else:
            await self.club_service.create_club(club, interaction.guild)
            await interaction.followup.send(f"Le club : {club.name} à été créé")

    @app_commands.command(name="passation")
    @app_commands.autocomplete(club=autocomplete_existing_club)
    async def handover(
        self,
        interaction: Interaction,
        club: Transform[ClubSchema, ClubTransformer],
        new_pres: Member,
        new_treso: Member,
    ):
        await interaction.response.defer(thinking=True)
        discord_club = DiscordClub.load(club.id)

        if not discord_club:
            await interaction.followup.send(f"Le club : {club.name} n'existe pas")
            return
        if (
            not interaction.user.guild_permissions.manage_roles
            and not interaction.user.get_role(discord_club.president_role_id)
        ):
            await interaction.followup.send(
                "Seul le président du club et les admins peuvent retirer un membre"
            )
            return

        await self.club_service.handover(club, new_pres, new_treso, interaction.guild)
        await interaction.followup.send(
            f"La passation est réussi !! {new_pres.mention} Vous êtes le nouveau "
            f"président du club {club.name} et {new_treso.mention} le nouveau trésorier"
        )
