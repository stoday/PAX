import os
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from dotenv import set_key, load_dotenv
import time # 導入 time 模組用於短暫等待

def get_tokens_from_browser():
    """
    自動打開 tel.iii.org.tw 網頁，讓使用者手動登入後，
    嘗試抓取 Bearer Token 和 Cookie Token，並儲存到 .env 檔案中。
    """
    load_dotenv() # 載入現有的 .env 檔案，如果有的話

    login_url = "https://tel.iii.org.tw/telbook/"
    
    # 確保 .env 檔案路徑正確，位於專案根目錄
    env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')

    print("正在啟動 Chrome 瀏覽器...")
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service)
    driver.maximize_window()

    try:
        driver.get(login_url)
        print(f"已打開網頁: {login_url}")
        print("請在瀏覽器中手動輸入您的帳號和密碼並登入。")
        print("登入成功後，請回到此終端機並按 Enter 鍵繼續...")

        # 等待使用者手動登入
        input("按下 Enter 鍵以繼續...")

        # 等待頁面加載完成，例如等待登入後才出現的元素
        # 這裡假設登入後頁面會有一個 ID 為 'app' 的主要容器元素。
        # 如果實際頁面沒有這個 ID，您可能需要根據登入後頁面實際的 HTML 結構調整等待條件。
        try:
            WebDriverWait(driver, 60*3).until(
                EC.presence_of_element_located((By.ID, "app"))
            )
            print("頁面已加載完成，嘗試獲取 Token。")
        except Exception:
            print("警告: 未能確認頁面完全加載 (ID為'app'的元素未出現)。")
            print("程式將繼續嘗試獲取 Token，但請確保您已成功登入。")
            time.sleep(5) # 短暫等待，給頁面一些時間執行JS和發送API請求

        # 嘗試獲取 Cookie Token
        cookie_token = None
        cookies = driver.get_cookies()
        for cookie in cookies:
            if cookie['name'] == 'token': # 根據 main.py 中的 cookie 名稱
                cookie_token = cookie['value']
                print(f"已找到 Cookie Token: {cookie_token[:30]}...") # 顯示部分內容
                break
        if cookie_token:
            set_key(env_path, "TEL_COOKIE_TOKEN", cookie_token)
            print("Cookie Token 已儲存到 .env 檔案。")
        else:
            print("未找到名為 'token' 的 Cookie。")
            print("請手動檢查瀏覽器開發者工具 (F12) -> 應用程式 (Application) -> Cookies，確認 'token' 的名稱和值。")

        # 嘗試獲取 Bearer Token (通常在 localStorage 或 sessionStorage 中)
        bearer_token = None
        # 嘗試從 localStorage 獲取常見的鍵
        # 這裡列出了幾個常見的鍵名，網站可能會使用其中之一來儲存 Bearer Token 的值
        js_script_local = """
        return localStorage.getItem('Bearer') || 
               localStorage.getItem('jwt') || 
               localStorage.getItem('accessToken') ||
               localStorage.getItem('token'); 
        """
        bearer_token = driver.execute_script(js_script_local)
        
        # 如果 localStorage 沒有，嘗試 sessionStorage
        if not bearer_token:
            js_script_session = """
            return sessionStorage.getItem('Bearer') || 
                   sessionStorage.getItem('jwt') || 
                   sessionStorage.getItem('accessToken') ||
                   sessionStorage.getItem('token');
            """
            bearer_token = driver.execute_script(js_script_session)

        if bearer_token:
            set_key(env_path, "TEL_BEARER_TOKEN", bearer_token)
            print(f"已找到 Bearer Token: {bearer_token[:30]}...") # 顯示部分內容
            
            # 存至 .env 檔案
            set_key(env_path, "TEL_BEARER_TOKEN", bearer_token)
            print("Bearer Token 已儲存到 .env 檔案。")
        else:
            print("未在 localStorage 或 sessionStorage 中找到 Bearer Token。")
            print("請手動檢查瀏覽器開發者工具 (F12) -> 應用程式 (Application) -> 儲存空間 (Local Storage / Session Storage)，尋找類似 'Bearer', 'jwt', 'accessToken' 或 'token' 的鍵。")
            print("如果 Bearer Token 僅存在於網路請求的 'Authorization' 標頭中，且未持久化到儲存空間，則無法透過此方法自動獲取。")
            print("您可能需要手動從瀏覽器開發者工具的網路分頁中複製 'Authorization' 標頭中的 Bearer Token。")

    except Exception as e:
        print(f"發生錯誤: {e}")
    finally:
        print("關閉瀏覽器。")
        driver.quit()


if __name__ == "__main__":
    get_tokens_from_browser()