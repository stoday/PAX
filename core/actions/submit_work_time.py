# -*- coding: utf-8 -*-
import calendar
import datetime
import os
import sys
import requests
from bs4 import BeautifulSoup
from typing import Dict, Any, Optional, List
from .utils import get_dynamic_user_agent, get_dynamic_platform_info, get_auth_cookies

BASE_TIMESHEET_URL = "https://hrwt.iii.org.tw/TSM/MyWorkTime.aspx"

def generate_form_payload(year_month: str, work_times: Dict[str, Any], soup: BeautifulSoup) -> Dict[str, str]:
    """生成表單 POST Payload"""
    year, month = map(int, year_month.split('/'))
    
    # 取得 ASP.NET 隱藏欄位，並加上安全檢查
    def get_val(name):
        tag = soup.find('input', {'name': name})
        return tag['value'] if tag and 'value' in tag.attrs else ""

    # 基本隱藏欄位
    payload = {
        "__EVENTTARGET": "ctl00$ContentPlaceHolder1$btnEdit",
        "__EVENTARGUMENT": "",
        "__VIEWSTATE": get_val('__VIEWSTATE'),
        "__VIEWSTATEGENERATOR": get_val('__VIEWSTATEGENERATOR'),
        "__EVENTVALIDATION": get_val('__EVENTVALIDATION'),
        "ctl00$ContentPlaceHolder1$txb_StDay": year_month,
    }
    
    # 如果關鍵欄位都沒抓到，代表頁面不正確
    if not payload["__VIEWSTATE"]:
        return None
    
    days_in_month = calendar.monthrange(year, month)[1]
    work_days_with_reason = []
    work_days_without_reason = []
    holidays_list = []

    for day in range(1, days_in_month + 1):
        date_obj = datetime.date(year, month, day)
        date_str = date_obj.strftime("%Y%m%d")
        is_workday = date_obj.weekday() < 5
        
        # --- 讀取現有值 ---
        def get_existing(prefix):
            # 嘗試找 input[value] 或 select > option[selected]
            name = f"ctl00$ContentPlaceHolder1${prefix}_{date_str}"
            tag = soup.find(['input', 'select'], {'name': name})
            if not tag: return ""
            
            if tag.name == 'input':
                return tag.get('value', '')
            elif tag.name == 'select':
                opt = tag.find('option', selected=True)
                return opt.get('value', '') if opt else ""
            return ""

        existing_arr = get_existing("txtArr")
        existing_lev = get_existing("txtLev")
        existing_reason = get_existing("Dp")
        existing_remark = get_existing("txtR")

        # --- 決定最終填寫值 (有傳入則覆蓋，否則保留現有值) ---
        day_config = work_times.get(date_str, {})
        arrival = day_config.get('arrival_time', existing_arr)
        leave = day_config.get('leave_time', existing_lev)
        reason = day_config.get('reason', existing_reason)
        remark = day_config.get('remark', existing_remark)
        
        # 欄位填寫
        payload[f"ctl00$ContentPlaceHolder1$txtArr_{date_str}"] = arrival
        payload[f"ctl00$ContentPlaceHolder1$txtLev_{date_str}"] = leave
        payload[f"ctl00$ContentPlaceHolder1$Dp_{date_str}"] = reason
        payload[f"ctl00$ContentPlaceHolder1$txtR_{date_str}"] = remark
        
        if not is_workday:
            holidays_list.append(date_str)
        else:
            # 如果有填報工時且有原因，歸類到 ACtrl；否則歸類到 Ctrl
            if reason:
                work_days_with_reason.append(date_str)
            else:
                work_days_without_reason.append(date_str)
            
    payload["ctl00$ContentPlaceHolder1$HidWkHCtrl"] = ";".join(holidays_list)
    payload["ctl00$ContentPlaceHolder1$HidWkACtrl"] = ";".join(work_days_with_reason)
    payload["ctl00$ContentPlaceHolder1$HidWkCtrl"] = ";".join(work_days_without_reason)
    payload["ctl00$ContentPlaceHolder1$HidStTimes"] = ""
    payload["ctl00$ContentPlaceHolder1$HidEdTimes"] = ""
    
    # Debug: 計算實際上填了幾天的工時 (包含原本就有的)
    filled_days = [k for k, v in payload.items() if "txtArr_" in k and v]
    print(f"[Debug] Payload generated: {len(filled_days)} days total in payload.", file=sys.stderr)
    
    return payload

def submit_work_time(cookies: Optional[Dict[str, Any]] = None, **params) -> Dict[str, Any]:
    """
    提交工時的具體實作
    """
    try:
        # 取得傳入參數
        work_times = params.get("work_times", {})
        
        # 強健性處理：如果 LLM 回傳的是 List 而非 Dict，嘗試轉換它
        if isinstance(work_times, list):
            new_work_times = {}
            for item in work_times:
                if isinstance(item, dict):
                    # 嘗試抓取日期欄位 (可能是 'date' 或 'YYYY-MM-DD' 格式的 Key)
                    date_key = item.get("date") or item.get("日期")
                    if date_key:
                        # 標準化日期格式：移除 - 或 /，確保變成 YYYYMMDD
                        normalized_key = str(date_key).replace("-", "").replace("/", "")
                        new_work_times[normalized_key] = item
                    elif len(item.keys()) > 0:
                        # 如果沒有明確日期欄位，但第一個 Key 看起來像日期 (YYYY-MM-DD)
                        first_key = list(item.keys())[0]
                        if "-" in first_key or "/" in first_key:
                            normalized_key = str(first_key).replace("-", "").replace("/", "")
                            new_work_times[normalized_key] = item[first_key]
                        else:
                            new_work_times[first_key] = item[first_key]
            work_times = new_work_times
            print(f"[Debug] Normalized work_times keys: {list(work_times.keys())}", file=sys.stderr)

        # 支援直接傳入 work_times 字典 (由 AutoScheduler 使用)
        if not work_times and "response" in params:
             # TODO: 解析 LLM 回應內容轉為 work_times 字典
             pass

        now = datetime.datetime.now()
        target_year_month = f"{now.year}/{now.month:02d}"
        
        session = requests.Session()
        ua = get_dynamic_user_agent()
        platform_info = get_dynamic_platform_info()
        
        headers = {
            "User-Agent": ua,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Referer": BASE_TIMESHEET_URL,
            "Origin": "https://hrwt.iii.org.tw"
        }
        
        # 設定 Cookie
        auth_cookies = get_auth_cookies()
        if cookies: auth_cookies.update(cookies)
        
        for name, value in auth_cookies.items():
            if value: session.cookies.set(name, value, domain='hrwt.iii.org.tw')
            
        # 1. 獲取頁面隱藏欄位
        resp = session.get(BASE_TIMESHEET_URL, headers=headers, timeout=20, allow_redirects=False)
        # 強制指定編碼，避免 requests 誤判 (III 系統有時是 Big5 但 Header 沒寫清楚)
        # 但通常現代網頁是 utf-8，我們先嘗試 apparent_encoding
        resp.encoding = resp.apparent_encoding or "utf-8"
        
        if resp.status_code == 302 or "Login.aspx" in resp.url:
            return {"status": "auth_failed", "message": "認證無效，網頁已被重定向至登入頁面。"}
        
        if resp.status_code != 200:
            return {"status": "error", "message": f"無法存取網頁 (HTTP {resp.status_code})"}
        
        soup = BeautifulSoup(resp.text, 'html.parser')
        if not soup.find('input', {'name': '__VIEWSTATE'}):
            return {"status": "auth_failed", "message": "認證無效，無法取得網頁狀態欄位。"}
        
        # 2. 準備 Payload
        payload = generate_form_payload(target_year_month, work_times, soup)
        if payload is None:
            return {"status": "auth_failed", "message": "無法從網頁抓取必要欄位，可能是認證失效。"}
        
        # 3. 執行 POST 提交 (包含 YM 參數以確保目標月份正確)
        from urllib.parse import quote
        from core.logger import get_pax_logger
        logger = get_pax_logger()
        
        submit_url = f"{BASE_TIMESHEET_URL}?YM={quote(target_year_month)}"
        # 更新 Referer 確保包含 YM 參數
        headers["Referer"] = submit_url
        logger.log(f"正在提交工時至: {submit_url}")
        
        post_resp = session.post(submit_url, data=payload, headers=headers, allow_redirects=False)
        
        # 成功標誌：302 重定向到其他頁面 (通常是 Home 或原頁面)
        if post_resp.status_code in [302, 200]:
            logger.log(f"工時提交成功! 狀態碼: {post_resp.status_code}")
            if post_resp.status_code == 302:
                logger.log(f"網頁重定向至: {post_resp.headers.get('Location')}")
            
            return {
                "status": "success",
                "message": f"工時已提交 ({target_year_month})",
                "details": {"count": len(work_times)}
            }
        else:
            logger.log(f"工時提交失敗! 狀態碼: {post_resp.status_code}", level="ERROR")
            return {"status": "error", "message": f"提交失敗 (HTTP {post_resp.status_code})"}
        
    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return {
            "status": "error",
            "message": f"提交工時時發生意外錯誤: {str(e)}"
        }
