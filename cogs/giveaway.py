import discord
from discord.ext import commands
from discord import app_commands
import random
import asyncio
from datetime import datetime, timedelta, timezone
from config import VERIFY_ROLE_ID, is_admin


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

        # Check required role
        if giveaway["required_role_id"] is not None:
            required_role = interaction.guild.get_role(giveaway["required_role_id"])
            role_name = required_role.mention if required_role else "Unknown Role"
            if required_role not in interaction.user.roles:
                await interaction.response.send_message(
                    f"You need the {role_name} role to join this giveaway!", ephemeral=True
                )
                return

        if interaction.user.id in giveaway["participants"]:
            await interaction.response.send_message("You already joined this giveaway!", ephemeral=True)
            return

        giveaway["participants"].add(interaction.user.id)

        # Update the embed with new participant count
        embed = build_active_embed(giveaway)
        await interaction.message.edit(embed=embed)
        await interaction.response.send_message("You have entered the giveaway! Good luck! 🍀", ephemeral=True)


def build_active_embed(giveaway: dict) -> discord.Embed:
    role_text = "Everyone"
    if giveaway["required_role_id"] is not None:
        role_text = f"<@&{giveaway['required_role_id']}>"

    embed = discord.Embed(
        title="🎰  GIVEAWAY  🎰",
        description=(
            f"🎁 **Prize:** {giveaway['prize']}\n\n"
            f"⏰ **Ends:** <t:{int(giveaway['end_time'].timestamp())}:R>\n"
            f"👑 **Hosted by:** {giveaway['host'].mention}\n"
            f"🏆 **Winners:** {giveaway['winner_count']}\n"
            f"🎭 **Required Role:** {role_text}\n\n"
            f"👥 **Participants:** {len(giveaway['participants'])}\n\n"
            "Click the button below to enter!"
        ),
        color=0x2ecc71,
    )
    if giveaway.get("guild_icon"):
        embed.set_thumbnail(url=giveaway["guild_icon"])
    embed.set_footer(text="Good luck to everyone!")
    return embed


def build_ended_embed(giveaway: dict, winner_mentions: list[str]) -> discord.Embed:
    winners_text = ", ".join(winner_mentions) if winner_mentions else "No participants"
    embed = discord.Embed(
        title="🎰  GIVEAWAY ENDED  🎰",
        description=(
            f"🎁 **Prize:** {giveaway['prize']}\n"
            f"🏆 **Winner(s):** {winners_text}\n"
            f"👥 **Participants:** {len(giveaway['participants'])}\n\n"
            "Congratulations! 🎊"
        ),
        color=0xF1C40F,
    )
    embed.set_footer(text=f"Hosted by {giveaway['host'].display_name}")
    return embed


def build_cancelled_embed() -> discord.Embed:
    return discord.Embed(
        title="🎰  GIVEAWAY CANCELLED  🎰",
        description="This giveaway has been cancelled.",
        color=0xE74C3C,
    )


def pick_winners(participants: set[int], count: int) -> list[int]:
    pool = list(participants)
    return random.sample(pool, min(count, len(pool)))


class Giveaway(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.active_giveaway: dict | None = None
        self.last_giveaway: dict | None = None
        self._timer_task: asyncio.Task | None = None

    async def cog_load(self):
        self.bot.add_view(GiveawayJoinView(self))

    async def cog_unload(self):
        if self._timer_task and not self._timer_task.done():
            self._timer_task.cancel()

    # ── Setup ────────────────────────────────────────────────────────

    @app_commands.command(name="setup_giveaway", description="Create the giveaway channel")
    async def setup_giveaway(self, interaction: discord.Interaction):
        if not is_admin(interaction.user):
            await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)

        channel_name = "🎰｜giveaways"
        channel = discord.utils.get(interaction.guild.channels, name=channel_name)

        if not channel:
            for c in interaction.guild.text_channels:
                if "giveaway" in c.name:
                    channel = c
                    break

        if not channel:
            overwrites = {
                interaction.guild.default_role: discord.PermissionOverwrite(
                    read_messages=True, send_messages=False
                ),
                interaction.guild.me: discord.PermissionOverwrite(
                    read_messages=True, send_messages=True
                ),
            }
            channel = await interaction.guild.create_text_channel(channel_name, overwrites=overwrites)
            await interaction.followup.send(f"Created giveaway channel: {channel.mention}", ephemeral=True)
        else:
            await interaction.followup.send(f"Using existing giveaway channel: {channel.mention}", ephemeral=True)

        embed = discord.Embed(
            title="🎰  Giveaways",
            description=(
                "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                "Welcome to the giveaway room!\n\n"
                "**How it works:**\n"
                ">>> 🎁 Admins will post giveaways here\n"
                "✅ You must be **verified** to participate\n"
                "🎉 Click the button to enter when a giveaway is live\n"
                "🏆 Winners are picked randomly when time runs out\n\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
            ),
            color=0x2B2D31,
        )
        embed.set_thumbnail(url=interaction.guild.icon.url if interaction.guild.icon else None)
        embed.set_footer(text="Stay tuned for the next giveaway!")
        await channel.send(embed=embed)

    # ── Start ────────────────────────────────────────────────────────

    @app_commands.command(name="giveaway", description="Start a giveaway")
    @app_commands.describe(
        prize="What are you giving away?",
        duration_minutes="Duration in minutes",
        winners="Number of winners (default 1)",
        required_role="Only members with this role can join",
    )
    async def start_giveaway(
        self,
        interaction: discord.Interaction,
        prize: str,
        duration_minutes: int,
        winners: int = 1,
        required_role: discord.Role | None = None,
    ):
        if not is_admin(interaction.user):
            await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)
            return

        if self.active_giveaway is not None:
            await interaction.response.send_message(
                "A giveaway is already running! End it first with `/giveaway_end`.", ephemeral=True
            )
            return

        if duration_minutes < 1:
            await interaction.response.send_message("Duration must be at least 1 minute.", ephemeral=True)
            return

        if winners < 1:
            await interaction.response.send_message("Winner count must be at least 1.", ephemeral=True)
            return

        end_time = datetime.now(timezone.utc) + timedelta(minutes=duration_minutes)

        self.active_giveaway = {
            "prize": prize,
            "host": interaction.user,
            "channel_id": interaction.channel_id,
            "message_id": None,
            "end_time": end_time,
            "participants": set(),
            "winner_count": winners,
            "required_role_id": required_role.id if required_role else None,
            "guild_icon": interaction.guild.icon.url if interaction.guild.icon else None,
        }

        view = GiveawayJoinView(self)
        embed = build_active_embed(self.active_giveaway)

        await interaction.response.send_message(embed=embed, view=view)
        msg = await interaction.original_response()
        self.active_giveaway["message_id"] = msg.id

        self._timer_task = self.bot.loop.create_task(self._auto_end(duration_minutes * 60))

    # ── Auto-end timer ───────────────────────────────────────────────

    async def _auto_end(self, seconds: float):
        await asyncio.sleep(seconds)
        await self._end_giveaway()

    # ── End (shared logic) ───────────────────────────────────────────

    async def _end_giveaway(self):
        if self.active_giveaway is None:
            return

        giveaway = self.active_giveaway
        self.active_giveaway = None
        self.last_giveaway = giveaway

        channel = self.bot.get_channel(giveaway["channel_id"])
        if channel is None:
            return

        participants = giveaway["participants"]

        if not participants:
            winner_mentions = []
            announce_text = "🎰 **Giveaway ended!** No one participated. No winner this time."
        else:
            winner_ids = pick_winners(participants, giveaway["winner_count"])
            winner_mentions = []
            for wid in winner_ids:
                member = channel.guild.get_member(wid)
                winner_mentions.append(member.mention if member else f"<@{wid}>")
            announce_text = None

        embed = build_ended_embed(giveaway, winner_mentions)

        # Edit original message to disable the button
        try:
            msg = await channel.fetch_message(giveaway["message_id"])
            ended_view = discord.ui.View()
            btn = discord.ui.Button(
                label="Giveaway Ended", style=discord.ButtonStyle.grey,
                disabled=True, custom_id="giveaway_ended_btn",
            )
            ended_view.add_item(btn)
            await msg.edit(embed=embed, view=ended_view)
        except discord.NotFound:
            pass

        if announce_text:
            await channel.send(announce_text)
        else:
            mentions = " ".join(winner_mentions)
            await channel.send(f"🎊 Congratulations {mentions}! You won **{giveaway['prize']}**!")

    # ── End command ──────────────────────────────────────────────────

    @app_commands.command(name="giveaway_end", description="End the current giveaway early")
    async def end_giveaway(self, interaction: discord.Interaction):
        if not is_admin(interaction.user):
            await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)
            return

        if self.active_giveaway is None:
            await interaction.response.send_message("There is no active giveaway to end.", ephemeral=True)
            return

        if self._timer_task and not self._timer_task.done():
            self._timer_task.cancel()

        await interaction.response.send_message("Ending giveaway...", ephemeral=True)
        await self._end_giveaway()

    # ── Cancel command ───────────────────────────────────────────────

    @app_commands.command(name="giveaway_cancel", description="Cancel the active giveaway without picking a winner")
    async def cancel_giveaway(self, interaction: discord.Interaction):
        if not is_admin(interaction.user):
            await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)
            return

        if self.active_giveaway is None:
            await interaction.response.send_message("There is no active giveaway to cancel.", ephemeral=True)
            return

        if self._timer_task and not self._timer_task.done():
            self._timer_task.cancel()

        giveaway = self.active_giveaway
        self.active_giveaway = None

        channel = self.bot.get_channel(giveaway["channel_id"])
        if channel:
            embed = build_cancelled_embed()
            try:
                msg = await channel.fetch_message(giveaway["message_id"])
                cancelled_view = discord.ui.View()
                btn = discord.ui.Button(
                    label="Giveaway Cancelled", style=discord.ButtonStyle.grey,
                    disabled=True, custom_id="giveaway_cancelled_btn",
                )
                cancelled_view.add_item(btn)
                await msg.edit(embed=embed, view=cancelled_view)
            except discord.NotFound:
                await channel.send(embed=embed)

        await interaction.response.send_message("Giveaway has been cancelled.", ephemeral=True)

    # ── Reroll command ───────────────────────────────────────────────

    @app_commands.command(name="giveaway_reroll", description="Re-pick a new winner from the last giveaway")
    async def reroll_giveaway(self, interaction: discord.Interaction):
        if not is_admin(interaction.user):
            await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)
            return

        if self.last_giveaway is None:
            await interaction.response.send_message("There is no previous giveaway to reroll.", ephemeral=True)
            return

        participants = self.last_giveaway["participants"]
        if not participants:
            await interaction.response.send_message("The last giveaway had no participants.", ephemeral=True)
            return

        winner_ids = pick_winners(participants, 1)
        winner_id = winner_ids[0]
        member = interaction.guild.get_member(winner_id)
        winner_mention = member.mention if member else f"<@{winner_id}>"

        channel = self.bot.get_channel(self.last_giveaway["channel_id"])
        if channel:
            await channel.send(
                f"🎰 **Giveaway Reroll** — The new winner for **{self.last_giveaway['prize']}** is {winner_mention}! Congratulations! 🎊"
            )

        await interaction.response.send_message(f"Rerolled! New winner: {winner_mention}", ephemeral=True)


async def setup(bot):
    await bot.add_cog(Giveaway(bot))
