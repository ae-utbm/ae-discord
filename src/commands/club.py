from __future__ import annotations

from typing import TYPE_CHECKING

from discord import Interaction, Member, app_commands, utils
from discord.app_commands import Choice, Transform, Transformer
from discord.ext import commands
from discord.ext.commands import BadArgument

from src.client import ClubSchema  # noqa TC001
from src.db.models import Club
from src.services.club import ClubService
from src.settings import Settings

if TYPE_CHECKING:
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
    def __init__(self, bot: AeBot):
        self.club_service = ClubService(bot)
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
        db_club = Club.get_or_none(Club.sith_id == club.id)
        if not db_club:
            await interaction.followup.send(f"Le club : {club.name} n'existe pas")
            return
        role_membre = utils.get(member.guild.roles, id=db_club.member_role_id)
        if (
            not interaction.user.guild_permissions.manage_roles
            and not interaction.user.get_role(db_club.president_role_id)
        ):
            await interaction.followup.send(
                "Seul le président du club et les admins peuvent retirer un membre"
            )
            return
        if role_membre not in member.roles:
            await interaction.followup.send("Cet utilisateur n'est pas dans le club")
            return
        await self.club_service.remove_member(db_club, member)
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
        db_club = Club.get_or_none(Club.sith_id == club.id)
        role_membre = member.guild.get_role(db_club.member_role_id)
        if not db_club:
            await interaction.followup.send(f"Le club : {club.name} n'existe pas")
            return
        if (
            not interaction.user.guild_permissions.manage_roles
            and not interaction.user.get_role(db_club.president_role_id)
        ):
            await interaction.followup.send(
                "Seul le président du club et les admins peuvent ajouter un membre"
            )
            return
        if role_membre in member.roles:
            await interaction.followup.send("Cet utilisateur est déjà dans le club")
            return
        await self.club_service.add_member(db_club, member)
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
        if Club.filter(Club.sith_id == club.id).exists():
            await interaction.followup.send(f"Le club : {club.name} existe déjà...")
        else:
            await self.club_service.create_club(club, interaction.guild)
            await interaction.followup.send(f"Le club : {club.name} à été créé")

    @app_commands.command(name="passation")
    @app_commands.autocomplete(club=autocomplete_existing_club)
    @app_commands.checks.has_permissions(manage_roles=True)
    async def handover(
        self,
        interaction: Interaction,
        club: Transform[ClubSchema, ClubTransformer],
        new_president: Member,
        new_treasurer: Member,
    ):
        await interaction.response.defer(thinking=True)
        db_club = Club.get_or_none(Club.sith_id == club.id)
        guild = interaction.guild

        if not db_club:
            await interaction.followup.send(f"Le club : {club.name} n'existe pas")
            return

        await self.club_service.handover(club, new_president, new_treasurer, guild)
        annonce = await self.club_service.get_channel(
            guild, db_club.category_id, f"annonces {club.name}".lower()
        )

        if annonce:
            await annonce.send(
                f"La passation est réussie !! {new_president.mention}, vous êtes "
                f"le nouveau président du club {club.name}"
                f" et {new_treasurer.mention} le nouveau trésorier !!"
            )
        else:
            await interaction.followup.send(
                "Attention, ce club n'a pas ses salons de discussion.\n"
                "La passation va quand même se faire, mais il faut "
                "contacter un des mainteneurs du bot pour remettre "
                "les salons en place"
            )
        await interaction.followup.send("Passation effectuée")

    @app_commands.command(name="arret")
    @app_commands.autocomplete(club=autocomplete_existing_club)
    @app_commands.checks.has_permissions(manage_guild=True)
    async def stop_club(
        self, interaction: Interaction, club: Transform[ClubSchema, ClubTransformer]
    ):
        await interaction.response.defer(thinking=True)
        db_club = Club.get_or_none(Club.sith_id == club.id)
        await self.club_service.stop_club(db_club, interaction.guild)
        annonce = await self.club_service.get_channel(
            interaction.guild, db_club.category_id, f"annonces {club.name}".lower()
        )

        if annonce:
            await annonce.send(
                "Le club, n'ayant pas été repris, est "
                "temporairement fermé jusqu'à reprise du club"
            )
        await interaction.followup.send(f"Le club : {club.name} à été arrêté")
