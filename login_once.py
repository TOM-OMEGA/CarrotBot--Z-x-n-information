from playwright.sync_api import sync_playwright
import json

def login_and_save_cookie():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)  # ✅ GUI 模式，可手動通過驗證
        context = browser.new_context()
        page = context.new_page()

        print("🔐 請手動登入 Facebook，通過驗證後關閉分頁即可")
        page.goto("https://www.facebook.com/login")

        input("⏳ 登入完成後請按 Enter 繼續儲存 cookie...")

        # ✅ 儲存登入狀態
        context.storage_state(path="fb_state.json")
        print("✅ 登入狀態已儲存至 fb_state.json")

        browser.close()

if __name__ == "__main__":
    login_and_save_cookie()
