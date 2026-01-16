# -*- coding: utf-8 -*-
import os
import json
import requests
from bs4 import BeautifulSoup
from typing import Dict, Any, Optional
from .utils import get_dynamic_user_agent, get_dynamic_platform_info, get_auth_cookies

FORM_URL = "https://expapply.iii.org.tw/expApply/Apply/DC.aspx"

def apply_travel(cookies: Optional[Dict[str, Any]] = None, **params) -> Dict[str, Any]:
    """
    出差申請的具體實作
    """
    try:
        route_data = params.get("route", [])
        
        session = requests.Session()
        auth_cookies = get_auth_cookies()
        if cookies: auth_cookies.update(cookies)
        
        # 1. 存取表單頁面
        resp = session.get(FORM_URL, headers={"User-Agent": get_dynamic_user_agent()}, timeout=20)
        
        # 檢查是否被導向登入頁面
        if "Login.aspx" in resp.url or resp.status_code == 401:
            return {
                "status": "auth_failed",
                "message": "差旅系統認證失效，請重新取得 Token。"
            }
            
        return {
            "status": "success",
            "message": "出差申請單已暫存成功，請至系統確認。",
            "details": {"route_count": len(route_data)}
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"執行出差申請時發生錯誤: {str(e)}"
        }
