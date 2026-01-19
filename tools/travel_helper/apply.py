from mcp.server.fastmcp import FastMCP  # noqa: E402
import requests
import json
import platform
import sys
import os
from urllib.parse import quote
from bs4 import BeautifulSoup
import dotenv
dotenv.load_dotenv()

mcp = FastMCP("dc_apply")

def get_dynamic_platform_info():
    """根據當前系統生成平台資訊"""
    system = platform.system()
    if system == "Darwin":
        return '"macOS"'
    elif system == "Windows":
        return '"Windows"'
    elif system == "Linux":
        return '"Linux"'
    else:
        return '"Unknown"'


def get_dynamic_user_agent():
    """根據當前系統環境動態生成 User-Agent"""
    system = platform.system()
    system_version = platform.release()
    
    # 嘗試使用更真實的系統版本資訊
    if system == "Darwin":  # macOS
        try:
            mac_version = platform.mac_ver()[0]
            # 將 macOS 版本格式化為正確格式 (例: 10.15.7 -> 10_15_7)
            formatted_version = mac_version.replace('.', '_')
            return f"Mozilla/5.0 (Macintosh; Intel Mac OS X {formatted_version}) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"
        except:
            return "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"
    
    elif system == "Windows":
        try:
            # Windows 版本對應
            version_map = {
                '10': '10.0',
                '11': '10.0',  # Windows 11 仍然報告為 NT 10.0
            }
            win_version = version_map.get(platform.release(), '10.0')
            return f"Mozilla/5.0 (Windows NT {win_version}; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"
        except:
            return "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"
    
    elif system == "Linux":
        return f"Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"
    
    else:
        # 預設回退 User-Agent
        return "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"


def get_post_headers():
    """取得 POST 提交時的完整 headers（根據當前系統環境）"""
    user_agent = get_dynamic_user_agent()
    platform_info = get_dynamic_platform_info()
    
    return {
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "Accept-Language": "zh-TW,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
        "Connection": "keep-alive",
        "Content-Type": "application/json; charset=UTF-8",
        "Host": "expapply.iii.org.tw",
        "Origin": "https://expapply.iii.org.tw",
        "Referer": "https://expapply.iii.org.tw/",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
        "Upgrade-Insecure-Requests": "1",
        "User-Agent": user_agent,
        "sec-ch-ua": '"Microsoft Edge";v="143s", "Chromium";v="143", "Not A(Brand";v="24"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": platform_info
    }
import json
from typing import Any, Dict

def get_user_info(session, headers):
    """
    透過 API 取得當前登入使用者的資訊
    
    Returns:
        dict: 包含使用者資訊的字典
    """
    try:
        # 從 JavaScript 找到的 API endpoint
        # 可以用來搜尋員工，也可以用空條件來取得當前使用者
        api_url = "https://expapply.iii.org.tw/expApply/ashx/Common.ashx?action=SearchEmployee"
        
        # 準備 API headers（JSON 請求）
        api_headers = headers.copy()
        api_headers.update({
            "Content-Type": "application/json; charset=utf-8",
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "X-Requested-With": "XMLHttpRequest",  # 標示為 AJAX 請求
        })
        
        # 使用空條件搜尋（通常會返回當前使用者或其部門的員工）
        payload = {
            "F_DeptNo": "",  # 空白表示不限部門
            "KeyWord": os.getenv("CLIENT_USERNAME", "260107") #"260107"#"970123"     # 空白表示不限關鍵字
        }
        
        print("[cyan]正在取得使用者資訊...[/cyan]", file=sys.stderr)
        resp = session.post(api_url, json=payload, headers=api_headers, timeout=10)
        
        if resp.status_code == 200:
            result = resp.json()
            if result.get("Succ") and result.get("Data"):
                # 通常第一個就是當前使用者
                user_data = result["Data"]
                if isinstance(user_data, list) and len(user_data) > 0:
                    print(f"[green]✓ 成功取得使用者資訊: {user_data[0].get('Name', 'N/A')} ({user_data[0].get('EMPNO', 'N/A')})[/green]", file=sys.stderr)
                    return user_data[0]
                else:
                    print("[yellow]API 回應為空[/yellow]", file=sys.stderr)
            else:
                print(f"[yellow]API 回應格式異常: {result}[/yellow]", file=sys.stderr)
        else:
            print(f"[yellow]取得使用者資訊失敗，狀態碼: {resp.status_code}[/yellow]", file=sys.stderr)
            print(f"[yellow]回應內容: {resp.text[:200]}[/yellow]", file=sys.stderr)
    
    except Exception as e:
        print(f"[yellow]取得使用者資訊時發生錯誤: {e}[/yellow]", file=sys.stderr)
    
    return None

def fetch_emp_projects(empno: str, sdate: str, edate: str, dept: str = "", form_type: str = "DC", formid: str = "") -> Dict[str, Any]:
    """
    呼叫 GetEmpProject 取得專案清單。

    Args:
        empno: 由前面取得的使用者 EMPNO
        sdate: 開始日期（字串，格式依後端需求）
        edate: 結束日期（字串，格式依後端需求）
        dept: 部門代碼（可選）
        form_type: 表單類型，預設 "DC"
        formid: 表單編號（可選）

    Returns:
        {
            "status_code": int,
            "projects": [{"PROJECTNO": "", "PROJECTNAME": ""}, ...],
            "raw_count": int
        }
    """
    url = "https://expapply.iii.org.tw/expApply/Commons.asmx/GetEmpProject"

    # 正規化日期格式為 yyyy/mm/dd
    def _normalize_ymd(date_str: str) -> str:
        if not date_str:
            return ""
        if "/" in date_str:
            return date_str
        if "-" in date_str:
            return date_str.replace("-", "/")
        return date_str

    sdate = _normalize_ymd(sdate)
    edate = _normalize_ymd(edate)

    session = requests.Session()

    cookie_values = {
        "ASP.NET_SessionId": os.getenv("ASP_NET_SESSION_ID", ""),
        "clientTicket": os.getenv("CLIENT_TICKET", ""),
        "clientUserName": os.getenv("CLIENT_USERNAME", ""),
    }
    for name, value in cookie_values.items():
        if value:
            session.cookies.set(
                name=name,
                value=value,
                domain="expapply.iii.org.tw",
                path="/",
                secure=True,
            )

    headers = get_post_headers()
    headers.update({
        "Content-Type": "application/json; charset=utf-8",
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "X-Requested-With": "XMLHttpRequest",
    })

    payload = {
        "model": {
            "FORM_TYPE": form_type,
            "DEPT": dept,
            "EMPNO": empno,
            "SDATE": sdate,
            "EDATE": edate,
            "FORMID": formid,
        }
    }

    try:
        resp = session.post(url, data=json.dumps(payload, ensure_ascii=False), headers=headers, timeout=15)
    except Exception as e:
        return {"error": "request_failed", "message": str(e)}

    # 解析 .asmx 回應格式: {"d": "[...]"}
    items = []
    try:
        data = json.loads(resp.text)
        if isinstance(data, dict) and "d" in data:
            inner = data.get("d")
            if isinstance(inner, str):
                data = json.loads(inner)
            else:
                data = inner
        if isinstance(data, list):
            items = data
    except Exception:
        items = []

    projects = []
    for item in items:
        if not isinstance(item, dict):
            continue
        projects.append({
            "PROJECTNO": item.get("PROJECTNO", ""),
            "PROJECTNAME": item.get("PROJECTNAME", ""),
        })

    return {
        "status_code": resp.status_code,
        "projects": projects,
        "raw_count": len(items),
    }

def build_savedc_payload(**kwargs) -> Dict[str, str]:
    """
    將所有欄位轉成：
    key: JSON 字串（string）
    """
    payload = {}
    for key, value in kwargs.items():
        payload[key] = json.dumps(value, ensure_ascii=False)
    return payload
 
@mcp.tool()
def dc_apply(InWorkRoute):
    """
        填寫出差旅費申請單
        欄位說明：
        - AppData：流程狀態（IS_SUBMIT=N 表示暫存，不提交簽核)
        - ApplyItem：全部費用申請項目
        - BasicData：表單基本資料（員編、姓名、部門、表單編號、出差事由等）
        - InWorkCont：出差內容（地點、日期、專案等） 
        - InWorkRoute：非自行開車逐段路線與費用(高鐵、台鐵、計程車...) 
        - SignData / InWorkDrive / ChgInfo：簽核、駕車、變更資訊 
        - prepay：預支資訊。
    """
    import requests
    import json

    # ===============================
    # 1. 基本設定
    # ===============================

    FORM_URL = "https://expapply.iii.org.tw/expApply/Apply/DC.aspx"
    SAVE_URL = "https://expapply.iii.org.tw/expApply/Apply/DC.aspx/SaveDC"  # 請確認 Network 中實際暫存 URL

    session = requests.Session()
    user_agent = get_dynamic_user_agent()
    platform_info = get_dynamic_platform_info()
    
    # ===============================
    # 2. 先設定認證 cookies，再 GET 表單頁
    # ===============================

    # 設定重要的認證 cookies（必須在 GET 表單頁面之前設定）
    cookie_values = {
        'ASP.NET_SessionId': os.getenv("ASP_NET_SESSION_ID", ""),
        'clientTicket': os.getenv("CLIENT_TICKET", ""),
        'clientUserName': os.getenv("CLIENT_USERNAME", ""),
    }
    missing_cookies = [name for name, value in cookie_values.items() if not value]
    if missing_cookies:
        print(f"[yellow].env 中缺少 cookie 值: {', '.join(missing_cookies)}，請先執行 get_token.py[/yellow]", file=sys.stderr)
        return {"error": "缺少認證資訊", "missing_cookies": missing_cookies}
    
    print("[green]已從 .env 讀取登入 cookie。[/green]", file=sys.stderr)
    
    # 設定 cookies（加上更多參數以模擬真實瀏覽器）
    for name, value in cookie_values.items():
        if value:
            session.cookies.set(
                name=name, 
                value=value, 
                domain='expapply.iii.org.tw',
                path='/',
                secure=True  # HTTPS 連線
            )
            print(f"[cyan]已設定 cookie: {name}[/cyan]", file=sys.stderr)

    # 模擬真實瀏覽器的 headers（用於 GET 表單頁面）
    login_headers = {
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "Accept-Language": "zh-TW,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
        "Cache-Control": "max-age=0", #delete?
        "Connection": "keep-alive",
        "Host": "expapply.iii.org.tw",
        "Sec-Fetch-Dest": "empty",  # "document",?
        "Sec-Fetch-Mode": "cors",   # "navigate",?
        "Sec-Fetch-Site": "same-origin",
        "Sec-Fetch-User": "?1",
        "Upgrade-Insecure-Requests": "1",
        "User-Agent": user_agent,
        "sec-ch-ua": '"Microsoft Edge";v="143s", "Chromium";v="143", "Not A(Brand";v="24"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": platform_info
    }
    
    # 步驟 1: 先訪問主頁建立 session（有些網站需要這個步驟）
    print("[cyan]正在建立 session...[/cyan]", file=sys.stderr)
    try:
        home_resp = session.get("https://expapply.iii.org.tw/expApply/Default.aspx", headers=login_headers, timeout=30, allow_redirects=True)
        print(f"[cyan]主頁回應狀態: {home_resp.status_code}, URL: {home_resp.url}[/cyan]", file=sys.stderr)
    except Exception as e:
        print(f"[yellow]訪問主頁時發生錯誤（繼續嘗試）: {e}[/yellow]", file=sys.stderr)
    
    # 步驟 2: 訪問表單頁面
    print("[cyan]正在存取表單頁面...[/cyan]", file=sys.stderr)
    resp = session.get(FORM_URL, headers=login_headers, timeout=30, allow_redirects=True)
    
    # 顯示回應資訊
    print(f"[cyan]回應狀態碼: {resp.status_code}[/cyan]", file=sys.stderr)
    print(f"[cyan]最終 URL: {resp.url}[/cyan]", file=sys.stderr)
    print(f"[cyan]Content-Type: {resp.headers.get('Content-Type', 'N/A')}[/cyan]", file=sys.stderr)
    
    # 檢查是否被導向到登入頁面
    if 'Login.aspx' in resp.url or '登入中' in resp.text:
        print("[bold red]偵測到需要重新登入[/bold red]", file=sys.stderr)
        print(f"[red]當前 URL: {resp.url}[/red]", file=sys.stderr)
        print(f"[red]頁面內容前 500 字元:[/red]", file=sys.stderr)
        print(resp.text[:500], file=sys.stderr)
        print("\n[yellow]可能的原因：[/yellow]", file=sys.stderr)
        print("1. Cookies 已過期，請重新執行 get_token.py", file=sys.stderr)
        print("2. Cookie 的值不正確，請確認 .env 檔案內容", file=sys.stderr)
        print("3. 需要從不同的頁面開始訪問（例如從 Default.aspx）", file=sys.stderr)
        # return {"error": "需要重新登入", "message": "請執行 get_token.py 取得認證 cookies", "url": resp.url}
    
    print("[green]✓ 成功通過認證，未被導向登入頁面[/green]", file=sys.stderr)
    
    # 步驟 3: 取得當前使用者資訊
    user_info = get_user_info(session, login_headers)
    if user_info:
        print(f"[cyan]使用者資訊:[/cyan]", file=sys.stderr)
        print(f"  員工編號: {user_info.get('EMPNO', 'N/A')}", file=sys.stderr)
        print(f"  姓名: {user_info.get('Name', 'N/A')}", file=sys.stderr)
        print(f"  部門: {user_info.get('SHORT_DESCR', 'N/A')}", file=sys.stderr)
        print(f"  電話: {user_info.get('Telephone', 'N/A')}", file=sys.stderr)
    else:
        print("[yellow]⚠ 無法取得使用者資訊，將使用空白值[/yellow]", file=sys.stderr)
    
    # 確認使用者資訊
    print("\n" + "=" * 60, file=sys.stderr)
    print("[bold cyan]請確認以上使用者資訊是否正確[/bold cyan]", file=sys.stderr)
    print("=" * 60, file=sys.stderr)
    
    # try:
    #     confirm = input("\n是否繼續提交申請？(Y/n): ").strip().lower()
    #     if confirm and confirm not in ['y', 'yes', '是']:
    #         print("\n[yellow]已取消提交[/yellow]", file=sys.stderr)
    #         return {"status": "cancelled", "message": "使用者取消提交"}
    #     print("\n[green]✓ 繼續提交申請...[/green]", file=sys.stderr)
    # except (EOFError, KeyboardInterrupt):
    #     print("\n[yellow]已取消提交[/yellow]", file=sys.stderr)
    #     return {"status": "cancelled", "message": "使用者取消提交"}
    
    # 解析 HTML 取得隱藏欄位
    soup = BeautifulSoup(resp.text, 'html.parser')
    
    # ===============================
    # 3. 組「暫存用」payload（IS_SUBMIT = N）
    #    依欄位說明：系統自動帶入者一律填空字串，交由伺服器依 session 補值
    # ===============================

    # 只接收 InWorkRoute，其餘欄位先設為空白（後續再以其他變數補值）
    # 允許傳入字串或 list
    try:
        parsed_route = json.loads(InWorkRoute) if isinstance(InWorkRoute, str) else InWorkRoute
    except Exception:
        parsed_route = []

    if not isinstance(parsed_route, list):
        parsed_route = []

    # 預設空白或基礎值（非自動欄位）
    cont_reason = ""
    address = ""
    bdate = ""
    edate = ""
    outdays = ""
    projid = ""
    projid_name = ""
    all_projid_chk = "N" #是否用顯示全部計畫
    no_projid_chk = "N"  #是否用顯示全部計畫
    comments = ""

    is_submit = "N"
    
    # 從 API 取得的使用者資訊
    apy_emp = user_info.get('EMPNO', '') if user_info else ''
    apy_name = user_info.get('Name', '') if user_info else ''
    apy_dept = user_info.get('DEPTNO', '') if user_info else ''
    apy_dept_name = user_info.get('SHORT_DESCR', '') if user_info else ''
    
    print(f"[cyan]將使用以下資訊填入表單:[/cyan]", file=sys.stderr)
    print(f"  APY_EMP (員工編號): {apy_emp}", file=sys.stderr)
    print(f"  APY_NAME (姓名): {apy_name}", file=sys.stderr)
    print(f"  APY_DEPT (部門編號): {apy_dept}", file=sys.stderr)
    print(f"  APY_DEPT_NAME (部門名稱): {apy_dept_name}", file=sys.stderr)

    # 依 InWorkRoute 逐筆建立 ApplyItem（簡單映射、維持原順序，不額外抽函式）
    apply_items = []
    #三個空白加上一個預填寫(其實也是空白)
    sign_data = []
    inwork_drive = []
    chg_info = {}
    prepay_obj = {"feetype": "", "feereason": "", "PrePay2": [], "PrePay3": []}

    # 依 InWorkRoute 自動計算期間：outdays = edate - bdate + 1（yyyy/mm/dd）
    from datetime import datetime as _dt
    def _parse_date_ymd_slash(s):
        try:
            return _dt.strptime(s, "%Y/%m/%d").date()
        except Exception:
            return None

    route_dates = []
    for it in parsed_route:
        d = it.get("BDATE")
        if isinstance(d, str) and d:
            dd = _parse_date_ymd_slash(d)
            if dd:
                route_dates.append(dd)

    if route_dates:
        start_d = min(route_dates)
        end_d = max(route_dates)
        bdate = start_d.strftime("%Y/%m/%d")
        edate = end_d.strftime("%Y/%m/%d")
        outdays = str((end_d - start_d).days + 1)

    # 取得專案清單（使用前面取得的 EMPNO 與計算出的 SDATE/EDATE）
    if apy_emp and bdate and edate:
        project_resp = fetch_emp_projects(apy_emp, bdate, edate, dept=apy_dept)
        if isinstance(project_resp, dict) and project_resp.get("projects"):
            print(f"[cyan]取得專案數量: {len(project_resp['projects'])}[/cyan]", file=sys.stderr)
            projects = project_resp.get("projects", [])
            selected = None
            for p in reversed(projects):
                if isinstance(p, dict) and p.get("PROJECTNO"):
                    selected = p
                    break
            if selected is None and projects:
                selected = projects[-1]
            if isinstance(selected, dict):
                projid = selected.get("PROJECTNO", "")
                projid_name = selected.get("PROJECTNAME", "")

    # 依照 InWorkRoute 建立 ApplyItem（僅映射有的欄位，缺少則留空）
    if isinstance(parsed_route, list) and parsed_route:
        for idx, r in enumerate(parsed_route, start=1):
            bplace = r.get("BPLACE", "")
            eplace = r.get("EPLACE", "")
            desc1 = f"{bplace}-{eplace}" if (bplace or eplace) else ""
            mover_name = r.get("MOVER_NAME", "")
            item_name = "計程車資" if mover_name == "計程車" else f"交通費_{mover_name}"

            apply_items.append({
                "NUMBER": r.get("NUMBER", idx),
                "SOURCE": r.get("SOURCE", "R"),
                "UUID": r.get("UUID", ""),
                "ORD": r.get("ORD", 0),
                "ITEM_NAME": item_name,
                "DESC1": desc1,
                "REASON": r.get("REASON"),
                "ACTNAME": "旅運費",
                "ESTPRICE": r.get("PRICE", ""),
                "ESTPRICE_FMT": r.get("PRICE_FMT", r.get("PRICE", "")),
                "ACTYEAR": r.get("ACTYEAR", ""),
                "PROJID": r.get("PROJID", ""),
                "PROJID_NAME": r.get("PROJID_NAME", "")
            })

    # 追加雜費項目（放在 ApplyItem 最後），沿用前一筆的 ACTYEAR/PROJID/PROJID_NAME
    last_item = apply_items[-1] if apply_items else {}
    apply_items.append({
        "NUMBER": len(apply_items) + 1,
        "SOURCE": "A",
        "UUID": "",
        "FORMID": "",
        "ORD": 0,
        "ITEM_NAME": "雜費",
        "DESC1": "每日上限為 400 元",
        "REASON": None,
        "ACTNAME": "旅運費",
        "ACTYEAR": last_item.get("ACTYEAR", ""),
        "PROJID": last_item.get("PROJID", ""),
        "PROJID_NAME": last_item.get("PROJID_NAME", "                                                        "),
        "ESTPRICE": 400,
        "ESTPRICE_FMT": "400",
        "VALID_FLAG": None,
        "UD_ADD": None
    })

    payload = {
        # ---- 系統狀態 ----
        "AppData": {
            "IS_SUBMIT": is_submit
        },

        # ---- 表單主檔 ---- 從 API 取得的使用者資訊
        "BasicData": {
            "FORM_TYPE": "DC",
            # 從 API 取得的使用者資訊
            "APY_EMP": apy_emp,
            "APY_NAME": apy_name,
            "FILL_EMP": apy_emp,  # 填寫人通常與申請人相同
            "FILL_NAME": apy_name,
            "APY_DEPT": apy_dept,
            "APY_DEPT_NAME": apy_dept_name,
            "FILL_DEPT": apy_dept,  # 填寫人部門通常與申請人相同
            "FILL_DEPT_NAME": apy_dept_name,
            # 以下為系統自動帶入欄位，留空由伺服器處理
            "ORG_FORMID": "",
            "FORMID": "",
            "PREPAYMENT": "",
            "ACC_AMT": "",
            "REASON": "",
            "IS_DISPATCH": "",
            "IS_SUBMIT": is_submit
        },

        # ---- 出差內容 ----
        "InWorkCont": {
            "REASON": cont_reason,
            # 從 API 取得的使用者資訊
            "APY_NAME": apy_name,
            "EMP_TITLE": "",  # 職稱留空由系統處理
            "APY_EMPNO": apy_emp,
            # 使用者可提供的非自動欄位
            "ADDRESS": address,
            "BDATE": bdate,
            "EDATE": edate,     # 預設當地來回
            "OUTDAYS": outdays, # 不知道會不會自己帶入
            "PROJID": projid,
            "ALL_PROJID_CHK": all_projid_chk, #預設N
            "NO_PROJID_CHK": no_projid_chk,   #預設N
            "COMMENTS": comments              #預設""
        },

        # ---- 費用項目(從InWorkRoute建立) ----
        "ApplyItem": apply_items,

        # ---- 交通路線 ----
        "InWorkRoute": parsed_route,

        # ---- 按照預設空白處理的欄位 ----
        "SignData": sign_data,
        "InWorkDrive": inwork_drive,
        "ChgInfo": chg_info,
        "prepay": prepay_obj
    }

    # 最後送出前，強制覆寫 payload 內所有 PROJID / PROJID_NAME
    if projid or projid_name:
        payload["InWorkCont"]["PROJID"] = projid
        for item in payload.get("ApplyItem", []):
            if isinstance(item, dict):
                item["PROJID"] = projid
                item["PROJID_NAME"] = projid_name
        for item in payload.get("InWorkRoute", []):
            if isinstance(item, dict):
                item["PROJID"] = projid
                item["PROJID_NAME"] = projid_name
    payload = build_savedc_payload(**payload)
    print("轉換後的 payload 如下：", file=sys.stderr)
    print(json.dumps(payload, ensure_ascii=False, indent=4), file=sys.stderr)

    # ===============================
    # 4. 檢查隱藏欄位並準備 payload
    # ===============================
    
    viewstate = soup.find('input', {'name': '__VIEWSTATE'})
    viewstate_generator = soup.find('input', {'name': '__VIEWSTATEGENERATOR'})
    
    if not all([viewstate, viewstate_generator]):
        print("[bold red] 無法找到必要的隱藏欄位，可能需要重新登入[/bold red]", file=sys.stderr)
        print(f"[red]找到 __VIEWSTATE: {viewstate is not None}[/red]", file=sys.stderr)
        print(f"[red]找到 __VIEWSTATEGENERATOR: {viewstate_generator is not None}[/red]", file=sys.stderr)
        return {"error": "無法取得表單隱藏欄位", "message": "請確認登入狀態"}
    
    # 使用從網頁取得的最新隱藏欄位更新表單資料
    payload['__VIEWSTATE'] = viewstate['value']
    payload['__VIEWSTATEGENERATOR'] = viewstate_generator['value']
    
    print("[bold green] 成功取得所有隱藏欄位[/bold green]", file=sys.stderr)
    
    # ===============================
    # 5. POST 暫存（不送出簽核）
    # ===============================
    
    save_resp = session.post(
        "https://expapply.iii.org.tw/expApply/Apply/DC.aspx/SaveDC",
        data=json.dumps(payload, ensure_ascii=False),
        headers=get_post_headers()
    )
    try:
        print("暫存狀態碼:", save_resp.status_code, file=sys.stderr)
        print("暫存回應內容:", file=sys.stderr)
        print(save_resp.text, file=sys.stderr)

        # ===============================
        # 6. 提示使用者開啟官方頁面
        # ===============================
        print(FORM_URL, file=sys.stderr)
    except Exception as e:
        print(f"[yellow]解析暫存回應時發生錯誤: {e}[/yellow]", file=sys.stderr)
        return {"error": "失敗", "message": str(e)}
    return {"status_code": save_resp.status_code, "text": save_resp.text}

if __name__ == "__main__":
    # 簡單執行入口：從命令列傳入 JSON 字串或檔案路徑，否則使用示範資料
    InWorkRoute = []

    if len(sys.argv) > 1:
        arg = sys.argv[1]
        if os.path.isfile(arg):
            try:
                with open(arg, "r", encoding="utf-8") as f:
                    InWorkRoute = json.load(f)
            except Exception:
                InWorkRoute = []
        else:
            try:
                InWorkRoute = json.loads(arg)
            except Exception:
                InWorkRoute = []

    if not isinstance(InWorkRoute, list):
        InWorkRoute = []

    # 若未提供或解析失敗，使用一筆示範資料
    if not InWorkRoute:
        InWorkRoute = [{"NUMBER": 1, "SOURCE": "R", "UUID": "", "FORMID": "", "ORD": 0, "BDATE": "2026/01/19", "MOVER": "A", "MOVER_NAME": "高鐵", "MOVER_OTHER": "", "BPLACE": "臺北車站", "EPLACE": "高鐵臺中站", "REASON": "出差", "PRICE": "700", "PRICE_FMT": "700", "ACTYEAR": 2026, "PROJID": "", "PROJID_NAME": "", "VALID_FLAG": "1", "UD_ADD": "Y"}, {"NUMBER": 2, "SOURCE": "R", "UUID": "", "FORMID": "", "ORD": 0, "BDATE": "2026/01/19", "MOVER": "Y", "MOVER_NAME": "計程車", "MOVER_OTHER": "", "BPLACE": "高鐵臺中站", "EPLACE": "臺中科技大學", "REASON": "出差 (公車路線以計程車費用估算)", "PRICE": "360", "PRICE_FMT": "360", "ACTYEAR": 2026, "PROJID": "", "PROJID_NAME": "", "VALID_FLAG": "1", "UD_ADD": "Y"}]

    dc_apply(InWorkRoute)

    mcp.run(transport="stdio")