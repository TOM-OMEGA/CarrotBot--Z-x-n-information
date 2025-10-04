import requests, os, time, sqlite3, threading, json
from bs4 import BeautifulSoup
from flask import Flask, Response, jsonify
from datetime import datetime

app = Flask(__name__)

WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")
INTERVAL = int(os.getenv("SCRAPER_INTERVAL", 3600))
DB_FILE = "posts.db"
PAGE_URL = "https://www.facebook.com/appledaily.tw"

# 讀取整組 Cookie（JSON 格式）
try:
    COOKIES = json.loads(os.getenv("FB_COOKIES", "{}"))
except Exception as e:
    print(f"❌ Cookie 解析失敗: {e}")
    COOKIES = {}

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

def fetch_posts():
    headers = {"User-Agent": "Mozilla/5.0"}
    res = requests.get(PAGE_URL, headers=headers, cookies=COOKIES)
    print(f"🌐 抓取頁面狀態碼: {res.status_code}", flush=True)
    soup = BeautifulSoup(res.text, "html.parser")
    return soup.find_all("div", {"role": "article"})

def run_once():
    posts = fetch_posts()
    print(f"🔎 抓到 {len(posts)} 篇文章", flush=True)

    if len(posts) == 0:
        send_to_discord("⚠️ 測試訊息：目前抓不到文章，Webhook 正常")
        return

    for post in posts[:5]:
        post_id = post.get("data-ft")
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
            send_to_discord(f"📢 新貼文：\n{preview}")
            save_post(post_id, preview)
            print(f"✅ 推送新貼文 {post_id}", flush=True)
        else:
            print(f"⏭ 已存在 {post_id}", flush=True)

@app.route("/health", methods=["GET", "HEAD"])
def health():
    return Response("OK", status=200)

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

@app.route("/preview", methods=["GET"])
def preview():
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        res = requests.get(PAGE_URL, headers=headers, cookies=COOKIES)
        html = res.text
        return Response(html[:3000], mimetype="text/plain")
    except Exception as e:
        return jsonify({"error": str(e)})

@app.route("/history", methods=["GET"])
def history():
    return jsonify(get_all_posts())

if __name__ == "__main__":
    init_db()
    send_to_discord("🚀 Bot 已啟動，Webhook 正常！")

    def loop_scraper():
        while True:
            run_once()
            print(f"⏳ 等待 {INTERVAL} 秒後再次執行...", flush=True)
            time.sleep(INTERVAL)

    threading.Thread(target=loop_scraper, daemon=True).start()
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
