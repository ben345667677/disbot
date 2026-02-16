import discord
from discord.ext import commands
from aiohttp import web
import aiohttp
import os
import sqlite3
import json

class OAuth(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.client_id = None # Set in on_ready
        self.client_secret = os.getenv('CLIENT_SECRET')
        self.redirect_uri = os.getenv('REDIRECT_URI') # e.g., http://localhost:8080/callback
        self.conn = sqlite3.connect('data/users.db')
        self.cursor = self.conn.cursor()
        self.create_table()
        
        # Web server settings
        self.app = web.Application()
        self.app.router.add_get('/login', self.login)
        self.app.router.add_get('/callback', self.callback)
        self.runner = None
        self.site = None

    def create_table(self):
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id TEXT PRIMARY KEY,
                access_token TEXT,
                refresh_token TEXT
            )
        ''')
        self.conn.commit()

    async def start_server(self):
        self.runner = web.AppRunner(self.app)
        await self.runner.setup()
        self.site = web.TCPSite(self.runner, '0.0.0.0', 8080)
        await self.site.start()
        print("OAuth web server started on port 8080")

    @commands.Cog.listener()
    async def on_ready(self):
        self.client_id = self.bot.user.id
        await self.start_server()

    async def login(self, request):
        if not self.client_id or not self.redirect_uri:
            return web.Response(text="Bot not ready or configuration missing.")
        
        # Scopes: identify, email, guilds, guilds.join
        scope = "identify email guilds guilds.join"
        discord_login_url = (
            f"https://discord.com/api/oauth2/authorize?client_id={self.client_id}"
            f"&redirect_uri={self.redirect_uri}&response_type=code&scope={scope}"
        )
        return web.HTTPFound(discord_login_url)

    async def callback(self, request):
        code = request.query.get('code')
        if not code:
            return web.Response(text="Error: No code provided.")

        # Exchange code for token
        data = {
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'grant_type': 'authorization_code',
            'code': code,
            'redirect_uri': self.redirect_uri
        }
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }

        async with aiohttp.ClientSession() as session:
            async with session.post('https://discord.com/api/oauth2/token', data=data, headers=headers) as resp:
                if resp.status != 200:
                    return web.Response(text=f"Error exchanging token: {await resp.text()}")
                token_data = await resp.json()

            access_token = token_data['access_token']
            refresh_token = token_data['refresh_token']
            
            # Get User Info
            headers = {'Authorization': f"Bearer {access_token}"}
            async with session.get('https://discord.com/api/users/@me', headers=headers) as resp:
                user_data = await resp.json()
                user_id = user_data['id']

        # Store in DB
        self.cursor.execute('''
            INSERT OR REPLACE INTO users (user_id, access_token, refresh_token)
            VALUES (?, ?, ?)
        ''', (user_id, access_token, refresh_token))
        self.conn.commit()

        # Add "Verified" role to user in the guild
        # Assuming the bot is in the guild and we want to add them to the guild where verification started
        # For simplicity, we'll try to add them to ALL guilds the bot is in, or ideally, we just verify them.
        
        # BETTER LOGIC:
        # Since this is a "Restore" bot, we usually want to add them to the guild where the invite came from.
        # But for now, we will find the user in the cache and give them the role.
        
        assigned = False
        guild_id_redirect = None
        
        for guild in self.bot.guilds:
            member = guild.get_member(int(user_id))
            if member:
                role = discord.utils.get(guild.roles, name="Verified")
                if role:
                    try:
                        await member.add_roles(role)
                        assigned = True
                        guild_id_redirect = guild.id
                    except Exception as e:
                        print(f"Failed to assign role in {guild.name}: {e}")
            else:
                 # If using guilds.join, we could add them here if we knew the guild ID.
                 # For now, we assume they are in the server clicking the link.
                 pass

        if assigned and guild_id_redirect:
             return web.HTTPFound(f"https://discord.com/channels/{guild_id_redirect}")
        else:
             return web.Response(text="Verification successful! You can close this tab and return to Discord.")

    def cog_unload(self):
        self.conn.close()

async def setup(bot):
    await bot.add_cog(OAuth(bot))
