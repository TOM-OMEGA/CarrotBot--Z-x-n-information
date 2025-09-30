from facebook_scraper import get_posts
import os, time, sqlite3, threading, requests
from flask import Flask, Response, jsonify
from datetime import datetime

app = Flask(__name__)

WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")
INTERVAL = int(os.getenv("SCRAPER_INTERVAL", 3600))  # 預設 1 小時
DB_FILE = "posts.db"
PAGE_NAME = "appledaily.tw"  # 粉專 ID 或名稱

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

def get_all_posts(limit=20):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT id, content, created_at FROM posts ORDER BY created_at DESC LIMIT ?", (limit,))
    rows = c.fetchall()
    conn.close()
    return [{"id": r[0], "content": r[1], "created_at": r[2]} for r in rows]

def send_to_discord(content):
    if not WEBHOOK_URL:
        print("❌ 沒有設定 DISCORD_WEBHOOK_URL", flush=True)
        return
    r = requests.post(WEBHOOK_URL, json={"content": content})
    print(f"📡 Discord 回應: {r.status_code} {r.text}", flush=True)

def run_once():
    print("🔎 開始抓取 Facebook 貼文...", flush=True)
    for post in get_posts(PAGE_NAME, pages=1, options={"parser": "html.parser"}):  # 強制用 html.parser
        post_id = str(post['post_id'])
        text = post.get("text", "")
        preview = text[:200] + "..." if len(text) > 200 else text

        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("SELECT 1 FROM posts WHERE id=?", (post_id,))
        exists = c.fetchone()
        conn.close()

        if not exists:
            send_to_discord(f"📢 新貼文：\n{preview}")
            save_post(post_id, preview)
            print(f"✅ 推送新貼文 {post_id}", flush=True)
        else:
            print(f"⏭ 已存在 {post_id}", flush=True)

@app.route("/health", methods=["GET", "HEAD"])
def health():
    return Response("OK", status=200)

@app.route("/history", methods=["GET"])
def history():
    return jsonify(get_all_posts())

if __name__ == "__main__":
    init_db()

    def loop_scraper():
        while True:
            run_once()
            print(f"⏳ 等待 {INTERVAL} 秒後再次執行...", flush=True)
            time.sleep(INTERVAL)

    threading.Thread(target=loop_scraper, daemon=True).start()
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
