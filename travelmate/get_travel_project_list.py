#!/usr/bin/env python3
"""
Fetch Context.ProjectCode from the travel apply page and save to project_list.json.
Requires cookies in .env_cookie (TRAVEL_COOKIE_STRING or individual cookie fields).
"""
from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Dict, List

import requests
from dotenv import load_dotenv

ENV_COOKIE_PATH = Path(__file__).resolve().parent / ".env_cookie"
PROJECT_LIST_PATH = Path(__file__).resolve().parent / "project_list.json"
TARGET_URL = "https://expapply.iii.org.tw/expApply/Apply/DC.aspx"
COOKIE_ENV_KEYS = ("clientUserName", "clientTicket", "ASP.NET_SessionId")


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


def extract_project_code_list(html: str) -> List[Dict[str, str]]:
    pattern = r"Context\.ProjectCode\s*=\s*JSON\.parse\('(?P<data>.*?)'\);"
    match = re.search(pattern, html, flags=re.DOTALL)
    if not match:
        raise RuntimeError("無法在回應中找到 Context.ProjectCode")
    raw = match.group("data")
    # Try direct JSON decode; if fails, attempt to unescape.
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        unescaped = raw.encode("utf-8").decode("unicode_escape")
        return json.loads(unescaped)


def fetch_project_list() -> List[Dict[str, str]]:
    cookie_string = load_cookie_string()
    session = requests.Session()
    session.headers.update(
        {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/131.0.0.0 Safari/537.36"
            ),
            "Content-Type": "text/html; charset=UTF-8",
        }
    )
    session.cookies.update(cookie_str_to_dict(cookie_string))

    resp = session.get(TARGET_URL, timeout=15)
    resp.raise_for_status()
    return extract_project_code_list(resp.text)


def main() -> None:
    try:
        projects = fetch_project_list()
    except Exception as exc:  # noqa: BLE001
        raise SystemExit(f"取得 ProjectCode 失敗：{exc}") from exc

    PROJECT_LIST_PATH.write_text(json.dumps(projects, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"已將 {len(projects)} 筆專案資料寫入 {PROJECT_LIST_PATH}")


if __name__ == "__main__":
    main()
