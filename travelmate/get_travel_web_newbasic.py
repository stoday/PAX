#!/usr/bin/env python3
"""
Fetch the travel application's basic info using cookies from .env_cookie.
Stores the returned fields back into .env_cookie for reuse.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Dict

import requests
from dotenv import load_dotenv, set_key


ENV_COOKIE_PATH = Path(__file__).resolve().parent / ".env_cookie"
TARGET_URL = "https://expapply.iii.org.tw/expApply/Commons.asmx/GetNewBasic"
COOKIE_ENV_KEYS = ("clientUserName", "clientTicket", "ASP.NET_SessionId")
SAVE_KEYS = ("NAME", "DEPTNAME", "DEPTNO", "ORG_DEPTNO", "Telephone")


def cookie_str_to_dict(raw: str) -> Dict[str, str]:
    pairs = [item.strip() for item in raw.split(";") if item.strip()]
    cookies: Dict[str, str] = {}
    for pair in pairs:
        if "=" not in pair:
            continue
        key, value = pair.split("=", 1)
        cookies[key.strip()] = value.strip()
    return cookies


def load_cookie_string(env_path: Path = ENV_COOKIE_PATH) -> str:
    load_dotenv(env_path, override=False)
    cookie_string = os.getenv("TRAVEL_COOKIE_STRING")
    if cookie_string:
        return cookie_string

    pieces = []
    for name in COOKIE_ENV_KEYS:
        env_key = f"COOKIE_{name.replace('.', '_').upper()}"
        value = os.getenv(env_key)
        if value:
            pieces.append(f"{name}={value}")
    if pieces:
        return "; ".join(pieces)

    raise RuntimeError("找不到 TRAVEL_COOKIE_STRING，請先執行 get_travel_web_cookie.py 取得 cookies。")


def persist_basic_info(data: Dict[str, str], env_path: Path = ENV_COOKIE_PATH) -> None:
    env_path.touch(exist_ok=True)
    set_key(str(env_path), "TRAVEL_NEWBASIC_JSON", json.dumps(data, ensure_ascii=False))
    for key in SAVE_KEYS:
        if key in data:
            set_key(str(env_path), f"TRAVEL_{key}", str(data[key]))


def fetch_newbasic() -> Dict[str, str]:
    cookie_string = load_cookie_string()
    session = requests.Session()
    session.headers.update(
        {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/131.0.0.0 Safari/537.36"
            ),
            "Content-Type": "application/json; charset=UTF-8",
        }
    )
    session.cookies.update(cookie_str_to_dict(cookie_string))

    resp = session.post(TARGET_URL, json={})
    resp.raise_for_status()
    payload = resp.json()
    raw_d = payload.get("d")
    if not raw_d:
        raise RuntimeError("回應中沒有欄位 'd'")

    try:
        data = json.loads(raw_d)
    except json.JSONDecodeError as exc:  # noqa: F841
        raise RuntimeError("無法解析回應中的 d 欄位，非有效 JSON") from exc

    if not isinstance(data, dict):
        raise RuntimeError("d 欄位不是物件格式，無法存入 .env_cookie")

    persist_basic_info(data)
    return data  # type: ignore[return-value]


def main() -> None:
    try:
        data = fetch_newbasic()
    except Exception as exc:  # noqa: BLE001
        raise SystemExit(f"取得資料失敗：{exc}") from exc

    print("取得的新基本資料：")
    print(json.dumps(data, ensure_ascii=False, indent=2))
    print(f"已寫入 {ENV_COOKIE_PATH}")


if __name__ == "__main__":
    main()
