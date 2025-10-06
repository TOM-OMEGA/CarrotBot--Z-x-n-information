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
    try:
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
        print("✅ 資料庫初始化完成或已存在")
    except Exception as e:
        print(f"⚠️ 初始化資料庫失敗：{e}")

def ensure_db():
    """自動檢查資料庫是否存在，不存在就建立"""
    if not os.path.exists(DB_FILE):
        print("📦 偵測到 posts.db 不存在，正在建立中...")
        init_db()
    else:
        try:
            conn = sqlite3.connect(DB_FILE)
            c = conn.cursor()
            c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='posts'")
            if not c.fetchone():
                print("📦 偵測到資料表不存在，重新建立中...")
                init_db()
            conn.close()
        except Exception as e:
            print(f"⚠️ 資料庫檢查錯誤：{e}")
            init_db()

def save_post(post_id, content):
    ensure_db()
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO posts (id, content, created_at) VALUES (?, ?, ?)",
              (post_id, content, datetime.utcnow().isoformat()))
    conn.commit()
    conn.close()

def get_all_posts(limit=20):
    ensure_db()
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
    ensure_db()
    if not os.path.exists("fb_state.json"):
        raise FileNotFoundError("❌ 缺少 fb_state.json，請先上傳或設定 FB_STATE_JSON")

    selectors = [
        'div[data-testid="post_message"]',
        'div[data-ad-preview="message"]',
        'div[data-pagelet^="FeedUnit_"]',
        'div[role="article"]',
        'div[role="article"] span[dir="auto"]'
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
            # ⚙️ 修改為你要爬的粉專
            page.goto("https://www.facebook.com/appledaily.tw/posts", timeout=60000)
            page.wait_for_load_state("networkidle")
            page.wait_for_timeout(8000)
            expand_see_more(page)

            found_any = False
            for selector in selectors:
                try:
                    page.wait_for_selector(selector, timeout=3000)
                    articles = page.query_selector_all(selector)
                    if articles:
                        found_any = True
                        for a in articles[:3]:
                            text = a.inner_text().strip()
                            img_src = ""
                            try:
                                img = a.query_selector("img")
                                if img:
                                    img_src = img.get_attribute("src") or ""
                            except:
                                pass

                            if not text and img_src:
                                preview = f"🖼️ 圖片貼文：{img_src}"
                            elif text:
                                preview = text[:200] + "..." if len(text) > 200 else text
                            else:
                                preview = "⚠️ 無法解析貼文內容"

                            post_id = a.get_attribute("data-ft") or str(hash(preview))
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
        ensure_db()
        return jsonify({
            "fb_state_exists": os.path.exists("fb_state.json"),
            "env_FB_EMAIL": bool(os.getenv("FB_EMAIL")),
            "env_FB_PASSWORD": bool(os.getenv("FB_PASSWORD")),
            "env_DISCORD_WEBHOOK_URL": bool(os.getenv("DISCORD_WEBHOOK_URL")),
            "recent_posts": get_all_posts(limit=5)
        })
    except Exception as e:
        return jsonify({"error": str(e)})

@app.route("/init-db")
def init_database():
    try:
        init_db()
        return "✅ 資料庫初始化完成"
    except Exception as e:
        return f"❌ 初始化失敗：{e}"

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
    ensure_db()  # 確保資料庫存在
    for rule in app.url_map.iter_rules():
        print(f" - {rule}")
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
