import os
import sqlite3
import json
from flask import Flask, jsonify
from playwright.sync_api import sync_playwright
import threading
import time

app = Flask(__name__)

DB_PATH = "fb_posts.db"

def ensure_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            content TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

def save_post(content):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO posts (content) VALUES (?)", (content,))
    conn.commit()
    conn.close()

def scrape_facebook():
    app.logger.info("🚀 開始執行爬蟲...")
    ensure_db()

    if not os.path.exists("fb_state.json"):
        app.logger.error("❌ 缺少 fb_state.json，請先上傳或設定 FB_STATE_JSON")
        return "缺少 fb_state.json"

    try:
        with sync_playwright() as p:
            # 自動偵測環境
            is_render = os.getenv("RENDER", "0") == "1"
            mode = "🌐 Render（headless 模式）" if is_render else "🖥️ 本機（可視化模式）"
            app.logger.info(f"⚙️ 偵測到執行環境：{mode}")

            browser = p.chromium.launch(
                headless=is_render,
                args=[
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                    "--disable-gpu",
                    "--disable-dev-shm-usage",
                    "--disable-software-rasterizer",
                    "--single-process",
                    "--no-zygote"
                ]
            )

            context = browser.new_context(
                storage_state="fb_state.json",
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                           "AppleWebKit/537.36 (KHTML, like Gecko) "
                           "Chrome/121.0 Safari/537.36",
                viewport={"width": 1280, "height": 800}
            )

            page = context.new_page()
            target_url = os.getenv("FB_PAGE_URL", "https://www.facebook.com/appledaily.tw/posts")
            app.logger.info(f"🌍 正在載入粉專頁面：{target_url}")

            page.goto(target_url, timeout=120000)
            page.wait_for_load_state("networkidle", timeout=60000)

            # 自動滾動觸發 lazy load
            for i in range(3):
                page.evaluate("window.scrollBy(0, document.body.scrollHeight)")
                app.logger.info(f"🔽 滾動載入第 {i+1} 次 ...")
                page.wait_for_timeout(5000)

            # 擴展貼文文字
            try:
                buttons = page.query_selector_all('div[role="button"]:has-text("顯示更多")')
                for b in buttons:
                    b.click()
                    page.wait_for_timeout(1000)
                app.logger.info(f"🔓 展開所有貼文文字，共 {len(buttons)} 項")
            except Exception as e:
                app.logger.warning(f"⚠️ 展開貼文時發生例外：{e}")

            selectors = [
                'div[data-ad-preview="message"]',
                'div[data-testid="post_message"]',
                'span[dir="auto"]'
            ]
            posts = []
            for selector in selectors:
                elements = page.query_selector_all(selector)
                for e in elements:
                    text = e.inner_text().strip()
                    if len(text) > 20 and text not in posts:
                        posts.append(text)
                        save_post(text)

            app.logger.info(f"✅ 共擷取到 {len(posts)} 則貼文。")
            browser.close()
            return f"共擷取到 {len(posts)} 則貼文。"

    except Exception as e:
        app.logger.error(f"❌ 爬蟲執行錯誤：{e}")
        return str(e)

@app.route("/run", methods=["GET"])
def run_scraper_api():
    thread = threading.Thread(target=scrape_facebook)
    thread.start()
    return jsonify({"status": "ok", "message": "爬蟲已在背景啟動"}), 200

@app.route("/status", methods=["GET"])
def status():
    ensure_db()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT content, timestamp FROM posts ORDER BY id DESC LIMIT 3")
    rows = c.fetchall()
    conn.close()
    posts = [{"content": r[0], "timestamp": r[1]} for r in rows]
    return jsonify({
        "fb_state.json": os.path.exists("fb_state.json"),
        "posts_count": len(posts),
        "recent_posts": posts
    })

def run_flask():
    port = int(os.getenv("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

if __name__ == "__main__":
    run_flask()
