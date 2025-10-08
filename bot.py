import os
import json
import discord
from discord.ext import commands
import requests
import threading
from flask import Flask

# =========================================================
# ⚙️ 設定
# =========================================================
BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
API_BASE = os.getenv("RAILWAY_API_URL", "").rstrip("/")
API_KEY = os.getenv("RENDER_API_KEY")  # ✅ 改成與 Scraper 同名變數

print(f"[DEBUG] DISCORD_BOT_TOKEN exists? {bool(BOT_TOKEN)}")
print(f"[DEBUG] RAILWAY_API_URL: {API_BASE}")
print(f"[DEBUG] API_KEY exists? {bool(API_KEY)}")

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)


# =========================================================
# 📡 API 請求功能
# =========================================================
def make_headers():
    headers = {"Content-Type": "application/json"}
    if API_KEY:
        headers["Authorization"] = f"Bearer {API_KEY}"
    return headers


def post_json(path, payload):
    url = f"{API_BASE}{path}"
    return requests.post(url, headers=make_headers(), json=payload, timeout=15)


def get_json(path):
    url = f"{API_BASE}{path}"
    return requests.get(url, headers=make_headers(), timeout=15)


# =========================================================
# 🤖 Discord Bot 指令
# =========================================================
@bot.event
async def on_ready():
    print(f"✅ {bot.user} 上線了！")


@bot.command()
async def fbupload(ctx, *, json_text: str = None):
    """上傳 Facebook cookies JSON（支援檔案或文字）"""
    data = None

    # --- 若有附加檔案 ---
    if ctx.message.attachments:
        file = ctx.message.attachments[0]
        if not file.filename.endswith(".json"):
            await ctx.send("❌ 請上傳 JSON 檔案（例如 fb_state.json）")
            return
        await ctx.send(f"📂 偵測到檔案：{file.filename}，正在讀取中...")
        content = await file.read()
        try:
            data = json.loads(content.decode("utf-8"))
        except Exception as e:
            await ctx.send(f"❌ JSON 解析錯誤：{e}")
            return

    # --- 若使用文字輸入 ---
    elif json_text:
        try:
            data = json.loads(json_text)
        except Exception as e:
            await ctx.send(f"❌ JSON 格式錯誤: {e}")
            return

    # --- 沒資料時 ---
    else:
        await ctx.send("請附上 cookies JSON 檔案或貼上 JSON 內容。")
        return

    # --- 上傳至爬蟲伺服器 ---
    await ctx.send("📤 正在上傳 cookies 到爬蟲伺服器...")
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
    try:
        r = get_json("/status")
        await ctx.send(f"伺服器回應：{r.status_code} → {r.text[:400]}")
    except Exception as e:
        await ctx.send(f"❌ 查詢失敗: {e}")


# =========================================================
# 🧱 Render 偵測用 Flask Web Server
# =========================================================
web_app = Flask("keep_alive")


@web_app.route("/")
def home():
    return "✅ Discord bot is running!", 200


def run_web():
    port = int(os.getenv("PORT", 10000))
    print(f"🌐 Render Flask server running on port {port}")
    web_app.run(host="0.0.0.0", port=port)


# =========================================================
# 🚀 主程式啟動
# =========================================================
if __name__ == "__main__":
    if not BOT_TOKEN:
        print("❌ ERROR: DISCORD_BOT_TOKEN 未設定，請到 Render Environment Variables 新增。")
    else:
        # 啟動 Flask 以通過 Render Web Service 檢測
        threading.Thread(target=run_web, daemon=True).start()

        # 啟動 Discord Bot
        print("🚀 啟動 Discord Bot...")
        bot.run(BOT_TOKEN)
