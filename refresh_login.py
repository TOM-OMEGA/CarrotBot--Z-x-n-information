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
        page.goto("https://www.facebook.com/login")
        page.fill("input[name='email']", email)
        page.fill("input[name='pass']", password)
        page.click("button[name='login']")
        page.wait_for_load_state("networkidle")
        context.storage_state(path="fb_state.json")
        print("✅ 登入成功，已更新 fb_state.json")
        page.close()
        context.close()
        browser.close()
