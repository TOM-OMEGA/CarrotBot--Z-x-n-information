from playwright.sync_api import sync_playwright
import os, requests, sqlite3, base64
from flask import Flask, Response, jsonify, request
from datetime import datetime
from refresh_login import refresh_fb_login

WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")
DB_FILE = "posts.db"
app = Flask(__name__)

# === Discord 推送功能 ===
def send_to_discord(content):
    if WEBHOOK_URL:
        requests.post(WEBHOOK_URL, json={"content": content})

# === SQLite 初始化 ===
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
    c.execute("INSERT OR IGNORE INTO posts (id, content, created_at) VALUES (?, ?, ?)", (post_id, content, datetime.utcnow().isoformat()))
    conn.commit()
    conn.close()

def get_all_posts(limit=20):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT id, content, created_at FROM posts ORDER BY created_at DESC LIMIT ?", (limit,))
    rows = c.fetchall()
    conn.close()
    return [{"id": r[0], "content": r[1], "created_at": r[2]} for r in rows]

# === 主要爬蟲 ===
def expand_see_more(page):
    page.wait_for_timeout(2000)
    keywords = ["see more", "顯示更多", "查看更多"]
    for keyword in keywords:
        try:
            locators = page.locator(f'xpath=//*[contains(text(), "{keyword}")]')
            count = min(locators.count(), 5)
            for i in range(count):
                locators.nth(i).click(timeout=1000)
                page.wait_for_timeout(500)
        except:
            pass

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
                    for a in articles[:3]:
                        text = a.inner_text()
                        post_id = a.get_attribute("data-ft") or str(hash(text))
                        preview = text[:200] + "..." if len(text) > 200 else text
                        send_to_discord(f"📢 新貼文：\n{preview}")
                        save_post(post_id, preview)
                    break
            except:
                continue
        page.close()
        context.close()
        browser.close()

# === Flask 路由 ===
@app.route("/")
def index():
    return "✅ FB爬蟲助手已啟動"

@app.route("/run")
def run():
    try:
        run_scraper()
        return Response("✅ 執行完成", status=200)
    except Exception as e:
        return Response(f"❌ 執行錯誤：{str(e)}", status=500)

@app.route("/status")
def status():
    return jsonify({
        "fb_state_exists": os.path.exists("fb_state.json"),
        "env_FB_EMAIL": bool(os.getenv("FB_EMAIL")),
        "env_FB_PASSWORD": bool(os.getenv("FB_PASSWORD")),
        "env_DISCORD_WEBHOOK_URL": bool(os.getenv("DISCORD_WEBHOOK_URL")),
        "recent_posts": get_all_posts(limit=5)
    })

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
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto("https://www.facebook.com/login", timeout=30000)
            page.wait_for_timeout(3000)
            screenshot_path = "login_debug.png"
            page.screenshot(path=screenshot_path)
            page.close()
            browser.close()
        with open(screenshot_path, "rb") as f:
            encoded = base64.b64encode(f.read()).decode("utf-8")
        return jsonify({"image_base64": encoded})
    except Exception as e:
        return jsonify({"error": str(e)})

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

@app.route("/clear-cookie", methods=["POST"])
def clear_cookie():
    try:
        os.remove("fb_state.json")
        return "✅ Cookie 已清除"
    except FileNotFoundError:
        return "⚠️ Cookie 不存在"
    except Exception as e:
        return f"❌ 清除失敗：{str(e)}"

@app.route("/routes")
def list_routes():
    return "\n".join([str(rule) for rule in app.url_map.iter_rules()])

@app.route("/health")
def health():
    return "OK", 200

# === 啟動伺服器 ===
if __name__ == "__main__":
    print("✅ Flask 啟動中：fb_scraper.py")
    print("📚 已掛載路由：")
    for rule in app.url_map.iter_rules():
        print(f" - {rule}")
    init_db()
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
