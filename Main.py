from discord import app_commands
from discord.ext import commands
from backend import *
from typing import Optional

ConfigPath = "Config.ini"
Token = get_config(ConfigPath, "bot", "token")

intents = discord.Intents.default()
intents.members = True
intents.guilds = True
intents.message_content = True
bot = commands.Bot(command_prefix=get_config(ConfigPath, "bot", "prefix"), intents=intents)

print(get_config(ConfigPath, "bot", "prefix"))

@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"Bot connecté en tant que {bot.user}")

@bot.command()
async def ping(ctx):
    await ctx.send("Pong !")

@bot.tree.command(name="newclub", description="Crée un club avec rôles et salons.")
@app_commands.describe(club_name="Nom complet du club")
async def newClub(interaction: discord.Interaction, club_name: str):
    auteur = interaction.user

    if not have_AdminRoles(ConfigPath, auteur.roles):
        await interaction.response.send_message("⛔ Tu n'as pas les permissions pour faire ça.", ephemeral=True)
        return

    await interaction.response.defer(thinking=True)  # ping Discord pour lui dire que c'est en cours délais de création role/salon

    guild = interaction.guild
    created_roles = await create_newclubRole(guild, club_name, ConfigPath)
    await create_clubCategory(guild, club_name, created_roles)

    await interaction.followup.send(f"✅ Club `{club_name}` créé avec succès !")



@bot.tree.command(name="giverole", description="Donne un rôle de club à un membre.")
@app_commands.describe(
    member="Membre à qui donner le rôle",
    club_name="Nom du club (ex: Club Info)",
    prefix="Rôle à donner (ex: Staff, Président.e, Tréso)"
)
async def giveRole(interaction: discord.Interaction, member: discord.Member, club_name: str, prefix: str):
    auteur = interaction.user
    guild = interaction.guild

    # Vérification des droits
    if not (has_president_or_treso_role(auteur, guild, club_name) or have_AdminRoles(ConfigPath, auteur.roles)):
        await interaction.response.send_message("⛔ Tu n'as pas les permissions pour faire ça.", ephemeral=True)
        return

    role_name = f"{prefix} {club_name}"
    role = discord.utils.get(guild.roles, name=role_name)

    if role is None:
        await interaction.response.send_message(f"❌ Le rôle `{role_name}` n'existe pas.", ephemeral=True)
        return

    try:
        await member.add_roles(role)
        await interaction.response.send_message(f"✅ Le rôle `{role.name}` a été ajouté à {member.mention}.")
    except discord.Forbidden:
        await interaction.response.send_message("⛔ Je n'ai pas la permission d'ajouter ce rôle.", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"⚠️ Une erreur est survenue : {e}", ephemeral=True)


@bot.tree.command(name="updateclub", description="Associe un président et un trésorier à un club.")
@app_commands.describe(
    club_name="Nom du club",
    president="Mention du président",
    treso="Mention du trésorier"
)
async def updateclub(interaction: discord.Interaction, club_name: str, president: discord.Member, treso: discord.Member):
    autorRoles = interaction.user.roles

    if not have_AdminRoles(ConfigPath, autorRoles):
        await interaction.response.send_message("⛔ Tu n'as pas les permissions pour faire ça.")
        return

    Prole = discord.utils.get(interaction.guild.roles, name=f"Président.e {club_name}")
    Trole = discord.utils.get(interaction.guild.roles, name=f"Tréso {club_name}")

    if Prole is None or Trole is None:
        await interaction.response.send_message(f"❌ Le club `{club_name}` n'existe pas.")
        return

    try:
        await president.add_roles(Prole)
        await treso.add_roles(Trole)
        await interaction.response.send_message(f"📌 Mise à jour du club `{club_name}` :\n👤 Président.e : {president.mention}\n💰 Tréso : {treso.mention}")
    except discord.Forbidden:
        await interaction.response.send_message("⛔ Je n'ai pas la permission d'ajouter ces rôles.")
        return
    except Exception as e:
        await interaction.response.send_message(f"⚠️ Une erreur est survenue : {e}")
        return


@bot.tree.command(name="createrole", description="Crée un rôle avec le préfixe du club.")
@app_commands.describe(
    role_name="Nom du rôle",
    club_name="Nom du club (ex: Club Info) [facultatif si admin pour la création role AE]",
)
async def createRole(
        interaction: discord.Interaction,
        role_name: str,
        club_name: Optional[str] = None
):
    auteur = interaction.user

    # Si club_name non fourni, seuls les admins peuvent utiliser
    if club_name is None:
        if not have_AdminRoles(ConfigPath, auteur.roles):
            await interaction.response.send_message("⛔ Tu dois être admin pour créer un rôle sans club spécifié.", ephemeral=True)
            return
        full_role_name = role_name
    else:
        full_role_name = f"{role_name} {club_name}"

    # Vérifie si le rôle existe déjà
    existing_role = discord.utils.get(interaction.guild.roles, name=full_role_name)
    if existing_role:
        await interaction.response.send_message(f"⚠️ Le rôle `{full_role_name}` existe déjà.", ephemeral=True)
        return

    # Création du rôle
    try:
        new_role = await interaction.guild.create_role(name=full_role_name, mentionable=True)
        await interaction.response.send_message(f"✅ Rôle `{new_role.name}` créé avec succès.")
    except discord.Forbidden:
        await interaction.response.send_message("⛔ Je n'ai pas les permissions pour créer un rôle.", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"⚠️ Une erreur est survenue : {e}", ephemeral=True)


@bot.tree.command(name="infoclub", description="Toutes les informations concernant un club.")
@app_commands.describe(
    club_name="Nom du club (ex: Club Info)"
)
async def infoclub(interaction: discord.Interaction, club_name: str):
    auteur = interaction.user
    guild = interaction.guild

    try:
        role_prefixes = get_config(ConfigPath, "roles", "role_prefix")
        found_roles = []

        for prefix in role_prefixes:
            role_name = f"{prefix} {club_name}"
            role = discord.utils.get(guild.roles, name=role_name)
            if role:
                member_count = sum(1 for m in guild.members if role in m.roles)
                found_roles.append((role.name, member_count))

        if not found_roles:
            await interaction.response.send_message(f"❌ Aucun rôle trouvé pour le club `{club_name}`.", ephemeral=True)
            return

    except Exception as e:
        await interaction.response.send_message(f"⚠️ Une erreur est survenue : {e}", ephemeral=True)

    # Compter les membres uniques avec au moins un des rôles du club
    members_with_roles = set()
    for role_name, _ in found_roles:
        role = discord.utils.get(guild.roles, name=role_name)
        if role:
            for member in guild.members:
                if role in member.roles:
                    members_with_roles.add(member)

    # recherche des rôles président & trésorier
    president_role = discord.utils.get(guild.roles, name=f"président {club_name}")
    treso_role = discord.utils.get(guild.roles, name=f"trésorier {club_name}")

    presidents = [m.mention for m in guild.members if president_role in m.roles] if president_role else []
    tresos = [m.mention for m in guild.members if treso_role in m.roles] if treso_role else []

    # Création du message
    result = f"📘 **Informations : `{club_name}`**\n"
    result += f"- 🏆 Président·e : {', '.join(presidents) if presidents else 'Aucun'}\n"
    result += f"- 💰 Trésorier·e : {', '.join(tresos) if tresos else 'Aucun'}\n"
    result += f"- 👥 Membres totaux : **{len(members_with_roles)}**\n"
    result += f"\n📊 **Rôles associés :**\n"

    for role_name, count in found_roles:
        result += f"- `{role_name}` : **{count}** membres\n"


    await interaction.response.send_message(result)




bot.run(Token)
