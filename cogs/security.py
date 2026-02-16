import discord
from discord.ext import commands
from discord import app_commands
import datetime
ADMIN_ROLE_ID = 1472653727935496285
STAFF_ROLE_ID = 1471769220759945236


def is_admin(user: discord.Member) -> bool:
    role_ids = {r.id for r in user.roles}
    return ADMIN_ROLE_ID in role_ids or STAFF_ROLE_ID in role_ids


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

        await interaction.response.send_message("Deleting all messages...", ephemeral=True)

        try:
            await interaction.channel.purge(limit=None)
        except Exception as e:
            await interaction.followup.send(f"Failed to delete messages: {e}", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Security(bot))
