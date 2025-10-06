from playwright.sync_api import sync_playwright
import os, requests, sqlite3, base64, threading, json
from flask import Flask, Response, jsonify, request
from datetime import datetime
from refresh_login import refresh_fb_login

# === 工作目錄修正 ===
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# === 從環境變數還原 fb_state.json（避免 Render 重啟丟失） ===
state_env = os.getenv("FB_STATE_JSON")
if state_env and not os.path.exists("fb_state.json"):
    try:
        with open("fb_state.json", "w", encoding="utf-8") as f:
            f.write(base64.b64decode(state_env).decode("utf-8"))
        print("✅ 已從環境變數還原 fb_state.json")
    except Exception as e:
        print(f"⚠️ 無法還原 fb_state.json：{e}")

WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")
DB_FILE = "posts.db"
app = Flask(__name__)

# === Discord 推送功能 ===
def send_to_discord(content):
    if WEBHOOK_URL:
        try:
            requests.post(WEBHOOK_URL, json={"content": content})
        except Exception as e:
            app.logger.error(f"❌ Discord Webhook 錯誤：{e}")

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

# === 主要爬蟲 ===
def expand_see_more(page):
    page.wait_for_timeout(1200)
    for keyword in ["see more", "顯示更多", "查看更多"]:
        try:
            locators = page.locator(f'xpath=//*[contains(text(), "{keyword}")]')
            for i in range(min(locators.count(), 3)):
                locators.nth(i).click(timeout=500)
                page.wait_for_timeout(200)
        except Exception:
            pass

def run_scraper():
    app.logger.info("🚀 開始執行爬蟲...")
    if not os.path.exists("fb_state.json"):
        raise FileNotFoundError("❌ 缺少 fb_state.json，請先上傳或設定 FB_STATE_JSON")

    selectors = [
        'div[data-testid="post_message"]',
        'div[data-ad-preview="message"]',
        'div[data-pagelet^="FeedUnit_"]',
        'div[role="article"]'
    ]

    with sync_playwright() as p:
        # 🔧 超低記憶體模式啟動 Chromium
        browser = p.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-gpu",
                "--disable-dev-shm-usage",
                "--disable-software-rasterizer",
                "--single-process",
                "--no-zygote",
                "--disable-background-networking",
                "--disable-extensions",
                "--disable-sync"
            ]
        )

        context = browser.new_context(storage_state="fb_state.json")
        page = context.new_page()

        try:
            page.goto("https://www.facebook.com/LARPtimes", timeout=45000)
            page.wait_for_load_state("networkidle")
            page.wait_for_timeout(2000)
            expand_see_more(page)

            found_any = False
            for selector in selectors:
                try:
                    page.wait_for_selector(selector, timeout=3000)
                    articles = page.query_selector_all(selector)
                    if articles:
                        found_any = True
                        for a in articles[:3]:
                            text = a.inner_text()
                            post_id = a.get_attribute("data-ft") or str(hash(text))
                            preview = text[:200] + "..." if len(text) > 200 else text
                            send_to_discord(f"📢 新貼文：\n{preview}")
                            save_post(post_id, preview)
                        break
                except Exception as e:
                    app.logger.warning(f"⚠️ 無法找到 {selector}：{e}")
                    continue

            if found_any:
                app.logger.info("✅ 爬蟲完成並推送貼文。")
            else:
                app.logger.warning("⚠️ 未抓到任何貼文內容。")

        except Exception as e:
            app.logger.error(f"❌ 爬蟲錯誤：{e}")
        finally:
            page.close()
            context.close()
            browser.close()

# === Flask 路由 ===
@app.route("/")
def index():
    return "✅ FB爬蟲助手已啟動"

@app.route("/run")
def run():
    def run_task():
        try:
            run_scraper()
        except Exception as e:
            app.logger.error(f"❌ 爬蟲執行錯誤：{e}")

    threading.Thread(target=run_task, daemon=True).start()
    return Response("🚀 已啟動背景爬蟲，請稍候幾秒再查看 !fbstatus", status=200)

@app.route("/status")
def status():
    try:
        return jsonify({
            "fb_state_exists": os.path.exists("fb_state.json"),
            "env_FB_EMAIL": bool(os.getenv("FB_EMAIL")),
            "env_FB_PASSWORD": bool(os.getenv("FB_PASSWORD")),
            "env_DISCORD_WEBHOOK_URL": bool(os.getenv("DISCORD_WEBHOOK_URL")),
            "recent_posts": get_all_posts(limit=5)
        })
    except Exception as e:
        return jsonify({"error": str(e)})

@app.route("/refresh-login")
def refresh_login():
    try:
        refresh_fb_login()
        return Response("✅ 登入已更新", status=200)
    except Exception as e:
        return Response(f"❌ 登入失敗：{str(e)}", status=500)

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

@app.route("/routes")
def list_routes():
    return "\n".join([str(rule) for rule in app.url_map.iter_rules()])

@app.route("/health")
def health():
    return "OK", 200

# === 啟動伺服器 ===
if __name__ == "__main__":
    print("✅ Flask 啟動中：fb_scraper.py")
    for rule in app.url_map.iter_rules():
        print(f" - {rule}")
    init_db()
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
