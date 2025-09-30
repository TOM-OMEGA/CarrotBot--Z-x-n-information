import requests
from bs4 import BeautifulSoup
import os
import time
import sqlite3
from flask import Flask, Response, jsonify
from datetime import datetime
import threading
import sys

app = Flask(__name__)

PAGE_URL = "https://www.facebook.com/appledaily.tw/posts"
WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")
INTERVAL = int(os.getenv("SCRAPER_INTERVAL", 60))  # 測試先設 60 秒
DB_FILE = "posts.db"

# 初始化 SQLite
def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS posts (
            id TEXT PRIMARY KEY,
            content TEXT,
            created_at TEXT
        )
    """)
    conn.commit()
    conn.close()

def save_post(post_id, content):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO posts (id, content, created_at) VALUES (?, ?, ?)",
              (post_id, content, datetime.utcnow().isoformat()))
    conn.commit()
    conn.close()

def fetch_posts():
    headers = {"User-Agent": "Mozilla/5.0"}
    res = requests.get(PAGE_URL, headers=headers)
    print(f"🌐 抓取頁面狀態碼: {res.status_code}", flush=True)
    soup = BeautifulSoup(res.text, "html.parser")
    return soup.find_all("div", {"role": "article"})

def send_to_discord(content):
    if not WEBHOOK_URL:
        print("❌ 沒有設定 DISCORD_WEBHOOK_URL", flush=True)
        return
    payload = {"content": content}
    r = requests.post(WEBHOOK_URL, json=payload)
    print(f"📡 Discord 回應: {r.status_code} {r.text}", flush=True)

def run_once():
    try:
        posts = fetch_posts()
        print(f"🔎 抓到 {len(posts)} 篇文章", flush=True)

        for post in posts[:5]:
            post_id = post.get("data-ft")
            print("➡️ 找到文章 ID:", post_id, flush=True)

            if not post_id:
                continue

            conn = sqlite3.connect(DB_FILE)
            c = conn.cursor()
            c.execute("SELECT 1 FROM posts WHERE id=?", (post_id,))
            exists = c.fetchone()
            conn.close()

            if not exists:
                text = post.get_text(separator="\n", strip=True)
                preview = text[:200] + "..." if len(text) > 200 else text
                print(f"📝 準備推送內容: {preview[:50]}...", flush=True)
                send_to_discord(f"📢 新貼文：\n{preview}")
                save_post(post_id, preview)
                print(f"✅ 推送新貼文 {post_id}", flush=True)
            else:
                print(f"⏭ 已存在 {post_id}", flush=True)

    except Exception as e:
        print(f"❌ run_once 發生錯誤: {e}", flush=True)

@app.route("/health", methods=["GET", "HEAD"])
def health():
    return Response("OK", status=200)

@app.route("/history", methods=["GET"])
def history():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT id, content, created_at FROM posts ORDER BY created_at DESC LIMIT 20")
    rows = c.fetchall()
    conn.close()
    return jsonify([{"id": r[0], "content": r[1], "created_at": r[2]} for r in rows])

if __name__ == "__main__":
    init_db()

    # 主線程直接跑爬蟲循環
    def loop_scraper():
        while True:
            run_once()
            print(f"⏳ 等待 {INTERVAL} 秒後再次執行...", flush=True)
            time.sleep(INTERVAL)

    threading.Thread(target=loop_scraper, daemon=True).start()

    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
