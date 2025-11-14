import os
import discord
from discord.ext import commands
from keep_alive import keep_alive  # <-- 引入

TOKEN = os.environ.get("DISCORD_TOKEN")  # 從 Render 環境變數讀取

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")

@bot.command()
async def ping(ctx):
    await ctx.send("Pong!")

# 啟動 Web server
keep_alive()

# 啟動 Discord bot
bot.run(TOKEN)
