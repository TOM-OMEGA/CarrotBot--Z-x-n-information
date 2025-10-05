from playwright.sync_api import sync_playwright
import os

email = os.getenv("FB_EMAIL")
password = os.getenv("FB_PASSWORD")

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context()
    page = context.new_page()
    page.goto("https://www.facebook.com/login", timeout=30000)
    page.wait_for_selector("input[name='email']", timeout=10000)
    page.fill("input[name='email']", email)
    page.fill("input[name='pass']", password)

    try:
        page.wait_for_selector("text=Log In", timeout=10000)
        page.click("text=Log In", timeout=5000)
    except Exception as e:
        print(f"❌ 登入按鈕點擊失敗：{e}")
        page.screenshot(path="login_click_error.png")
        raise e

    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(3000)

    if "login" in page.url or "checkpoint" in page.url:
        print("❌ 登入失敗，可能需要驗證或帳密錯誤")
        page.screenshot(path="login_error.png")
    else:
        context.storage_state(path="fb_state.json")
        print("✅ 登入成功，已更新 fb_state.json")

    page.close()
    context.close()
    browser.close()
