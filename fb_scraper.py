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

def expand_see_more(page):
    page.wait_for_timeout(2000)
    keywords = ["see more", "顯示更多", "查看更多"]
    expanded = 0
    for keyword in keywords:
        try:
            locators = page.locator(f'xpath=//*[contains(text(), "{keyword}")]')
            count = min(locators.count(), 5)  # 限制最多展開 5 個
            print(f"🔍 嘗試展開「{keyword}」：最多展開 {count} 個")
            for i in range(count):
                try:
                    locators.nth(i).click(timeout=1000)
                    page.wait_for_timeout(500)
                    expanded += 1
                except Exception as e:
                    print(f"⚠️ 點擊失敗：{e}")
        except Exception as e:
            print(f"⚠️ 無法搜尋「{keyword}」：{e}")
    print(f"✅ 展開成功 {expanded} 個貼文")

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
        expand_see_more(page)

        for selector in selectors:
            try:
                page.wait_for_selector(selector, timeout=8000)
                articles = page.query_selector_all(selector)
                if articles:
                    print(f"✅ 使用 selector：{selector}，找到 {len(articles)} 篇貼文")
                    for a in articles[:3]:  # 最多處理 3 篇
                        text = a.inner_text()
                        post_id = a.get_attribute("data-ft") or str(hash(text))
                        preview = text[:200] + "..." if len(text) > 200 else text
                        send_to_discord(f"📢 新貼文：\n{preview}")
                        save_post(post_id, preview)
                    break
            except:
                print(f"⚠️ selector 超時或無結果：{selector}")
        page.close()
        context.close()
        browser.close()

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
            page.wait_for_timeout(3000)
            title = page.title()
            url = page.url
            page.close()
            context.close()
            browser.close()
            return jsonify({"title": title, "url": url})
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
            page.wait_for_timeout(3000)
            html = page.content()
            result["html_length"] = len(html)
            result["contains_article_div"] = (
                'data-ad-preview="message"' in html or
                'data-testid="post_message"' in html or
                'FeedUnit_' in html
            )
            page.close()
            context.close()
            browser.close()
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
            page.wait_for_timeout(3000)
            page.wait_for_selector(selector, timeout=10000)
            elements = page.query_selector_all(selector)
            previews = [e.inner_text()[:100] for e in elements[:5]]
            page.close()
            context.close()
            browser.close()
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
            page.wait_for_timeout(3000)

            for selector in selectors:
                try:
                    page.wait_for_selector(selector, timeout=8000)
                    elements = page.query_selector_all(selector)
                    if elements:
                        previews = [e.inner_text()[:100] for e in elements[:5]]
                        page.close()
                        context.close()
                        browser.close()
                        return jsonify({
                            "selector": selector,
                            "count": len(elements),
                            "previews": previews
                        })
                except:
                    continue
            page.close()
            context.close()
            browser.close()
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

from refresh_login import refresh_fb_login

@app.route("/refresh-login")
def refresh_login():
    try:
        refresh_fb_login()
        return Response("✅ 登入已更新", status=200)
    except Exception as e:
        return Response(f"❌ 登入失敗：{str(e)}", status=500)

@app.route("/debug-login")
def debug_login():
    try:
        from playwright.sync_api import sync_playwright
        import base64

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context()
            page = context.new_page()
            page.goto("https://www.facebook.com/login", timeout=30000)
            page.wait_for_timeout(3000)
            screenshot_path = "login_debug.png"
            page.screenshot(path=screenshot_path)
            page.close()
            context.close()
            browser.close()

        with open(screenshot_path, "rb") as f:
            encoded = base64.b64encode(f.read()).decode("utf-8")
        return jsonify({"image_base64": encoded})

    except Exception as e:
        return jsonify({"error": str(e)})

@app.route("/status")
def status():
    print("📡 收到 /status 請求")
    try:
        result = {
            "fb_state_exists": os.path.exists("fb_state.json"),
            "env_FB_EMAIL": bool(os.getenv("FB_EMAIL")),
            "env_FB_PASSWORD": bool(os.getenv("FB_PASSWORD")),
            "env_DISCORD_WEBHOOK_URL": bool(os.getenv("DISCORD_WEBHOOK_URL")),
            "recent_posts": get_all_posts(limit=5)
        }
        return jsonify(result)
    except Exception as e:
        print(f"❌ /status 發生錯誤：{e}")
        return jsonify({"error": str(e)})

@app.route("/")
def index():
    return "✅ FB爬蟲助手已啟動"

@app.route("/upload-cookie", methods=["POST"])
def upload_cookie():
    file = request.files.get("file")
    if not file:
        return "❌ 未收到檔案"
    if file.filename != "fb_state.json":
        return "⚠️ 檔名必須為 fb_state.json"
    try:
        file.save("fb_state.json")
        return "✅ Cookie 已更新"
    except Exception as e:
        return f"❌ 儲存失敗：{str(e)}"

# ✅ 合併主程式區塊
if __name__ == "__main__":
    init_db()
    port = int(os.getenv("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
