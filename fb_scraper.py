from playwright.sync_api import sync_playwright
import os, requests, sqlite3
from flask import Flask, Response, jsonify, request
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
    selectors = [
        'div[data-testid="post_message"]',
        'div[data-ad-preview="message"]',
        'div[data-pagelet^="FeedUnit_"]',
        'div[role="article"]'
    ]
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(storage_state="fb_state.json")
        page = context.new_page()
        page.goto("https://www.facebook.com/appledaily.tw/posts")
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(5000)

        for selector in selectors:
            try:
                page.wait_for_selector(selector, timeout=8000)
                articles = page.query_selector_all(selector)
                if articles:
                    print(f"✅ 使用 selector：{selector}，找到 {len(articles)} 篇貼文")
                    for a in articles[:3]:
                        text = a.inner_text()
                        post_id = a.get_attribute("data-ft") or str(hash(text))
                        preview = text[:200] + "..." if len(text) > 200 else text
                        send_to_discord(f"📢 新貼文：\n{preview}")
                        save_post(post_id, preview)
                    return
            except:
                print(f"⚠️ selector 超時或無結果：{selector}")
        print("❌ 所有 selector 都失敗，未找到貼文")

@app.route("/run")
def run():
    try:
        run_scraper()
        return Response("✅ 執行完成", status=200)
    except Exception as e:
        return Response(f"❌ 執行錯誤：{str(e)}", status=500)

@app.route("/preview")
def preview():
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(storage_state="fb_state.json")
            page = context.new_page()
            page.goto("https://www.facebook.com/appledaily.tw/posts")
            page.wait_for_load_state("networkidle")
            page.wait_for_timeout(5000)
            html = page.content()
            return Response(html[:3000], mimetype="text/plain")
    except Exception as e:
        return Response(f"❌ 錯誤：{str(e)}", status=500)

@app.route("/history")
def history():
    return jsonify(get_all_posts())

@app.route("/debug")
def debug():
    result = {}
    try:
        result["fb_state_exists"] = os.path.exists("fb_state.json")
        result["env_FB_EMAIL"] = bool(os.getenv("FB_EMAIL"))
        result["env_FB_PASSWORD"] = bool(os.getenv("FB_PASSWORD"))
        result["env_DISCORD_WEBHOOK_URL"] = bool(os.getenv("DISCORD_WEBHOOK_URL"))
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(storage_state="fb_state.json")
            page = context.new_page()
            page.goto("https://www.facebook.com/appledaily.tw/posts")
            page.wait_for_load_state("networkidle")
            page.wait_for_timeout(5000)
            html = page.content()
            result["html_length"] = len(html)
            result["contains_article_div"] = (
                'data-ad-preview="message"' in html or
                'data-testid="post_message"' in html or
                'FeedUnit_' in html
            )
    except Exception as e:
        result["error"] = str(e)
    return jsonify(result)

@app.route("/selector-test")
def selector_test():
    selector = request.args.get("q", 'div[data-testid="post_message"]')
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(storage_state="fb_state.json")
            page = context.new_page()
            page.goto("https://www.facebook.com/appledaily.tw/posts")
            page.wait_for_load_state("networkidle")
            page.wait_for_timeout(5000)
            page.wait_for_selector(selector, timeout=10000)
            elements = page.query_selector_all(selector)
            previews = [e.inner_text()[:100] for e in elements[:5]]
            return jsonify({
                "selector": selector,
                "count": len(elements),
                "previews": previews
            })
    except Exception as e:
        return jsonify({"error": str(e), "selector": selector})

@app.route("/selector-test-fallback")
def selector_test_fallback():
    selectors = [
        'div[data-testid="post_message"]',
        'div[data-ad-preview="message"]',
        'div[data-pagelet^="FeedUnit_"]',
        'div[role="article"]'
    ]
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(storage_state="fb_state.json")
            page = context.new_page()
            page.goto("https://www.facebook.com/appledaily.tw/posts")
            page.wait_for_load_state("networkidle")
            page.wait_for_timeout(5000)

            for selector in selectors:
                try:
                    page.wait_for_selector(selector, timeout=8000)
                    elements = page.query_selector_all(selector)
                    if elements:
                        previews = [e.inner_text()[:100] for e in elements[:5]]
                        return jsonify({
                            "selector": selector,
                            "count": len(elements),
                            "previews": previews
                        })
                except:
                    continue
            return jsonify({"error": "所有 selector 都失敗"})
    except Exception as e:
        return jsonify({"error": str(e)})

@app.route("/health")
def health():
    return Response("OK", status=200)

if __name__ == "__main__":
    init_db()
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
