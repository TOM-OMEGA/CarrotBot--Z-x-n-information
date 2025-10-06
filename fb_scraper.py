import os
import sqlite3
import json
from flask import Flask, jsonify, request
from playwright.sync_api import sync_playwright
import threading

app = Flask(__name__)
DB_PATH = "fb_posts.db"


# ----------------------- 資料庫 -----------------------
def ensure_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            content TEXT,
            image TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()


def save_post(content, image=None):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO posts (content, image) VALUES (?, ?)", (content, image))
    conn.commit()
    conn.close()


# ----------------------- 爬蟲邏輯 -----------------------
def scrape_facebook():
    app.logger.info("🚀 開始執行爬蟲...")
    ensure_db()

    if not os.path.exists("fb_state.json"):
        app.logger.error("❌ 缺少 fb_state.json，請先上傳或設定 FB_STATE_JSON")
        return "缺少 fb_state.json"

    try:
        with sync_playwright() as p:
            # 偵測環境
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

            # 滾動頁面載入更多貼文
            for i in range(3):
                page.evaluate("window.scrollBy(0, document.body.scrollHeight)")
                app.logger.info(f"🔽 滾動載入第 {i + 1} 次 ...")
                page.wait_for_timeout(5000)

            # 展開「顯示更多」
            try:
                buttons = page.query_selector_all('div[role="button"]:has-text("顯示更多")')
                for b in buttons:
                    b.click()
                    page.wait_for_timeout(1000)
                app.logger.info(f"🔓 展開所有貼文文字，共 {len(buttons)} 項")
            except Exception as e:
                app.logger.warning(f"⚠️ 展開貼文時發生例外：{e}")

            # 擷取貼文
            posts = []
            articles = page.query_selector_all('div[role="article"]')
            app.logger.info(f"📰 找到可能的貼文區塊：{len(articles)}")

            for post in articles:
                try:
                    # 文字
                    text_el = post.query_selector('div[data-ad-preview="message"], div[data-testid="post_message"], span[dir="auto"]')
                    text = text_el.inner_text().strip() if text_el else ""

                    # 圖片
                    img_el = post.query_selector('img[src*="scontent"]')
                    img_url = img_el.get_attribute("src") if img_el else None

                    if text or img_url:
                        save_post(text, img_url)
                        posts.append({"text": text, "image": img_url})
                except Exception as e:
                    app.logger.warning(f"⚠️ 處理單一貼文時發生例外：{e}")

            browser.close()
            app.logger.info(f"✅ 共擷取到 {len(posts)} 則貼文。")
            return f"共擷取到 {len(posts)} 則貼文。"

    except Exception as e:
        app.logger.error(f"❌ 爬蟲執行錯誤：{e}")
        return str(e)


# ----------------------- API -----------------------
@app.route("/upload", methods=["POST"])
def upload_cookie():
    try:
        if "application/json" in str(request.content_type):
            data = request.get_json()
        else:
            data = json.loads(request.data.decode("utf-8"))

        with open("fb_state.json", "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        app.logger.info("✅ Cookie 已成功更新並儲存為 fb_state.json")
        return jsonify({"message": "✅ Cookie 已更新"}), 200

    except Exception as e:
        app.logger.error(f"❌ 上傳 cookie 時發生錯誤：{e}")
        return jsonify({"error": str(e)}), 500


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
    c.execute("SELECT content, image, timestamp FROM posts ORDER BY id DESC LIMIT 3")
    rows = c.fetchall()
    conn.close()
    posts = [{"content": r[0], "image": r[1], "timestamp": r[2]} for r in rows]
    return jsonify({
        "fb_state.json": os.path.exists("fb_state.json"),
        "posts_count": len(posts),
        "recent_posts": posts
    })


# ----------------------- 啟動 Flask -----------------------
def run_flask():
    port = int(os.getenv("PORT", 10000))
    app.run(host="0.0.0.0", port=port)


if __name__ == "__main__":
    run_flask()
