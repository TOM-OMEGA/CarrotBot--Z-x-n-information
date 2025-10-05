from playwright.sync_api import sync_playwright
import os

def refresh_fb_login():
    email = os.getenv("FB_EMAIL")
    password = os.getenv("FB_PASSWORD")

    if not email or not password:
        print("❌ 請先設定 FB_EMAIL 和 FB_PASSWORD 環境變數")
        return

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        try:
            page.goto("https://www.facebook.com/login", timeout=30000)
            page.wait_for_selector("input[name='email']", timeout=10000)
            page.fill("input[name='email']", email)
            page.fill("input[name='pass']", password)
            page.wait_for_selector("button[name='login']", timeout=10000)
            page.click("button[name='login']", timeout=5000)
            page.wait_for_load_state("networkidle")
            page.wait_for_timeout(3000)

            # 登入失敗偵測
            if "login" in page.url or "checkpoint" in page.url:
                print("❌ 登入失敗，可能需要驗證或帳密錯誤")
                page.screenshot(path="login_error.png")
            else:
                context.storage_state(path="fb_state.json")
                print("✅ 登入成功，已更新 fb_state.json")

        except Exception as e:
            print(f"⚠️ 登入流程錯誤：{e}")
            page.screenshot(path="login_exception.png")

        page.close()
        context.close()
        browser.close()
