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
    # 基本隱藏欄位
    payload = {
        "__EVENTTARGET": "ctl00$ContentPlaceHolder1$btnEdit",
        "__EVENTARGUMENT": "",
        "__VIEWSTATE": soup.find('input', {'name': '__VIEWSTATE'})['value'],
        "__VIEWSTATEGENERATOR": soup.find('input', {'name': '__VIEWSTATEGENERATOR'})['value'],
        "__EVENTVALIDATION": soup.find('input', {'name': '__EVENTVALIDATION'})['value'],
        "ctl00$ContentPlaceHolder1$txb_StDay": year_month,
    }
    
    days_in_month = calendar.monthrange(year, month)[1]
    work_days_list = []
    holidays_list = []

    for day in range(1, days_in_month + 1):
        date_obj = datetime.date(year, month, day)
        date_str = date_obj.strftime("%Y%m%d")
        is_workday = date_obj.weekday() < 5
        
        # 取得該日期的工時設定（如果有）
        day_config = work_times.get(date_str, {})
        
        # 欄位填寫
        payload[f"ctl00$ContentPlaceHolder1$txtArr_{date_str}"] = day_config.get('arrival_time', '')
        payload[f"ctl00$ContentPlaceHolder1$txtLev_{date_str}"] = day_config.get('leave_time', '')
        payload[f"ctl00$ContentPlaceHolder1$Dp_{date_str}"] = day_config.get('reason', '')
        payload[f"ctl00$ContentPlaceHolder1$txtR_{date_str}"] = day_config.get('remark', '')
        
        if is_workday: work_days_list.append(date_str)
        else: holidays_list.append(date_str)
            
    payload["ctl00$ContentPlaceHolder1$HidWkHCtrl"] = ";".join(holidays_list)
    payload["ctl00$ContentPlaceHolder1$HidWkACtrl"] = ";".join(work_days_list)
    payload["ctl00$ContentPlaceHolder1$HideStTimes"] = ""
    payload["ctl00$ContentPlaceHolder1$HidEdTimes"] = ""
    
    return payload

def submit_work_time(cookies: Optional[Dict[str, Any]] = None, **params) -> Dict[str, Any]:
    """
    提交工時的具體實作
    """
    try:
        # 支援直接傳入 work_times 字典 (由 AutoScheduler 使用)
        # 或從 LLM 回應解析 (目前 submit_work_time.py 原本的邏輯)
        work_times = params.get("work_times", {})
        
        # 如果沒提供 work_times，可能需要解析 llm_response (這裡保留擴展性)
        if not work_times and "response" in params:
             # TODO: 解析 LLM 回應內容轉為 work_times 字典
             pass

        now = datetime.datetime.now()
        target_year_month = f"{now.year}/{now.month:02d}"
        
        session = requests.Session()
        headers = {
            "User-Agent": get_dynamic_user_agent(),
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
        resp = session.get(BASE_TIMESHEET_URL, headers=headers, timeout=20)
        if resp.status_code != 200:
            return {"status": "error", "message": f"無法存取網頁 (HTTP {resp.status_code})"}
        
        soup = BeautifulSoup(resp.text, 'html.parser')
        if not soup.find('input', {'name': '__VIEWSTATE'}):
            return {"status": "auth_failed", "message": "認證無效，請重新登入。"}
        
        # 2. 準備 Payload
        payload = generate_form_payload(target_year_month, work_times, soup)
        
        # 3. 執行 POST 提交
        post_resp = session.post(BASE_TIMESHEET_URL, data=payload, headers=headers, allow_redirects=False)
        
        # 成功標誌：302 重定向到其他頁面 (通常是 Home 或原頁面)
        if post_resp.status_code in [302, 200]:
            return {
                "status": "success",
                "message": f"工時已提交 ({target_year_month})",
                "details": {"count": len(work_times)}
            }
        else:
            return {"status": "error", "message": f"提交失敗 (HTTP {post_resp.status_code})"}
        
    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return {
            "status": "error",
            "message": f"提交工時時發生意外錯誤: {str(e)}"
        }
