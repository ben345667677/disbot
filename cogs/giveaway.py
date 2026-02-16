import discord
from discord.ext import commands, tasks
from discord import app_commands
import random
import asyncio
from datetime import datetime, timedelta, timezone

ADMIN_ROLE_ID = 1472653727935496285
STAFF_ROLE_ID = 1471769220759945236
VERIFY_ROLE_ID = 1472316348771078275


def is_admin(user: discord.Member) -> bool:
    role_ids = {r.id for r in user.roles}
    return ADMIN_ROLE_ID in role_ids or STAFF_ROLE_ID in role_ids


class GiveawayJoinView(discord.ui.View):
    def __init__(self, cog: "Giveaway"):
        super().__init__(timeout=None)
        self.cog = cog

    @discord.ui.button(label="Join Giveaway 🎉", style=discord.ButtonStyle.green, custom_id="giveaway_join_btn")
    async def join_giveaway(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.cog.active_giveaway is None:
            await interaction.response.send_message("There is no active giveaway right now.", ephemeral=True)
            return

        verify_role = interaction.guild.get_role(VERIFY_ROLE_ID)
        if verify_role not in interaction.user.roles:
            await interaction.response.send_message("You must be verified to join the giveaway!", ephemeral=True)
            return

        giveaway = self.cog.active_giveaway
        if interaction.user.id in giveaway["participants"]:
            await interaction.response.send_message("You already joined this giveaway!", ephemeral=True)
            return

        giveaway["participants"].add(interaction.user.id)

        # Update the embed with new participant count
        embed = self._build_embed(giveaway)
        await interaction.message.edit(embed=embed)
        await interaction.response.send_message("You have entered the giveaway! Good luck! 🍀", ephemeral=True)

    def _build_embed(self, giveaway: dict) -> discord.Embed:
        embed = discord.Embed(
            title="🎉  GIVEAWAY  🎉",
            description=(
                f"**Prize:** {giveaway['prize']}\n\n"
                f"**Ends:** <t:{int(giveaway['end_time'].timestamp())}:R>\n"
                f"**Hosted by:** {giveaway['host'].mention}\n\n"
                f"**Participants:** {len(giveaway['participants'])}\n\n"
                "Click the button below to enter!"
            ),
            color=0x2ecc71,
        )
        embed.set_footer(text="Only verified members can participate")
        return embed


class Giveaway(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.active_giveaway = None  # stores current giveaway dict
        self._timer_task: asyncio.Task | None = None

    async def cog_load(self):
        self.bot.add_view(GiveawayJoinView(self))

    async def cog_unload(self):
        if self._timer_task and not self._timer_task.done():
            self._timer_task.cancel()

    @app_commands.command(name="setup_giveaway", description="Create the giveaway channel")
    async def setup_giveaway(self, interaction: discord.Interaction):
        if not is_admin(interaction.user):
            await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)

        channel_name = "🎉｜giveaways"
        channel = discord.utils.get(interaction.guild.channels, name=channel_name)

        if not channel:
            # Find a matching channel by keyword fallback
            for c in interaction.guild.text_channels:
                if "giveaway" in c.name:
                    channel = c
                    break

        if not channel:
            channel = await interaction.guild.create_text_channel(channel_name)
            await interaction.followup.send(f"Created giveaway channel: {channel.mention}", ephemeral=True)
        else:
            await interaction.followup.send(f"Using existing giveaway channel: {channel.mention}", ephemeral=True)

        embed = discord.Embed(
            title="🎉  Giveaways",
            description=(
                "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                "Welcome to the giveaway room!\n\n"
                "**How it works:**\n"
                ">>> 🎁 Admins will post giveaways here\n"
                "✅ You must be **verified** to participate\n"
                "🎉 Click the button to enter when a giveaway is live\n"
                "🏆 A winner is picked randomly when time runs out\n\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
            ),
            color=0x2b2d31,
        )
        embed.set_thumbnail(url=interaction.guild.icon.url if interaction.guild.icon else None)
        embed.set_footer(text="Stay tuned for the next giveaway!")
        await channel.send(embed=embed)

    @app_commands.command(name="giveaway", description="Start a giveaway")
    @app_commands.describe(prize="What are you giving away?", duration_minutes="Duration in minutes")
    async def start_giveaway(self, interaction: discord.Interaction, prize: str, duration_minutes: int):
        if not is_admin(interaction.user):
            await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)
            return

        if self.active_giveaway is not None:
            await interaction.response.send_message("A giveaway is already running! End it first with `/giveaway_end`.", ephemeral=True)
            return

        if duration_minutes < 1:
            await interaction.response.send_message("Duration must be at least 1 minute.", ephemeral=True)
            return

        end_time = datetime.now(timezone.utc) + timedelta(minutes=duration_minutes)

        self.active_giveaway = {
            "prize": prize,
            "host": interaction.user,
            "channel_id": interaction.channel_id,
            "message_id": None,
            "end_time": end_time,
            "participants": set(),
        }

        view = GiveawayJoinView(self)
        embed = view._build_embed(self.active_giveaway)

        await interaction.response.send_message(embed=embed, view=view)
        msg = await interaction.original_response()
        self.active_giveaway["message_id"] = msg.id

        # Start auto-end timer
        self._timer_task = self.bot.loop.create_task(self._auto_end(duration_minutes * 60))

    async def _auto_end(self, seconds: float):
        await asyncio.sleep(seconds)
        await self._end_giveaway()

    async def _end_giveaway(self):
        if self.active_giveaway is None:
            return

        giveaway = self.active_giveaway
        self.active_giveaway = None

        channel = self.bot.get_channel(giveaway["channel_id"])
        if channel is None:
            return

        participants = giveaway["participants"]
        if not participants:
            await channel.send("🎉 **Giveaway ended!** No one participated. No winner this time.")
            return

        winner_id = random.choice(list(participants))
        winner = channel.guild.get_member(winner_id)
        winner_mention = winner.mention if winner else f"<@{winner_id}>"

        embed = discord.Embed(
            title="🎉  GIVEAWAY ENDED  🎉",
            description=(
                f"**Prize:** {giveaway['prize']}\n\n"
                f"**Winner:** {winner_mention}\n"
                f"**Participants:** {len(participants)}\n\n"
                "Congratulations! 🏆"
            ),
            color=0xf1c40f,
        )
        embed.set_footer(text=f"Hosted by {giveaway['host'].display_name}")

        # Edit original message to disable button
        try:
            msg = await channel.fetch_message(giveaway["message_id"])
            ended_view = discord.ui.View()
            btn = discord.ui.Button(label="Giveaway Ended", style=discord.ButtonStyle.grey, disabled=True, custom_id="giveaway_ended_btn")
            ended_view.add_item(btn)
            await msg.edit(view=ended_view)
        except discord.NotFound:
            pass

        await channel.send(embed=embed)

    @app_commands.command(name="giveaway_end", description="End the current giveaway early")
    async def end_giveaway(self, interaction: discord.Interaction):
        if not is_admin(interaction.user):
            await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)
            return

        if self.active_giveaway is None:
            await interaction.response.send_message("There is no active giveaway to end.", ephemeral=True)
            return

        # Cancel the auto-end timer
        if self._timer_task and not self._timer_task.done():
            self._timer_task.cancel()

        await interaction.response.send_message("Ending giveaway...", ephemeral=True)
        await self._end_giveaway()


async def setup(bot):
    await bot.add_cog(Giveaway(bot))
