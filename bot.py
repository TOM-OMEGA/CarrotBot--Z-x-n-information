import disnake
from disnake.ext import commands
import os
from dotenv import load_dotenv
from keepalive import keep_alive

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")

# 禁用 VOICE，避免 audioop
intents = disnake.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"Bot is online as {bot.user}")

@bot.command()
async def ping(ctx):
    await ctx.send("Pong!")

# Render 保活
keep_alive()

bot.run(TOKEN)
