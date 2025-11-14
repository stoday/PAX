import time
from pathlib import Path

from dotenv import load_dotenv, set_key
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager


LOGIN_URL = "https://eip.iii.org.tw/"
# LOGIN_URL = "https://tel.iii.org.tw/telbook/"
# LOGIN_URL = "https://hrwt.iii.org.tw"
SECOND_URL = "https://hrwt.iii.org.tw"

ENV_PATH = Path(__file__).resolve().parent.parent / ".env"
COOKIE_NAMES = {
    "TEL_COOKIE_TOKEN": "token",
    "ASP_NET_SESSION_ID": "ASP.NET_SessionId",
    "CLIENT_TICKET": "clientTicket",
    "CLIENT_USERNAME": "clientUserName",
}
STORAGE_KEYS = ("Bearer", "jwt", "accessToken", "token")


def persist_env_value(env_key: str, value: str) -> None:
    """Save a value to the .env file if present."""
    if not value:
        print(f"[警告] 無法取得 {env_key}，請確認登入流程是否完成。")
        return

    set_key(str(ENV_PATH), env_key, value)
    if len(value) > 40:
        preview = f"{value[:37]}..."
    else:
        preview = value
    print(f"[成功] {env_key} => {preview}")
    

def collect_cookies(driver: webdriver.Chrome) -> None:
    """Grab required cookies from the current browser session."""
    cookies = {cookie["name"]: cookie["value"] for cookie in driver.get_cookies()}
    for env_key, cookie_name in COOKIE_NAMES.items():
        persist_env_value(env_key, cookies.get(cookie_name))


def collect_bearer_token(driver: webdriver.Chrome) -> None:
    """Attempt to read bearer token from localStorage / sessionStorage."""
    bearer_token = None

    for storage in ("localStorage", "sessionStorage"):
        if bearer_token:
            break

        for key in STORAGE_KEYS:
            script = f"return {storage}.getItem('{key}');"
            token = driver.execute_script(script)
            if token:
                bearer_token = token
                break

    if bearer_token:
        persist_env_value("TEL_BEARER_TOKEN", bearer_token)
    else:
        print("[警告] 尚未在 localStorage / sessionStorage 找到 Bearer Token。")
        print("        請於開發者工具確認 Token 所在位置後再試一次。")


def wait_for_login(driver: webdriver.Chrome) -> None:
    """Give the user time to log in and wait until the app shell loads."""
    driver.get(LOGIN_URL)
    print(f"已開啟登入頁面：{LOGIN_URL}")
    print("請在瀏覽器中手動輸入帳號密碼完成登入後，回到終端機按 Enter 繼續。")
    input("按下 Enter 後開始跳轉到下一個頁面...")
    # 在網址列自動輸入 https://hrwt.iii.org.tw 後自動跳轉
    current_url = driver.current_url
    if current_url != LOGIN_URL:
        print(f"[提示] 偵測到目前網址為 {current_url}，將繼續進行資料擷取。")
        
    driver.implicitly_wait(5)
    driver.get(SECOND_URL)
    input("按下 Enter 後開始擷取跳轉到後的頁面資料...")

    try:
        # 嘗試多種可能的元素選擇器
        conditions = [
            EC.presence_of_element_located((By.ID, "LabHR")),
            EC.presence_of_element_located((By.TAG_NAME, "body")),
            EC.presence_of_element_located((By.CSS_SELECTOR, "[id*='app'], [class*='app'], main, #content")),
        ]
        
        for i, condition in enumerate(conditions):
            try:
                WebDriverWait(driver, 10).until(condition)
                print(f"[成功] 使用條件 {i+1} 偵測到頁面載入完成")
                break
            except:
                if i == len(conditions) - 1:
                    raise
                continue
                
    except Exception:
        print("[提示] 等待頁面載入逾時，仍會嘗試擷取資料。")
        time.sleep(5)


def get_tokens_from_browser() -> None:
    """Launch Chrome, let the user log in, then capture tokens/cookies."""
    load_dotenv()

    print("啟動 Chrome 瀏覽器 ...")
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service)
    driver.maximize_window()

    try:
        wait_for_login(driver)
        collect_cookies(driver)
        collect_bearer_token(driver)
        print(f"[完成] 已將資訊寫入 {ENV_PATH}")
    except Exception as exc:
        print(f"[錯誤] 擷取資料時發生例外：{exc}")
    finally:
        print("關閉瀏覽器 ...")
        driver.quit()


if __name__ == "__main__":
    get_tokens_from_browser()
