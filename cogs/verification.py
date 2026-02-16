import discord
from discord.ext import commands
from discord import app_commands
from config import VERIFY_ROLE_ID, is_admin


class VerifyView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Verify your account!", style=discord.ButtonStyle.green, emoji="🔒", custom_id="verify_button")
    async def verify_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        role = interaction.guild.get_role(VERIFY_ROLE_ID)

        if role:
            if role in interaction.user.roles:
                await interaction.response.send_message("You are already verified!", ephemeral=True)
            else:
                try:
                    await interaction.user.add_roles(role)
                    await interaction.response.send_message("You have been verified!", ephemeral=True)
                except discord.Forbidden:
                    await interaction.response.send_message("I don't have permission to add that role.", ephemeral=True)
                except Exception as e:
                    await interaction.response.send_message(f"An error occurred: {e}", ephemeral=True)
        else:
            await interaction.response.send_message("Validation role not found. Please contact an administrator.", ephemeral=True)

class Verification(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="setup_verify", description="Create the verification panel")
    async def setup_verify(self, interaction: discord.Interaction):
        if not is_admin(interaction.user):
            await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)

        channel_name = "verify-✅"
        channel = discord.utils.get(interaction.guild.channels, name=channel_name)

        if not channel:
            channel = await interaction.guild.create_text_channel(channel_name)
            await interaction.followup.send(f"Created verification channel: {channel.mention}", ephemeral=True)
        else:
            await interaction.followup.send(f"Using existing verification channel: {channel.mention}", ephemeral=True)

        embed = discord.Embed(
            title="Hold on, wait a minute...",
            description="Looks like you haven't verified your account yet. To view any content within this guild you'll need to click the verification redirect button below!",
            color=0x2b2d31
        )
        embed.set_author(name="Guild Restore", icon_url="https://cdn.discordapp.com/emojis/1154522866637680650.webp?size=96&quality=lossless")

        await channel.send(embed=embed, view=VerifyView())

    async def cog_load(self):
        self.bot.add_view(VerifyView())

async def setup(bot):
    await bot.add_cog(Verification(bot))
