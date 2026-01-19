# -*- coding: utf-8 -*-
import os
import sys
import time
from pathlib import Path
from dotenv import load_dotenv, set_key
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

# 強制指向當前目錄下的 .env
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ENV_PATH = os.path.join(BASE_DIR, ".env")

LOGIN_URL = "https://eip.iii.org.tw/"
SECOND_URL = "https://hrwt.iii.org.tw/TSM/MyWorkTime.aspx"

COOKIE_NAMES = {
    "ASP_NET_SESSION_ID": "ASP.NET_SessionId",
    "CLIENT_TICKET": "clientTicket",
    "CLIENT_USERNAME": "clientUserName",
}

def persist_env_value(env_key: str, value: str) -> None:
    if not value: return
    # 儲存到當前目錄的 .env
    set_key(ENV_PATH, env_key, value)
    preview = f"{value[:20]}..." if len(value) > 25 else value
    print(f"[Save] {env_key} = {preview}")

def collect_cookies(driver: webdriver.Chrome) -> None:
    cookies = {cookie["name"]: cookie["value"] for cookie in driver.get_cookies()}
    print(f"\nFound {len(cookies)} cookies in current page.")
    for env_key, cookie_name in COOKIE_NAMES.items():
        val = cookies.get(cookie_name)
        if val:
            persist_env_value(env_key, val)
        else:
            print(f"[Wait] Still looking for {cookie_name}...")

def run_capture():
    print(f"=== Pax Token Capture Test Tool ===")
    print(f"Target .env: {ENV_PATH}")
    
    options = webdriver.ChromeOptions()
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    driver.maximize_window()
    
    try:
        print(f"\n1. Opening Login Page: {LOGIN_URL}")
        driver.get(LOGIN_URL)
        print("Please log in. Pax will detect when you're done...")
        
        # 偵測登入成功並跳轉
        logged_in = False
        print("Waiting for login... (Time limit: 10 minutes)")
        for _ in range(300): # 10分鐘
            curr_url = driver.current_url.lower()
            try:
                cookies = {c["name"]: c["value"] for c in driver.get_cookies()}
            except:
                cookies = {}

            # 情況 A: 偵測到已進入工時系統 (使用者手動跳轉或已登入)
            if "hrwt.iii.org.tw" in curr_url:
                print("\n[Detect] Already in WorkTime system.")
                logged_in = True
                break
            
            # 情況 B: 偵測到 EIP 網域且已經有票證 (表示登入完成)
            # 這能有效避免在登入前短暫停留在 eip.iii.org.tw 導致的誤判 (例如重新導向中)
            if "eip.iii.org.tw" in curr_url and "clientTicket" in cookies:
                print(f"\n[Detect] Login successful! (Captured ticket for {cookies.get('clientUserName', 'unknown')})")
                print("Redirecting to HR system...")
                logged_in = True
                break
            
            if _ % 5 == 0: # 每 10 秒提示一次
                print(f"  > Waiting... (Current domain: {curr_url.split('/')[2] if '/' in curr_url and len(curr_url.split('/')) > 2 else curr_url})")

            time.sleep(2)
            
        if logged_in:
            print(f"2. Navigating to WorkTime page...")
            driver.get(SECOND_URL)
            time.sleep(3) # 等待加載
            
            # 抓取並存檔
            collect_cookies(driver)
            print("\n[Success] Tokens updated in .env!")
            print("You can now run 'python temp_test_submit_work_time.py' to test submission.")
            
    except Exception as e:
        print(f"\n[Error] {e}")
    finally:
        input("\nPress Enter to close browser...")
        driver.quit()

if __name__ == "__main__":
    run_capture()
