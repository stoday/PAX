# -*- coding: utf-8 -*-
import time
import os
import sys
import shutil
from pathlib import Path

from dotenv import load_dotenv, set_key
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

LOGIN_URL = "https://eip.iii.org.tw/"
SECOND_URL = "https://hrwt.iii.org.tw"

if getattr(sys, 'frozen', False):
    BASE_DIR = Path(os.path.dirname(sys.executable))
else:
    BASE_DIR = Path(__file__).resolve().parent.parent

ENV_PATH = BASE_DIR / ".env"

def get_tokens_from_browser(headless: bool = False) -> bool:
    load_dotenv(str(ENV_PATH))
    
    # 使用臨時 Profile (每次都是全新的)
    temp_profile_dir = BASE_DIR / "temp_chrome_profile"
    if temp_profile_dir.exists():
        try: shutil.rmtree(temp_profile_dir)
        except: pass
    os.makedirs(temp_profile_dir, exist_ok=True)

    if not headless:
        print("\n" + "╔" + "═"*62 + "╗")
        print("║" + " " * 22 + "【 認證操作指引 】" + " " * 23 + "║")
        print("╠" + "═"*62 + "╣")
        print("║  1. 請關閉所有 Chrome 視窗                                    ║")
        print("║  2. 按 Enter，Pax 會啟動一個全新的認證視窗                    ║")
        print("║  3. 請手動輸入帳號密碼登入 (需進行 ADPT/簡訊驗證)             ║")
        print("║  4. 登入成功後，請留在網頁上不要關閉                          ║")
        print("║  5. 回到這裡按 Enter，Pax 會自動擷取 Token                    ║")
        print("╚" + "═"*62 + "╝")
        
        input("\n>>> 請先關閉所有 Chrome，然後按 [Enter] 開始：")
        
        print("\n[執行] 正在啟動認證瀏覽器...")
        
        # 設定 Chrome 選項 (使用臨時 Profile)
        options = Options()
        options.add_argument(f"user-data-dir={str(temp_profile_dir)}")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        # options.add_argument("--incognito") # 可選：強制無痕
        
        driver = None
        try:
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=options)
            
            # 設定超時
            driver.set_page_load_timeout(60)
            
            print("\n[成功] 瀏覽器已啟動！")
            print("[執行] 正在導航至 EIP 首頁...")
            driver.get(LOGIN_URL)
            
            print("\n" + "-"*64)
            print("  [狀態] 視窗已開啟。")
            print("  [操作] 請手動登入 (可能需要手機驗證)。")
            print("  [操作] 登入成功後，請回到這裡按 Enter。")
            print("-" * 64)
            
            input("\n>>> [最後一步] 我已完成登入，按 [Enter] 擷取 Token：")
            
            print("\n[執行] 正在擷取認證資訊...")
            
            # 手動跳轉 HRWT 確保 Cookie 被寫入
            print(f"  - 正在跳轉至: {SECOND_URL}")
            try:
                driver.get(SECOND_URL)
                time.sleep(2)
            except:
                pass
            
            # 抓取 Cookie
            cookies = {c["name"]: c["value"] for c in driver.get_cookies()}
            target_cookies = {
                "ASP_NET_SESSION_ID": "ASP.NET_SessionId",
                "CLIENT_TICKET": "clientTicket",
                "CLIENT_USERNAME": "clientUserName",
            }
            
            found_count = 0
            for env_key, cookie_name in target_cookies.items():
                val = cookies.get(cookie_name)
                if val:
                    set_key(str(ENV_PATH), env_key, val)
                    print(f"  - [成功] 獲取 {env_key}")
                    found_count += 1
            
            # 清理臨時 Profile
            driver.quit()
            try: shutil.rmtree(temp_profile_dir)
            except: pass
            
            if found_count > 0:
                print(f"\n[完成] 成功獲取 {found_count} 個 Token！")
                return True
            else:
                print("\n[失敗] 未能抓取到 Token，可能是登入未完成。")
                return False
                
        except Exception as e:
            print(f"\n[錯誤] {e}")
            if driver:
                try: driver.quit()
                except: pass
            return False

    return False

if __name__ == "__main__":
    get_tokens_from_browser()
