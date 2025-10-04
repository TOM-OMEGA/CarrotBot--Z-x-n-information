import requests, os, time, sqlite3, threading, json
from bs4 import BeautifulSoup
from flask import Flask, Response, jsonify
from datetime import datetime

app = Flask(__name__)

WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")
INTERVAL = int(os.getenv("SCRAPER_INTERVAL", 3600))
DB_FILE = "posts.db"
PAGE_URL = "https://www.facebook.com/appledaily.tw/posts"

# 從環境變數讀取整組 cookie（JSON 格式）
try:
    COOKIES = json.loads(os.getenv("FB_COOKIES", "{}"))
except Exception as e:
    print(f"❌ Cookie 解析失敗: {e}")
    COOKIES = {}

def fetch_posts():
    headers = {"User-Agent": "Mozilla/5.0"}
    res = requests.get(PAGE_URL, headers=headers, cookies=COOKIES)
    print(f"🌐 抓取頁面狀態碼: {res.status_code}", flush=True)
    soup = BeautifulSoup(res.text, "html.parser")
    return soup.find_all("div", {"role": "article"})

@app.route("/test", methods=["GET"])
def test():
    posts = fetch_posts()
    if len(posts) == 0:
        send_to_discord("🧪 測試結果：Cookie 可能失效，抓不到文章")
        return jsonify({"status": "fail", "message": "抓不到文章，請檢查 Cookie"})
    else:
        preview = posts[0].get_text(separator="\n", strip=True)[:200]
        send_to_discord(f"🧪 測試結果：成功抓到文章\n{preview}")
        return jsonify({"status": "ok", "message": "成功抓到文章", "preview": preview})

def send_to_discord(content):
    if not WEBHOOK_URL:
        print("❌ 沒有設定 DISCORD_WEBHOOK_URL", flush=True)
        return
    r = requests.post(WEBHOOK_URL, json={"content": content})
    print(f"📡 Discord 回應: {r.status_code} {r.text}", flush=True)

@app.route("/health", methods=["GET", "HEAD"])
def health():
    return Response("OK", status=200)

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
