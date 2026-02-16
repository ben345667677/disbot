import discord
import os
import asyncio
from discord.ext import commands
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get token
TOKEN = os.getenv('DISCORD_TOKEN')

# Setup intents
intents = discord.Intents.default()
intents.members = True
intents.message_content = True

# Setup bot
bot = commands.Bot(command_prefix='!', intents=intents)

# Load cogs
async def load_extensions():
    for filename in os.listdir('./cogs'):
        if filename.endswith('.py') and filename != '__init__.py':
            await bot.load_extension(f'cogs.{filename[:-3]}')
            print(f'Loaded extension: {filename[:-3]}')

@bot.event
async def on_ready():
    print(f'{bot.user.name} has connected to Discord!')
    print(f'ID: {bot.user.id}')
    await bot.tree.sync() # Sync slash commands

async def main():
    async with bot:
        await load_extensions()
        if not TOKEN:
            print("Error: DISCORD_TOKEN not found in .env")
            return
        await bot.start(TOKEN)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        # Handle Ctrl+C
        pass
