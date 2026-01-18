# -*- coding: utf-8 -*-
import time
import os
import sys
from pathlib import Path

from dotenv import load_dotenv, set_key
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager


LOGIN_URL = "https://eip.iii.org.tw/"
SECOND_URL = "https://hrwt.iii.org.tw"

if getattr(sys, 'frozen', False):
    ENV_PATH = Path(os.path.dirname(sys.executable)) / ".env"
else:
    # 這裡要小心路徑，如果是從 ui/tray_app.py 呼叫，__file__ 會是 app/get_token.py
    ENV_PATH = Path(__file__).resolve().parent.parent / ".env"

COOKIE_NAMES = {
    "TEL_COOKIE_TOKEN": "token",
    "ASP_NET_SESSION_ID": "ASP.NET_SessionId",
    "CLIENT_TICKET": "clientTicket",
    "CLIENT_USERNAME": "clientUserName",
}


def persist_env_value(env_key: str, value: str) -> None:
    """Save a value to the .env file if present."""
    if not value:
        return

    # 為值加上雙引號
    quoted_value = f'"{value}"'
    set_key(str(ENV_PATH), env_key, quoted_value)
    
    preview = f"{value[:37]}..." if len(value) > 40 else value
    print(f"[成功] {env_key} => {preview}")
    

def collect_cookies(driver: webdriver.Chrome) -> None:
    """Grab required cookies from the current browser session."""
    cookies = {cookie["name"]: cookie["value"] for cookie in driver.get_cookies()}
    for env_key, cookie_name in COOKIE_NAMES.items():
        val = cookies.get(cookie_name)
        if val:
            persist_env_value(env_key, val)


def wait_for_login_and_capture(driver: webdriver.Chrome) -> None:
    """自動偵測登入並擷取資訊"""
    driver.get(LOGIN_URL)
    print(f"已開啟登入頁面：{LOGIN_URL}")
    print("請在瀏覽器內完成登入，Pax 將自動執行後續動作...")
    
    # 1. 監控是否登入成功 (透過網址或特定 Cookie)
    start_time = time.time()
    timeout = 300 # 5 分鐘
    
    logged_in = False
    while time.time() - start_time < timeout:
        try:
            # 檢查是否有登入後的特徵 (例如網域改變，或是已經抓到 EIP 的 Session)
            current_url = driver.current_url.lower()
            cookies = {c["name"]: c["value"] for c in driver.get_cookies()}
            
            # EIP 登入成功的特徵：網址不再是 login 頁，或是已經抓到 ASP.NET_SessionId
            if "eip.iii.org.tw" in current_url and "/login" not in current_url and cookies.get("ASP.NET_SessionId"):
                print("[偵測] EIP 登入成功，正在自動跳轉至工時系統...")
                logged_in = True
                break
            
            # 或者使用者直接在該瀏覽器輸入了 hrwt
            if "hrwt.iii.org.tw" in current_url:
                logged_in = True
                break
        except:
            break
        time.sleep(2)
    
    if not logged_in:
        print("[逾時] 登入超時或瀏覽器已關閉。")
        return

    # 2. 自動跳轉到工時系統 (這步最關鍵，讓它自動完成)
    print("[執行] 自動導向至：", SECOND_URL)
    driver.get(SECOND_URL)
    
    # 3. 等待進入工時系統網域並抓取資料
    start_time = time.time()
    while time.time() - start_time < 30: # 給 30 秒跳轉時間
        try:
            current_url = driver.current_url.lower()
            if "hrwt.iii.org.tw" in current_url:
                # 確保頁面加載一些基本內容
                time.sleep(2)
                print("[成功] 已進入工時系統，正在擷取認證資訊...")
                collect_cookies(driver)
                return
        except:
            break
        time.sleep(1)
    
    # 如果自動跳轉沒成功，最後再試一次強制擷取 (可能在跳轉過程中已經有 Cookie 了)
    collect_cookies(driver)


def get_tokens_from_browser() -> None:
    """Launch Chrome, let the user log in, then capture tokens/cookies."""
    load_dotenv(str(ENV_PATH))

    print("啟動 Chrome 瀏覽器 ...")
    options = webdriver.ChromeOptions()
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    
    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        driver.maximize_window()
        
        # 移除 WebDriver 特徵
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

        # 執行自動偵測流程
        wait_for_login_and_capture(driver)
        
        print(f"[完成] 認證流程結束。")
    except Exception as exc:
        print(f"[錯誤] 發生例外：{exc}")
    finally:
        try:
            driver.quit()
        except: pass


if __name__ == "__main__":
    get_tokens_from_browser()
