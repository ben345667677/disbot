import discord
from discord.ext import commands
from discord import app_commands
ADMIN_ROLE_ID = 1472653727935496285
STAFF_ROLE_ID = 1471769220759945236


def is_admin(user: discord.Member) -> bool:
    role_ids = {r.id for r in user.roles}
    return ADMIN_ROLE_ID in role_ids or STAFF_ROLE_ID in role_ids


class Info(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def _send_info_embed(self, guild):
        channel = discord.utils.get(guild.text_channels, name="command")

        if not channel:
            overwrites = {
                guild.default_role: discord.PermissionOverwrite(send_messages=False),
                guild.me: discord.PermissionOverwrite(send_messages=True)
            }
            try:
                channel = await guild.create_text_channel("command", overwrites=overwrites)
                print(f"Created 'command' channel in {guild.name}")
            except Exception as e:
                print(f"Failed to create 'command' channel in {guild.name}: {e}")
                return

        if channel:
            found = False
            async for message in channel.history(limit=5):
                if message.author == self.bot.user and message.embeds and message.embeds[0].title == "📜 רשימת פקודות ומערכות":
                    found = True
                    break

            if not found:
                embed = discord.Embed(
                    title="📜 רשימת פקודות ומערכות",
                    description="הנה הסבר על כל הפקודות והמערכות בבוט:",
                    color=discord.Color.purple()
                )

                embed.add_field(
                    name="🛠️ הגדרות (Admins)",
                    value=(
                        "**`/setup_verify`**\n"
                        "יוצר את פאנל האימות. משתמשים לוחצים על הכפתור כדי לקבל רול 'Verified'.\n\n"
                        "**`/setup_tickets`**\n"
                        "יוצר את פאנל הטיקטים. משתמשים יכולים לפתוח פנייה אישית לצוות.\n\n"
                        "**`/setup_commands`**\n"
                        "יוצר את הערוץ הזה עם רשימת הפקודות.\n\n"
                        "**`/pay`**\n"
                        "מעביר טיקט לקטגוריית PAY (צוות בלבד)."
                    ),
                    inline=False
                )

                embed.add_field(
                    name="🤖 מערכות אוטומטיות",
                    value=(
                        "**AI Chat (בינה מלאכותית)**\n"
                        "הבוט עונה אוטומטית על כל הודעה בערוצים בשם `ai-chat` או `ai-room`.\n\n"
                        "**Welcome (קבלת פנים)**\n"
                        "הבוט שולח הודעת ברוכים הבאים מעוצבת בערוץ `welcome`, `general` או `chat`.\n\n"
                        "**Anti-Spam (אבטחה)**\n"
                        "הבוט משתיק אוטומטית (Mute לדקה) משתמשים ששולחים מעל 5 הודעות ב-5 שניות."
                    ),
                    inline=False
                )

                embed.set_footer(text="Smart Store Bot • פותח על ידי Gemini")
                await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_ready(self):
        for guild in self.bot.guilds:
            await self._send_info_embed(guild)

    @app_commands.command(name="setup_commands", description="Create the commands info channel")
    async def setup_commands(self, interaction: discord.Interaction):
        if not is_admin(interaction.user):
            await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)
        await self._send_info_embed(interaction.guild)
        await interaction.followup.send("Commands info panel has been set up!", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Info(bot))
