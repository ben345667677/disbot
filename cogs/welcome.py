import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime
ADMIN_ROLE_ID = 1472653727935496285
STAFF_ROLE_ID = 1471769220759945236


def is_admin(user: discord.Member) -> bool:
    role_ids = {r.id for r in user.roles}
    return ADMIN_ROLE_ID in role_ids or STAFF_ROLE_ID in role_ids


class Welcome(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="setup_welcome", description="Create the welcome channel")
    async def setup_welcome(self, interaction: discord.Interaction):
        if not is_admin(interaction.user):
            await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)

        channel = discord.utils.get(interaction.guild.text_channels, name="welcome")

        if channel:
            await interaction.followup.send(f"Welcome channel already exists: {channel.mention}", ephemeral=True)
            return

        overwrites = {
            interaction.guild.default_role: discord.PermissionOverwrite(send_messages=False),
            interaction.guild.me: discord.PermissionOverwrite(send_messages=True)
        }
        try:
            channel = await interaction.guild.create_text_channel("welcome", overwrites=overwrites)
            await interaction.followup.send(f"Created welcome channel: {channel.mention}", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"Failed to create welcome channel: {e}", ephemeral=True)

    @commands.Cog.listener()
    async def on_member_join(self, member):
        channel = discord.utils.get(member.guild.text_channels, name="welcome")

        if not channel:
            return

        now = datetime.now().strftime("%m/%d/%Y %I:%M %p")
        member_count = member.guild.member_count

        embed = discord.Embed(
            description=(
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                f"Hey {member.mention}, Welcome To **{member.guild.name}**!\n\n"
                f"We Are Now **{member_count}** Members!\n\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
            ),
            color=0x2b2d31
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        if member.guild.icon:
            embed.set_footer(text=f"{member.guild.name} • {now}", icon_url=member.guild.icon.url)
        else:
            embed.set_footer(text=f"{member.guild.name} • {now}")

        view = discord.ui.View()
        view.add_item(discord.ui.Button(
            label=f"{member_count} Members",
            style=discord.ButtonStyle.secondary,
            emoji="👥",
            disabled=True
        ))

        await channel.send(embed=embed, view=view)

async def setup(bot):
    await bot.add_cog(Welcome(bot))
