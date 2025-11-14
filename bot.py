import os
import discord
from discord.ext import commands
from flask import Flask
from threading import Thread
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

# ---------------- Discord Bot ----------------
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")

@bot.command()
async def ping(ctx):
    await ctx.send("Pong!")

# ---------------- Web Server ----------------
# 用來 Render 免費 Web Service 保活
app = Flask("")

@app.route("/")
def home():
    return "Bot is running!"

def run():
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

# Run Web Server in background thread
Thread(target=run).start()

# Run Discord bot
bot.run(TOKEN)
