#!/usr/bin/env python3
"""
Launch a browser, let the user log into EIP, then capture cookies for the
travel application site and store them in .env_cookie.
"""
from __future__ import annotations

from pathlib import Path
import os
from typing import Dict, Tuple

from dotenv import load_dotenv, set_key
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager


LOGIN_URL = "https://eip.iii.org.tw"
TARGET_URL = "https://expapply.iii.org.tw/expApply/Apply.aspx"
ENV_PATH = Path(__file__).resolve().parent / ".env_cookie"
IMPORTANT_COOKIES = ("clientUserName", "clientTicket", "ASP.NET_SessionId")


def launch_browser() -> webdriver.Chrome:
    """Start a Chrome browser via webdriver-manager."""
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service)
    driver.maximize_window()
    return driver


def wait_for_manual_login(driver: webdriver.Chrome) -> None:
    """Open the login page and pause until the user confirms they are logged in."""
    driver.get(LOGIN_URL)
    print(f"已開啟登入頁面：{LOGIN_URL}")
    print("請在瀏覽器中手動輸入帳號密碼完成登入後，回到終端機按 Enter 繼續。")
    input("登入完成後按 Enter 繼續跳轉到出差申請頁面...")


def auto_login(driver: webdriver.Chrome, username: str, password: str) -> None:
    """Auto-fill username/password and submit the login form.

    This targets the login inputs with id `EmpAccount` and `Password`, and
    clicks the button with id `ADSubmit_m`.
    """
    # Navigate to login page first
    driver.get(LOGIN_URL)
    print(f"自動填入帳密並嘗試登入：{LOGIN_URL}")

    # Wait for input elements to be visible and interactable
    wait = WebDriverWait(driver, 20)
    account_el = wait.until(EC.visibility_of_element_located((By.ID, "EmpAccount")))
    password_el = wait.until(EC.visibility_of_element_located((By.ID, "Password")))

    # Try to send keys; if element not interactable (hidden/overlaid), fallback to JS assignment
    try:
        account_el.clear()
        account_el.send_keys(username)
    except Exception:
        # fallback: directly set value via JS and fire input events
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

    # Click submit button; prefer element_to_be_clickable but fallback to JS click
    try:
        submit_btn = wait.until(EC.element_to_be_clickable((By.ID, "ADSubmit_m")))
        submit_btn.click()
    except Exception:
        # If click fails (element not interactable / overlay), try JS click
        try:
            btn = driver.find_element(By.ID, "ADSubmit_m")
            driver.execute_script("arguments[0].click();", btn)
        except Exception as exc:
            # Re-raise with context for caller to handle
            raise

    # Wait for navigation / ready state
    WebDriverWait(driver, 30).until(lambda d: d.execute_script("return document.readyState") == "complete")
    WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.TAG_NAME, "body")))


def goto_travel_page(driver: webdriver.Chrome) -> None:
    """Navigate to the travel application page and wait for it to finish loading."""
    print(f"前往出差申請頁面：{TARGET_URL}")
    driver.get(TARGET_URL)

    # Wait for the DOM to be ready and body present.
    WebDriverWait(driver, 30).until(
        lambda d: d.execute_script("return document.readyState") == "complete"
    )
    WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
    print("頁面載入完成，開始擷取 cookies ...")


def collect_cookie_data(driver: webdriver.Chrome) -> Tuple[str, Dict[str, str]]:
    """Return a raw cookie string and a name->value mapping."""
    cookies = driver.get_cookies()
    cookie_map = {cookie["name"]: cookie["value"] for cookie in cookies}
    cookie_pairs = [f"{name}={value}" for name, value in cookie_map.items()]
    cookie_string = "; ".join(cookie_pairs)
    return cookie_string, cookie_map


def persist_cookies(cookie_string: str, cookie_map: Dict[str, str]) -> None:
    """Persist cookies to .env_cookie for later reuse."""
    ENV_PATH.touch(exist_ok=True)
    set_key(str(ENV_PATH), "TRAVEL_COOKIE_STRING", cookie_string)

    for name in IMPORTANT_COOKIES:
        value = cookie_map.get(name)
        if not value:
            continue
        env_key = f"COOKIE_{name.replace('.', '_').upper()}"
        set_key(str(ENV_PATH), env_key, value)

    print(f"已寫入 cookies 至 {ENV_PATH}")
    print("TRAVEL_COOKIE_STRING 可直接用於後續的 requests，其他欄位則為常用單獨 cookie。")


def main(interactive: bool = True, username: str | None = None, password: str | None = None) -> None:
    """Entry point to launch browser and capture cookies.

    Parameters
    - interactive: when True (default), open login page and wait for user to press Enter.
      When False, the function will attempt to read credentials from parameters or
      environment variables and perform automated login.
    - username/password: optional overrides for automated login. If not provided
      and interactive is False, values are looked up from env `TRAVEL_EIP_USER` and
      `TRAVEL_EIP_PASS`.
    """
    load_dotenv()

    # Determine credentials for automated flow
    if not interactive:
        u = username or os.getenv("TRAVEL_EIP_USER")
        p = password or os.getenv("TRAVEL_EIP_PASS")
        if not u or not p:
            raise RuntimeError("自動登入時需提供 TRAVEL_EIP_USER / TRAVEL_EIP_PASS 或傳入 username/password")

    driver = launch_browser()

    try:
        if interactive:
            wait_for_manual_login(driver)
        else:
            auto_login(driver, u, p)

        goto_travel_page(driver)
        cookie_string, cookie_map = collect_cookie_data(driver)
        persist_cookies(cookie_string, cookie_map)
    except Exception as exc:  # noqa: BLE001
        print(f"[錯誤] 擷取 cookie 時發生例外：{exc}")
    finally:
        print("關閉瀏覽器 ...")
        driver.quit()


if __name__ == "__main__":
    main()
