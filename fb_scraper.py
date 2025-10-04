from playwright.sync_api import sync_playwright
import os, requests, sqlite3
from flask import Flask, Response, jsonify
from datetime import datetime

WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")
DB_FILE = "posts.db"
app = Flask(__name__)

def send_to_discord(content):
    if WEBHOOK_URL:
        requests.post(WEBHOOK_URL, json={"content": content})

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

def run_scraper():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(storage_state="fb_state.json")
        page = context.new_page()

        page.goto("https://www.facebook.com/LARPtimes")
        page.wait_for_selector('div[role="article"]', timeout=10000)
        articles = page.query_selector_all('div[role="article"]')
        for a in articles[:3]:
            text = a.inner_text()
            post_id = a.get_attribute("data-ft") or str(hash(text))
            preview = text[:200] + "..." if len(text) > 200 else text
            send_to_discord(f"📢 新貼文：\n{preview}")
            save_post(post_id, preview)

@app.route("/run", methods=["GET"])
def run():
    run_scraper()
    return Response("✅ 執行完成", status=200)

@app.route("/preview", methods=["GET"])
def preview():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(storage_state="fb_state.json")
        page = context.new_page()
        page.goto("https://www.facebook.com/appledaily.tw/posts")
        html = page.content()
        return Response(html[:3000], mimetype="text/plain")

@app.route("/history", methods=["GET"])
def history():
    return jsonify(get_all_posts())

@app.route("/health", methods=["GET"])
def health():
    return Response("OK", status=200)

if __name__ == "__main__":
    init_db()
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
