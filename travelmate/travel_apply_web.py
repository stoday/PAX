#!/usr/bin/env python3
"""
Automate sending the travel application POST request.
Loads cookies (and optional payload overrides) from .env_cookie.
"""
from __future__ import annotations

import json
import os
from copy import deepcopy
from pathlib import Path
from typing import Dict

import requests
from dotenv import load_dotenv


# Target endpoint for saving the travel application.
SAVE_URL = "https://expapply.iii.org.tw/expApply/Apply/DC.aspx/SaveDC"

# Readable default payload (Python objects); converted to JSON strings when sending.
DEFAULT_PAYLOAD = {
    "BasicData": {
        "FORM_TYPE": "DC",
        "APY_EMP": "970123",
        "APY_NAME": "宋經天",
        "APY_DEPT": "R0",
        "APY_DEPT_NAME": "數轉院",
        "FILL_EMP": "970123",
        "FILL_NAME": "宋經天",
        "FILL_DEPT": "R0",
        "FILL_DEPT_NAME": "",
        "ORG_FORMID": "",
        "FORMID": "",
        "PREPAYMENT": "N",
        "ACC_AMT": 0,
        "REASON": "宋經天 2025/12/11 至  2025/12/11 出差至 xxx",
        "IS_DISPATCH": "0",
        "IS_SUBMIT": "N",
    },
    "InWorkCont": {
        "REASON": "123",
        "APY_NAME": "宋經天",
        "EMP_TITLE": "\n                                               資深工程師\n                                                      \n                                            ",
        "APY_EMPNO": "970123",
        "ADDRESS": "xxx",
        "BDATE": "2025/12/11",
        "EDATE": "2025/12/11",
        "OUTDAYS": "1",
        "PROJID": "A4NASW10",
        "ALL_PROJID_CHK": "Y",
        "NO_PROJID_CHK": "Y",
        "NO_PROJID_DESC": "",
        "COMMENTS": "",
    },
    "InWorkDrive": [],
    "InWorkRoute": [
        {
            "NUMBER": 1,
            "SOURCE": "R",
            "UUID": "<uuid, empty for unknown>",
            "FORMID": "",
            "ORD": 0,
            "BDATE": "2025/12/11",
            "MOVER": "Y",
            "MOVER_NAME": "<mover_name, ex: 計程車>",
            "MOVER_OTHER": "",
            "BPLACE": "<begin_location>",
            "EPLACE": "<end_location>",
            "REASON": "<reason_for_taxi>",
            "PRICE": "<price>",
            "PRICE_FMT": "<price>",
            "ACTYEAR": 2025,
            # "PROJID": "A4NASW10",
            "PROJID": "",
            # "PROJID_NAME": "A4NASW10_新創IA智慧混合實境系統平台計畫(3/4) 2025/12/31_補助",
            # 讀取 project_list.json 時會自動帶入
            "PROJID_NAME": "",
            "VALID_FLAG": "1",
            "UD_ADD": "Y",
        }
    ],
    "ApplyItem": [
        {
            "NUMBER": 1,
            "SOURCE": "R",
            "UUID": "c7f23d3f-c5cc-4b5b-bfce-191cf1e5c484",
            "ORD": 0,
            "ITEM_NAME": "計程車資",
            "DESC1": "<begin_location> - <end_location>",
            "REASON": "<reason_for_taxi>",
            "ACTNAME": "旅運費",
            "ESTPRICE": "<price>",
            "ESTPRICE_FMT": "<price>",
            "ACTYEAR": 2025,
            "PROJID": "",
            "PROJID_NAME": "",
        },
        {
            "NUMBER": 2,
            "SOURCE": "A",
            "UUID": "2ee0fb60-b910-4000-8000-000000000000",
            "FORMID": "",
            "ORD": 0,
            "ITEM_NAME": "雜費",
            "DESC1": "每日上限為 400 元",
            "REASON": None,
            "ACTNAME": "旅運費",
            "ACTYEAR": 2025,
            "PROJID": "A4NASW10",
            # "PROJID_NAME": "A4NASW10_新創IA智慧混合實境系統平台計畫(3/4) 2025/12/31_補助",
            "PROJID_NAME": "",
            "ESTPRICE": 400,
            "ESTPRICE_FMT": "400",
        },
    ],
    "prepay": {"feetype": "", "feereason": "", "PrePay2": [], "PrePay3": []},
    "SignData": [],
    "ChgInfo": {},
    "AppData": {"IS_SUBMIT": "N"},
}

ENV_COOKIE_PATH = Path(__file__).resolve().parent / ".env_cookie"
COOKIE_ENV_KEYS = ("clientUserName", "clientTicket", "ASP.NET_SessionId")


def cookie_str_to_dict(raw: str) -> Dict[str, str]:
    """Convert a raw 'k=v; k2=v2' cookie string to a dict."""
    pairs = [item.strip() for item in raw.split(";") if item.strip()]
    cookies: Dict[str, str] = {}
    for pair in pairs:
        if "=" not in pair:
            continue
        key, value = pair.split("=", 1)
        cookies[key.strip()] = value.strip()
    return cookies


def load_cookie_string(env_path: Path = ENV_COOKIE_PATH) -> str:
    """Load cookie string from .env_cookie."""
    load_dotenv(env_path, override=False)
    cookie_string = os.getenv("TRAVEL_COOKIE_STRING")
    if cookie_string:
        return cookie_string

    # Fallback: build from individual cookie values if present.
    pieces = []
    for name in COOKIE_ENV_KEYS:
        env_key = f"COOKIE_{name.replace('.', '_').upper()}"
        value = os.getenv(env_key)
        if value:
            pieces.append(f"{name}={value}")
    if pieces:
        return "; ".join(pieces)

    raise RuntimeError("找不到 TRAVEL_COOKIE_STRING，請先執行 get_travel_web_cookie.py 取得 cookies。")


def load_payload(env_path: Path = ENV_COOKIE_PATH) -> Dict[str, str]:
    """
    Load payload from .env_cookie if provided; otherwise use readable defaults.
    """
    load_dotenv(env_path, override=False)
    payload_str = os.getenv("TRAVEL_PAYLOAD")
    if not payload_str:
        payload_obj = deepcopy(DEFAULT_PAYLOAD)
        # Backend expects stringified JSON for nested fields; convert uniformly.
        return {
            key: json.dumps(value, ensure_ascii=False)
            if isinstance(value, (dict, list))
            else value
            for key, value in payload_obj.items()
        }

    try:
        data = json.loads(payload_str)
        if not isinstance(data, dict):
            raise ValueError("TRAVEL_PAYLOAD 必須是 JSON 物件")
        return data  # type: ignore[return-value]
    except json.JSONDecodeError as exc:  # noqa: F841
        raise RuntimeError("TRAVEL_PAYLOAD 不是有效的 JSON 字串，請檢查 .env_cookie。") from exc


def submit_application(
    *,
    url: str = SAVE_URL,
    payload: Dict[str, str] | None = None,
    cookie_string: str | None = None,
    timeout: int = 15,
) -> requests.Response:
    """
    Send the captured payload to the travel application endpoint.

    Returns the raw Response object so callers can inspect status/text/JSON.
    """
    payload_to_send = payload or load_payload()
    cookie_str = cookie_string or load_cookie_string()

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
    session.cookies.update(cookie_str_to_dict(cookie_str))

    response = session.post(url, json=payload_to_send, timeout=timeout)
    response.raise_for_status()
    return response


def main() -> None:
    """
    Run the submission once and print the server reply.

    Note: This will perform a real POST to the remote system. Make sure the
    .env_cookie is present and up to date before running.
    """
    try:
        resp = submit_application()
    except Exception as exc:  # noqa: BLE001
        # Fail fast with a readable message.
        raise SystemExit(f"Request failed: {exc}") from exc

    print(f"Status: {resp.status_code}")
    try:
        print("Body:", json.dumps(resp.json(), ensure_ascii=False, indent=2))
    except ValueError:
        print("Body:", resp.text)


if __name__ == "__main__":
    main()
