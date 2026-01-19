# -*- coding: utf-8 -*-
import os
import json
import requests
import sys
from bs4 import BeautifulSoup
from typing import Dict, Any, Optional
from .utils import get_dynamic_user_agent, get_dynamic_platform_info, get_auth_cookies

FORM_URL = "https://expapply.iii.org.tw/expApply/Apply/DC.aspx"

def fetch_emp_projects(session, empno: str, sdate: str, edate: str, dept: str = "") -> Dict[str, Any]:
    url = "https://expapply.iii.org.tw/expApply/Commons.asmx/GetEmpProject"
    
    def _normalize_ymd(date_str: str) -> str:
        if not date_str: return ""
        return date_str.replace("-", "/") if "-" in date_str else date_str

    payload = {
        "model": {
            "FORM_TYPE": "DC",
            "DEPT": dept,
            "EMPNO": empno,
            "SDATE": _normalize_ymd(sdate),
            "EDATE": _normalize_ymd(edate),
            "FORMID": "",
        }
    }
    
    headers = {
        "Content-Type": "application/json; charset=utf-8",
        "X-Requested-With": "XMLHttpRequest",
    }

    try:
        resp = session.post(url, json=payload, headers=headers, timeout=15)
        data = resp.json()
        if "d" in data:
            inner = data["d"]
            items = json.loads(inner) if isinstance(inner, str) else inner
            return {"projects": items}
    except:
        pass
    return {"projects": []}

def apply_travel(cookies: Optional[Dict[str, Any]] = None, **params) -> Dict[str, Any]:
    """
    出差申請的具體實作
    """
    try:
        # 取得傳入的 InWorkRoute
        in_work_route = params.get("InWorkRoute", [])
        if not in_work_route and "route" in params:
            in_work_route = params.get("route", [])
            
        session = requests.Session()
        auth_cookies = get_auth_cookies()
        if cookies: auth_cookies.update(cookies)
        
        for name, value in auth_cookies.items():
            if value: session.cookies.set(name, value, domain='expapply.iii.org.tw')

        user_agent = get_dynamic_user_agent()
        headers = {"User-Agent": user_agent}
        
        # 1. 存取表單頁面取得隱藏欄位
        resp = session.get(FORM_URL, headers=headers, timeout=20)
        if "Login.aspx" in resp.url:
            return {"status": "auth_failed", "message": "認證失效，請重新登入。"}
            
        soup = BeautifulSoup(resp.text, 'html.parser')
        viewstate = soup.find('input', {'name': '__VIEWSTATE'})
        if not viewstate:
            return {"status": "auth_failed", "message": "無法取得表單資訊，可能需要重新登入。"}

        # 2. 取得使用者資訊 (模擬 AJAX)
        emp_no = os.getenv("CLIENT_USERNAME", "")
        user_info = {}
        try:
            api_url = "https://expapply.iii.org.tw/expApply/ashx/Common.ashx?action=SearchEmployee"
            api_resp = session.post(api_url, json={"F_DeptNo": "", "KeyWord": emp_no}, headers=headers)
            user_data = api_resp.json().get("Data", [])
            if user_data: user_info = user_data[0]
        except: pass

        apy_emp = user_info.get('EMPNO', emp_no)
        apy_name = user_info.get('Name', '')
        apy_dept = user_info.get('DEPTNO', '')
        apy_dept_name = user_info.get('SHORT_DESCR', '')

        # 3. 計算日期範圍與專案
        from datetime import datetime
        route_dates = []
        for r in in_work_route:
            d_str = r.get("BDATE", "")
            try:
                route_dates.append(datetime.strptime(d_str.replace("-", "/"), "%Y/%m/%d"))
            except: pass
        
        bdate = min(route_dates).strftime("%Y/%m/%d") if route_dates else ""
        edate = max(route_dates).strftime("%Y/%m/%d") if route_dates else ""
        outdays = str((max(route_dates) - min(route_dates)).days + 1) if route_dates else "0"

        # 取得專案
        projid = ""
        projid_name = ""
        if apy_emp and bdate:
            proj_data = fetch_emp_projects(session, apy_emp, bdate, edate, apy_dept)
            projects = proj_data.get("projects", [])
            if projects:
                projid = projects[-1].get("PROJECTNO", "")
                projid_name = projects[-1].get("PROJECTNAME", "")

        # 4. 構建 Payload
        apply_items = []
        for idx, r in enumerate(in_work_route, 1):
            mover_name = r.get("MOVER_NAME", "交通費")
            apply_items.append({
                "NUMBER": idx,
                "SOURCE": "R",
                "ITEM_NAME": "計程車資" if mover_name == "計程車" else f"交通費_{mover_name}",
                "DESC1": f"{r.get('BPLACE','')}-{r.get('EPLACE','')}",
                "REASON": r.get("REASON", ""),
                "ACTNAME": "旅運費",
                "ESTPRICE": r.get("PRICE", 0),
                "ESTPRICE_FMT": str(r.get("PRICE", 0)),
                "ACTYEAR": r.get("ACTYEAR", datetime.now().year),
                "PROJID": projid,
                "PROJID_NAME": projid_name
            })
            
        # 雜費
        apply_items.append({
            "NUMBER": len(apply_items) + 1,
            "SOURCE": "A",
            "ITEM_NAME": "雜費",
            "DESC1": "每日上限為 400 元",
            "ACTNAME": "旅運費",
            "ESTPRICE": 400,
            "ESTPRICE_FMT": "400",
            "PROJID": projid,
            "PROJID_NAME": projid_name
        })

        payload = {
            "AppData": {"IS_SUBMIT": "N"},
            "BasicData": {
                "FORM_TYPE": "DC", "APY_EMP": apy_emp, "APY_NAME": apy_name,
                "FILL_EMP": apy_emp, "FILL_NAME": apy_name, "APY_DEPT": apy_dept,
                "APY_DEPT_NAME": apy_dept_name, "IS_SUBMIT": "N"
            },
            "InWorkCont": {
                "APY_NAME": apy_name, "APY_EMPNO": apy_emp, "BDATE": bdate, "EDATE": edate,
                "OUTDAYS": outdays, "PROJID": projid, "ALL_PROJID_CHK": "N", "NO_PROJID_CHK": "N"
            },
            "ApplyItem": apply_items,
            "InWorkRoute": in_work_route,
            "SignData": [], "InWorkDrive": [], "ChgInfo": {}, 
            "prepay": {"feetype": "", "feereason": "", "PrePay2": [], "PrePay3": []}
        }

        # 密封為 ASP.NET 格式
        final_payload = {k: json.dumps(v, ensure_ascii=False) for k, v in payload.items()}
        final_payload['__VIEWSTATE'] = viewstate['value']
        final_payload['__VIEWSTATEGENERATOR'] = soup.find('input', {'name': '__VIEWSTATEGENERATOR'})['value']

        # 5. 送出暫存
        save_url = "https://expapply.iii.org.tw/expApply/Apply/DC.aspx/SaveDC"
        save_headers = {
            "User-Agent": user_agent,
            "Content-Type": "application/json; charset=UTF-8",
            "X-Requested-With": "XMLHttpRequest",
            "Referer": FORM_URL
        }
        
        save_resp = session.post(save_url, json=final_payload, headers=save_headers)
        
        print(f"[Debug] Travel apply status: {save_resp.status_code}", file=sys.stderr)
        
        return {
            "status": "success",
            "message": "出差申請單已成功暫存，請至系統確認。",
            "details": {"projid": projid, "items": len(apply_items)}
        }
        
    except Exception as e:
        import traceback
        print(traceback.format_exc(), file=sys.stderr)
        return {"status": "error", "message": f"出差申請失敗: {str(e)}"}
