# refresh_login.py
from playwright.sync_api import sync_playwright
import os, json, time

def refresh_fb_login():
    FB_EMAIL = os.getenv("FB_EMAIL")
    FB_PASSWORD = os.getenv("FB_PASSWORD")

    if not FB_EMAIL or not FB_PASSWORD:
        raise Exception("❌ 未設定 FB_EMAIL 或 FB_PASSWORD 環境變數")

    print("🌐 正在登入 Facebook...")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()
        page.goto("https://www.facebook.com/login", timeout=60000)

        page.fill("input[name='email']", FB_EMAIL)
        page.fill("input[name='pass']", FB_PASSWORD)
        page.click("button[name='login']")
        page.wait_for_timeout(8000)  # 等待重導完成

        if "login" in page.url:
            raise Exception("❌ 登入失敗，請確認帳密或驗證狀態")

        storage = context.storage_state()
        with open("fb_state.json", "w", encoding="utf-8") as f:
            f.write(json.dumps(storage))

        print("✅ Cookie 已更新 fb_state.json")
        context.close()
        browser.close()

if __name__ == "__main__":
    refresh_fb_login()
