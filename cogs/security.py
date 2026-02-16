import discord
from discord.ext import commands
from discord import app_commands
import datetime
from config import is_admin


class Security(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # 5 messages per 5 seconds
        self.spam_cd = commands.CooldownMapping.from_cooldown(5, 5.0, commands.BucketType.member)

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        # Simple spam detection
        bucket = self.spam_cd.get_bucket(message)
        retry_after = bucket.update_rate_limit()

        if retry_after:
            try:
                # Timeout for 60 seconds
                await message.author.timeout(datetime.timedelta(seconds=60), reason="Spamming")
                await message.channel.send(f"{message.author.mention}, you have been timed out for 60 seconds for spamming!", delete_after=5)
            except discord.Forbidden:
                print(f"Could not timeout {message.author}: Missing permissions")
            except Exception as e:
                print(f"Error timing out {message.author}: {e}")

    @app_commands.command(name="delete", description="Delete all messages in this channel")
    async def delete(self, interaction: discord.Interaction):
        if not is_admin(interaction.user):
            await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)
            return

        view = DeleteConfirmView(interaction.channel)
        await interaction.response.send_message(
            "Are you sure you want to **delete ALL messages** in this channel? This cannot be undone.",
            view=view,
            ephemeral=True,
        )


class DeleteConfirmView(discord.ui.View):
    def __init__(self, channel: discord.TextChannel):
        super().__init__(timeout=15)
        self.channel = channel

    @discord.ui.button(label="Confirm Delete", style=discord.ButtonStyle.danger)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(content="Deleting all messages...", view=None)
        try:
            await self.channel.purge(limit=None)
        except Exception as e:
            await interaction.followup.send(f"Failed to delete messages: {e}", ephemeral=True)
        self.stop()

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.secondary)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(content="Delete cancelled.", view=None)
        self.stop()

    async def on_timeout(self):
        pass


async def setup(bot):
    await bot.add_cog(Security(bot))
