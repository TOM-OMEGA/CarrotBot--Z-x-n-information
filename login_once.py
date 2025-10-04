from playwright.sync_api import sync_playwright
import os

EMAIL = os.getenv("FB_EMAIL")
PASSWORD = os.getenv("FB_PASSWORD")

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context()
    page = context.new_page()
    page.goto("https://www.facebook.com/login")
    page.fill('input[name="email"]', EMAIL)
    page.fill('input[name="pass"]', PASSWORD)
    page.click('button[name="login"]')
    page.wait_for_timeout(10000)
    context.storage_state(path="fb_state.json")
    print("✅ 登入成功，已儲存 fb_state.json")
