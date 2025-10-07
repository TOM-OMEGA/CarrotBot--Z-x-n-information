import os
import json
import discord
from discord.ext import commands
import requests

# === 設定 ===
BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
API_BASE = os.getenv("RENDER_API_URL", "").rstrip("/")
API_KEY = os.getenv("API_KEY", None)

# 加這行在這裡！
print(f"[DEBUG] DISCORD_BOT_TOKEN exists? {bool(BOT_TOKEN)}")

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)


def post_json(path, payload):
    url = f"{API_BASE}{path}"
    headers = {"Content-Type": "application/json"}
    if API_KEY:
        headers["X-API-KEY"] = API_KEY
    r = requests.post(url, headers=headers, json=payload, timeout=15)
    return r


def get_json(path):
    url = f"{API_BASE}{path}"
    headers = {}
    if API_KEY:
        headers["X-API-KEY"] = API_KEY
    r = requests.get(url, headers=headers, timeout=15)
    return r


@bot.event
async def on_ready():
    print(f"✅ {bot.user} 上線了！")


@bot.command()
async def fbupload(ctx, *, json_text: str = None):
    """上傳 Facebook cookies JSON"""
    if not json_text:
        await ctx.send("請附上 cookies JSON 內容。")
        return
    try:
        data = json.loads(json_text)
    except Exception as e:
        await ctx.send(f"❌ JSON 格式錯誤: {e}")
        return

    await ctx.send("📤 正在上傳 cookies 到伺服器...")
    try:
        r = post_json("/upload", data)
        await ctx.send(f"伺服器回應：{r.status_code} → {r.text[:400]}")
    except Exception as e:
        await ctx.send(f"❌ 上傳失敗: {e}")


@bot.command()
async def fbrun(ctx):
    """啟動爬蟲"""
    await ctx.send("🚀 正在觸發爬蟲...")
    try:
        r = get_json("/run")
        await ctx.send(f"伺服器回應：{r.status_code} → {r.text[:400]}")
    except Exception as e:
        await ctx.send(f"❌ 錯誤：{e}")


@bot.command()
async def fbstatus(ctx):
    """查詢爬蟲狀態"""
    await ctx.send("📡 正在查詢爬蟲狀態...")

if __name__ == "__main__":
    if not BOT_TOKEN:
        print("❌ ERROR: DISCORD_BOT_TOKEN 未設定，請到 Render Environment Variables 新增。")
    else:
        print("🚀 啟動 Discord Bot...")
        bot.run(BOT_TOKEN)

