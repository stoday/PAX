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
# LOGIN_URL = "https://hrwt.iii.org.tw"
SECOND_URL = "https://hrwt.iii.org.tw"

if getattr(sys, 'frozen', False):
    ENV_PATH = Path(os.path.dirname(sys.executable)) / ".env"
else:
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
    # print("若環境變數 `EIP_USER`/`EIP_PASS` 或 `TRAVEL_EIP_USER`/`TRAVEL_EIP_PASS` 已設定，程式會嘗試自動登入；否則請手動輸入帳號密碼後按 Enter 繼續。")
    # Allow caller to perform auto login by returning to caller; we will
    # attempt auto-login from the main flow if credentials are available.
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
        # Try automatic login if credentials are available in env.
        load_dotenv()
        username = None
        password = None
        for u_key, p_key in (("EIP_USER", "EIP_PASS"), ("TRAVEL_EIP_USER", "TRAVEL_EIP_PASS")):
            if not username:
                username = __import__("os").getenv(u_key)
            if not password:
                password = __import__("os").getenv(p_key)

        if username and password:
            # perform auto login
            print("偵測到帳密，嘗試自動填入並登入...")
            try:
                # reuse a small auto-login helper defined below
                auto_login(driver, username, password)
            except Exception as exc:
                print(f"[警告] 自動登入失敗，將回到手動登入：{exc}")
                wait_for_login(driver)
        else:
            wait_for_login(driver)
        collect_cookies(driver)
        collect_bearer_token(driver)
        print(f"[完成] 已將資訊寫入 {ENV_PATH}")
    except Exception as exc:
        print(f"[錯誤] 擷取資料時發生例外：{exc}")
    finally:
        print("關閉瀏覽器 ...")
        driver.quit()


def auto_login(driver: webdriver.Chrome, username: str, password: str) -> None:
    """Auto-fill username/password and submit the login form on the EIP login page.

    Mirrors logic used in `travelmate/get_travel_web_cookie.py` to handle hidden
    inputs or overlays by falling back to JS assignment and JS click.
    """
    driver.get(LOGIN_URL)
    print(f"自動填入帳密並嘗試登入：{LOGIN_URL}")

    wait = WebDriverWait(driver, 20)
    account_el = wait.until(EC.visibility_of_element_located((By.ID, "EmpAccount")))
    password_el = wait.until(EC.visibility_of_element_located((By.ID, "Password")))

    try:
        account_el.clear()
        account_el.send_keys(username)
    except Exception:
        driver.execute_script(
            "arguments[0].value = arguments[1]; arguments[0].dispatchEvent(new Event('input'));",
            account_el,
            username,
        )

    try:
        password_el.clear()
        password_el.send_keys(password)
    except Exception:
        driver.execute_script(
            "arguments[0].value = arguments[1]; arguments[0].dispatchEvent(new Event('input'));",
            password_el,
            password,
        )

    try:
        submit_btn = wait.until(EC.element_to_be_clickable((By.ID, "ADSubmit_m")))
        submit_btn.click()
    except Exception:
        try:
            btn = driver.find_element(By.ID, "ADSubmit_m")
            driver.execute_script("arguments[0].click();", btn)
        except Exception:
            raise

    WebDriverWait(driver, 30).until(lambda d: d.execute_script("return document.readyState") == "complete")
    WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.TAG_NAME, "body")))


if __name__ == "__main__":
    get_tokens_from_browser()
