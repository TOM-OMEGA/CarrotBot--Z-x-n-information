import os
import json
import threading
import asyncio
import time
import requests
import discord
from discord.ext import commands
from flask import Flask

# =========================================================
# ⚙️ 基本設定
# =========================================================
BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
SCRAPER_URL = os.getenv("SCRAPER_URL", "").rstrip("/")
RENDER_API_KEY = os.getenv("RENDER_API_KEY")
SELF_URL = os.getenv("SELF_URL", "").rstrip("/")  # ✅ 新增自己的 Bot Render URL

print("===== BOT 啟動前環境檢查 =====")
print(f"[DEBUG] Discord Bot Token exists? {bool(BOT_TOKEN)}")
print(f"[DEBUG] Scraper URL: {SCRAPER_URL or '(未設定)'}")
print(f"[DEBUG] API Key set? {bool(RENDER_API_KEY)}")
print(f"[DEBUG] Bot Self URL: {SELF_URL or '(未設定)'}")
print("=====================================")

# --- URL 驗證 ---
if SCRAPER_URL and not SCRAPER_URL.startswith("http"):
    print("⚠️ SCRAPER_URL 格式錯誤！請加上 'https://' 或 'http://'")
    SCRAPER_URL = None
if SELF_URL and not SELF_URL.startswith("http"):
    print("⚠️ SELF_URL 格式錯誤！請加上 'https://' 或 'http://'")
    SELF_URL = None

# --- Discord intents ---
intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# =========================================================
# 📡 HTTP 請求（含重試與授權）
# =========================================================
def request_with_retry(method, path, **kwargs):
    if not SCRAPER_URL:
        raise ValueError("SCRAPER_URL 未設定或格式錯誤（需以 http/https 開頭）")

    url = f"{SCRAPER_URL}{path}"
    headers = {"Authorization": f"Bearer {RENDER_API_KEY}"}
    if "json" in kwargs:
        headers["Content-Type"] = "application/json"

    retries = 3
    for i in range(retries):
        try:
            print(f"[HTTP] {method.upper()} {url} (嘗試 {i+1}/{retries})")
            if method == "get":
                return requests.get(url, headers=headers, timeout=60)
            elif method == "post":
                return requests.post(url, headers=headers, **kwargs, timeout=60)
        except requests.exceptions.ReadTimeout:
            print("⚠️ 請求逾時，5 秒後重試...")
            time.sleep(5)
        except Exception as e:
            print(f"❌ 第 {i+1} 次請求失敗：{e}")
            time.sleep(5)
    return type("Resp", (), {"status_code": 504, "text": "⚠️ 無法連線至爬蟲伺服器（連續逾時）"})()

# =========================================================
# 🧩 自動 Keep-Alive 背景執行緒
# =========================================================
def keep_both_awake():
    """每 10 分鐘同時 ping Scraper + 自己，保持 Render 不睡覺"""
    while True:
        try:
            if SCRAPER_URL:
                r = request_with_retry("get", "/status")
                print(f"💤 Scraper Keep-alive：{r.status_code}")
            if SELF_URL:
                s = requests.get(SELF_URL, timeout=30)
                print(f"🌐 Bot Self Keep-alive：{s.status_code}")
        except Exception as e:
            print(f"⚠️ Keep-alive 執行錯誤：{e}")
        time.sleep(600)  # 每 10 分鐘執行一次

def start_keep_alive_thread():
    t = threading.Thread(target=keep_both_awake, daemon=True)
    t.start()
    print("🌙 已啟動 Scraper + Bot 雙向 Keep-alive 背景任務")

# =========================================================
# 🤖 Discord Bot 指令
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
        r = request_with_retry("post", "/upload", json=data)
        await ctx.send(f"📡 回應：{r.status_code} → {r.text[:400]}")
    except Exception as e:
        await ctx.send(f"❌ 上傳失敗：{e}")

@bot.command()
async def fbrun(ctx):
    """啟動爬蟲（含自動查詢狀態與重試）"""
    await ctx.send("🚀 正在觸發爬蟲...")
    try:
        r = request_with_retry("get", "/run")
        await ctx.send(f"📡 初始回應：{r.status_code} → {r.text[:400]}")

        if r.status_code == 200:
            await ctx.send("⌛ 等待 30 秒後自動查詢爬蟲狀態（最多重試 3 次）...")
            for i in range(3):
                await asyncio.sleep(30)
                s = request_with_retry("get", "/status")
                await ctx.send(f"📊 第 {i+1} 次查詢 → {s.status_code}：{s.text[:400]}")
                if '"posts_count":' in s.text and '"posts_count":0' not in s.text:
                    await ctx.send("✅ 爬蟲似乎有抓到資料，停止重試！")
                    break

    except ValueError as ve:
        await ctx.send(f"⚠️ 設定錯誤：{ve}")
    except Exception as e:
        await ctx.send(f"❌ 無法連線到爬蟲伺服器：{e}")

@bot.command()
async def fbstatus(ctx):
    """查詢爬蟲狀態"""
    await ctx.send("📡 查詢爬蟲狀態中...")
    try:
        r = request_with_retry("get", "/status")
        await ctx.send(f"伺服器回應：{r.status_code} → {r.text[:400]}")
    except Exception as e:
        await ctx.send(f"❌ 查詢失敗：{e}")

# =========================================================
# ☕ Flask Keep-Alive Web
# =========================================================
web_app = Flask("keep_alive")

@web_app.route("/")
def home():
    return "✅ Discord Bot is active and awake!", 200

def run_web():
    port = int(os.getenv("PORT", 10000))
    print(f"🌐 Keep-alive Flask running on port {port}")
    web_app.run(host="0.0.0.0", port=port)

# =========================================================
# 🚀 主程式
# =========================================================
if __name__ == "__main__":
    if not BOT_TOKEN:
        print("❌ 錯誤：DISCORD_BOT_TOKEN 未設定")
        exit(1)

    if not SCRAPER_URL or not RENDER_API_KEY:
        print("⚠️ 警告：SCRAPER_URL 或 RENDER_API_KEY 未設定，Bot 將無法連線爬蟲伺服器。")

    # 啟動 Flask（防止 Render 判定休眠）
    threading.Thread(target=run_web, daemon=True).start()

    # 啟動 Keep-alive（Scraper + 自己）
    start_keep_alive_thread()

    # 啟動 Discord Bot
    print("🚀 啟動 Discord Bot...")
    bot.run(BOT_TOKEN)
