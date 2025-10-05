import discord
import requests
import os
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("DISCORD_BOT_TOKEN")
API_URL = os.getenv("SCRAPER_API_URL")

intents = discord.Intents.default()
client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f"✅ Bot 已啟動：{client.user}")

@client.event
async def on_message(message):
    if message.author.bot:
        return

    if message.content == "/fbrefresh":
        await message.channel.send("🔄 正在更新 Facebook 登入狀態...")
        try:
            r = requests.get(f"{API_URL}/refresh-login", timeout=30)
            await message.channel.send(r.text)
        except Exception as e:
            await message.channel.send(f"⚠️ 錯誤：{str(e)}")

    elif message.content == "/fbstatus":
        await message.channel.send("📡 正在查詢爬蟲狀態...")
        try:
            r = requests.get(f"{API_URL}/status", timeout=15)
            data = r.json()
            if "error" in data:
                await message.channel.send(f"❌ 錯誤：{data['error']}")
            else:
                msg = (
                    f"🗂 fb_state.json：{data['fb_state_exists']}\n"
                    f"🔐 FB_EMAIL：{data['env_FB_EMAIL']}\n"
                    f"🔐 FB_PASSWORD：{data['env_FB_PASSWORD']}\n"
                    f"📣 Webhook：{data['env_DISCORD_WEBHOOK_URL']}\n"
                    f"📝 最近貼文：\n" +
                    "\n".join([f"- {p['created_at'][:19]} → {p['content'][:50]}" for p in data["recent_posts"]])
                )
                await message.channel.send(msg)
        except Exception as e:
            await message.channel.send(f"⚠️ 錯誤：{str(e)}")

    elif message.content == "/fbrun":
        await message.channel.send("🚀 正在執行爬蟲...")
        try:
            r = requests.get(f"{API_URL}/run", timeout=60)
            await message.channel.send(r.text)
        except Exception as e:
            await message.channel.send(f"⚠️ 錯誤：{str(e)}")

client.run(TOKEN)
