import discord
from discord.ext import commands
import os
import openai

class AIChat(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.api_key = os.getenv('OPENROUTER_API_KEY')
        self.client = None
        if self.api_key:
            self.client = openai.AsyncOpenAI(
                base_url="https://openrouter.ai/api/v1",
                api_key=self.api_key,
            )
        else:
            print("Warning: OPENROUTER_API_KEY not found. AI Chat will not work.")

    @commands.Cog.listener()
    async def on_ready(self):
        for guild in self.bot.guilds:
            channel_exists = False
            for channel in guild.text_channels:
                if channel.name in ['ai-chat', 'ai-room']:
                    channel_exists = True
                    break
            
            if not channel_exists:
                try:
                    await guild.create_text_channel("ai-chat")
                    print(f"Created 'ai-chat' channel in {guild.name}")
                except Exception as e:
                    print(f"Failed to create 'ai-chat' channel in {guild.name}: {e}")

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return
            
        # Check if channel is 'ai-chat' or 'ai-room'
        if message.channel.name not in ['ai-chat', 'ai-room']:
            return

        if not self.client:
             await message.channel.send("AI Chat is not configured (Missing API Key).")
             return

        async with message.channel.typing():
            try:
                completion = await self.client.chat.completions.create(
                    extra_headers={
                        "HTTP-Referer": "https://discord.com", # Required by OpenRouter
                        "X-Title": "Discord Bot", # Required by OpenRouter
                    },
                    model="stepfun/step-3.5-flash:free",
                    messages=[
                        {
                            "role": "user",
                            "content": message.content,
                        },
                    ],
                )
                reply_text = completion.choices[0].message.content
                
                # Split if too long (Discord limit 2000)
                if len(reply_text) > 2000:
                    for i in range(0, len(reply_text), 2000):
                        await message.reply(reply_text[i:i+2000])
                else:
                    await message.reply(reply_text)
            except Exception as e:
                await message.reply(f"I encountered an error: {e}")

async def setup(bot):
    await bot.add_cog(AIChat(bot))
