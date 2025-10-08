import os
import json
import threading
import requests
import discord
from discord.ext import commands
from flask import Flask

# =========================================================
# ⚙️ 基本設定
# =========================================================
BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
SCRAPER_URL = os.getenv("SCRAPER_URL", "").rstrip("/")  # 例：https://your-scraper.onrender.com
RENDER_API_KEY = os.getenv("RENDER_API_KEY")

print(f"[DEBUG] Discord Bot Token exists? {bool(BOT_TOKEN)}")
print(f"[DEBUG] Scraper URL: {SCRAPER_URL}")
print(f"[DEBUG] API Key set? {bool(RENDER_API_KEY)}")

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# =========================================================
# 📡 通用 HTTP 請求封裝（含授權）
# =========================================================
def post_json(path, payload):
    url = f"{SCRAPER_URL}{path}"
    headers = {"Authorization": f"Bearer {RENDER_API_KEY}", "Content-Type": "application/json"}
    return requests.post(url, json=payload, headers=headers, timeout=20)

def get_json(path):
    url = f"{SCRAPER_URL}{path}"
    headers = {"Authorization": f"Bearer {RENDER_API_KEY}"}
    return requests.get(url, headers=headers, timeout=20)

# =========================================================
# 🤖 Discord Bot 事件與指令
# =========================================================
@bot.event
async def on_ready():
    print(f"✅ {bot.user} 已上線，準備接收指令！")

@bot.command()
async def fbupload(ctx):
    """上傳 Facebook Cookie JSON"""
    if not ctx.message.attachments:
        await ctx.send("❌ 請附上 fb_state.json 檔案")
        return

    file = ctx.message.attachments[0]
    if not file.filename.endswith(".json"):
        await ctx.send("⚠️ 檔案必須是 .json 格式")
        return

    await ctx.send(f"📂 偵測到檔案：{file.filename}，正在上傳中...")
    content = await file.read()

    try:
        data = json.loads(content.decode("utf-8"))
    except Exception as e:
        await ctx.send(f"❌ JSON 格式錯誤：{e}")
        return

    try:
        r = post_json("/upload", data)
        await ctx.send(f"📡 回應：{r.status_code} → {r.text[:400]}")
    except Exception as e:
        await ctx.send(f"❌ 上傳失敗：{e}")

@bot.command()
async def fbrun(ctx):
    """啟動爬蟲"""
    await ctx.send("🚀 正在觸發爬蟲...")
    try:
        r = get_json("/run")
        await ctx.send(f"📡 回應：{r.status_code} → {r.text[:400]}")
    except Exception as e:
        await ctx.send(f"❌ 無法連線到爬蟲伺服器：{e}")

@bot.command()
async def fbstatus(ctx):
    """查詢爬蟲狀態"""
    await ctx.send("📡 查詢爬蟲狀態中...")
    try:
        r = get_json("/status")
        await ctx.send(f"伺服器回應：{r.status_code} → {r.text[:400]}")
    except Exception as e:
        await ctx.send(f"❌ 查詢失敗：{e}")

# =========================================================
# ☕ 防 Render 睡眠的小型 Flask Web 伺服器
# =========================================================
web_app = Flask("keep_alive")

@web_app.route("/")
def home():
    return "✅ Discord Bot is active!", 200

def run_web():
    port = int(os.getenv("PORT", 10000))
    print(f"🌐 Keep-alive Flask running on port {port}")
    web_app.run(host="0.0.0.0", port=port)

# =========================================================
# 🚀 啟動主程式
# =========================================================
if __name__ == "__main__":
    if not BOT_TOKEN:
        print("❌ 錯誤：DISCORD_BOT_TOKEN 未設定")
        exit(1)

    if not SCRAPER_URL or not RENDER_API_KEY:
        print("⚠️ 警告：SCRAPER_URL 或 RENDER_API_KEY 未設定，無法安全連線爬蟲。")

    # 啟動 Flask（防止 Render 判定休眠）
    threading.Thread(target=run_web, daemon=True).start()

    # 啟動 Discord Bot
    print("🚀 啟動 Discord Bot...")
    bot.run(BOT_TOKEN)
