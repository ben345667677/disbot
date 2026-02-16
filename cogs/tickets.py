import discord
from discord.ext import commands
from discord import app_commands
import asyncio

ADMIN_ROLE_ID = 1472653727935496285
STAFF_ROLE_ID = 1471769220759945236
TICKET_CATEGORY_ID = 1471769129156349952
PAY_CATEGORY_ID = 1471769793433702462


def is_admin(user: discord.Member) -> bool:
    role_ids = {r.id for r in user.roles}
    return ADMIN_ROLE_ID in role_ids or STAFF_ROLE_ID in role_ids


class TicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Open Ticket", style=discord.ButtonStyle.primary, emoji="📩", custom_id="ticket_create_btn")
    async def create_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild = interaction.guild
        staff_role = guild.get_role(STAFF_ROLE_ID)

        if not staff_role:
             await interaction.response.send_message("Staff role not found in guild.", ephemeral=True)
             return

        # Check if user already has an open ticket
        category = guild.get_channel(TICKET_CATEGORY_ID)
        if not category or not isinstance(category, discord.CategoryChannel):
            await interaction.response.send_message("Ticket category not found.", ephemeral=True)
            return

        channel_name = f"ticket-{interaction.user.name}"

        for ch in category.text_channels:
            if ch.name == channel_name:
                await interaction.response.send_message(f"You already have an open ticket: {ch.mention}", ephemeral=True)
                return

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            interaction.user: discord.PermissionOverwrite(view_channel=True, send_messages=True),
            staff_role: discord.PermissionOverwrite(view_channel=True, send_messages=True)
        }

        admin_role = guild.get_role(ADMIN_ROLE_ID)
        if admin_role:
            overwrites[admin_role] = discord.PermissionOverwrite(view_channel=True, send_messages=True)

        try:
            channel = await guild.create_text_channel(channel_name, category=category, overwrites=overwrites)
            await interaction.response.send_message(f"Ticket created: {channel.mention}", ephemeral=True)

            embed = discord.Embed(
                title="Ticket Created",
                description=f"Welcome {interaction.user.mention}!\nSupport will be with you shortly.",
                color=0x3ba55c
            )
            await channel.send(embed=embed, view=TicketCloseView())

        except Exception as e:
            await interaction.response.send_message(f"Failed to create ticket: {e}", ephemeral=True)


class TicketCloseView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Close Ticket", style=discord.ButtonStyle.danger, emoji="🔒", custom_id="ticket_close_btn")
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not is_admin(interaction.user):
            await interaction.response.send_message("Only staff/admins can close tickets.", ephemeral=True)
            return

        await interaction.response.send_message("Ticket will be deleted in 5 seconds...")
        await asyncio.sleep(5)
        try:
            await interaction.channel.delete(reason=f"Ticket closed by {interaction.user}")
        except Exception as e:
            print(f"Failed to delete ticket channel: {e}")


class Tickets(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def cog_load(self):
        self.bot.add_view(TicketView())
        self.bot.add_view(TicketCloseView())

    @app_commands.command(name="setup_tickets", description="Create the ticket support panel")
    async def setup_tickets(self, interaction: discord.Interaction):
        if not is_admin(interaction.user):
            await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)

        category = interaction.guild.get_channel(TICKET_CATEGORY_ID)
        if not category or not isinstance(category, discord.CategoryChannel):
            await interaction.followup.send("Ticket category not found.", ephemeral=True)
            return

        target_name = "🎫｜tickets"
        channel = None

        for c in category.text_channels:
            if c.name == target_name or "tickets" in c.name:
                channel = c
                break

        if not channel:
            channel = await category.create_text_channel(target_name)
            await interaction.followup.send(f"Created ticket panel channel: {channel.mention}", ephemeral=True)
        else:
            await interaction.followup.send(f"Using existing ticket panel channel: {channel.mention}", ephemeral=True)

        if channel and isinstance(channel, discord.TextChannel):
            embed = discord.Embed(
                title="🎫  Support Tickets",
                description=(
                    "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                    "Need help? Have a question? Want to make a purchase?\n"
                    "Our team is here for you **24/7**!\n\n"
                    "**How it works:**\n"
                    ">>> 📩 Click the button below to open a ticket\n"
                    "🔒 A private channel will be created just for you\n"
                    "💬 Describe your issue and our staff will respond\n\n"
                    "━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
                ),
                color=0x2b2d31
            )
            embed.set_thumbnail(url=interaction.guild.icon.url if interaction.guild.icon else None)
            embed.set_footer(text="Smart Store • Click below to get started")
            await channel.send(embed=embed, view=TicketView())
        else:
            await interaction.followup.send("Error: Could not verify ticket channel.", ephemeral=True)

    @app_commands.command(name="pay", description="Move this ticket to the PAY category (Staff Only)")
    async def pay(self, interaction: discord.Interaction):
        if not isinstance(interaction.channel, discord.TextChannel):
            await interaction.response.send_message("This command can only be used in a text channel.", ephemeral=True)
            return

        if not is_admin(interaction.user):
            await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)
            return

        try:
            category = interaction.guild.get_channel(PAY_CATEGORY_ID)
            if not category or not isinstance(category, discord.CategoryChannel):
                await interaction.response.send_message("PAY category not found.", ephemeral=True)
                return

            await interaction.channel.edit(category=category)
            await interaction.response.send_message(f"Ticket moved to {category.name}.")

        except Exception as e:
            await interaction.response.send_message(f"Failed to move ticket: {e}", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Tickets(bot))
