import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
from keepalive import keep_alive

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"Bot is online as {bot.user}")

@bot.command()
async def ping(ctx):
    await ctx.send("Pong!")

# 重要：啟動 Flask 保活
keep_alive()

# 啟動 BOT
bot.run(TOKEN)
