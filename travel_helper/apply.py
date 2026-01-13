from mcp.server.fastmcp import FastMCP  # noqa: E402
import requests
import json
import platform
from urllib.parse import quote
from bs4 import BeautifulSoup
import dotenv
dotenv.load_dotenv()

mcp = FastMCP("math")

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

@mcp.tool()
def dc_apply(InWorkRoute):
    """
        填寫出差旅費申請單

        待處理: 
            - 抓PROJID" / "PROJID_NAME" ?
            - 把輸入的InWorkRoute改成Applyitem(看到這裡，還沒確定怎麼改)
            - InWorkRoute 沒有 edate
            - 還是outdays其實會自己算?(只要給bdate和edate就好)
        payload 範例（可直接以 dict 提供；程式會自動將複雜物件轉為字串送出）：

        {
            "AppData": {"IS_SUBMIT":"N"},
            "ApplyItem": [
                {"NUMBER":1,"SOURCE":"R","UUID":"428895b8-943c-4aea-86e4-93136ac6a7f1","ORD":1,"ITEM_NAME":"交通費_高鐵","DESC1":"台中-台北","REASON":null,"ACTNAME":"旅運費","ESTPRICE":700,"ESTPRICE_FMT":"700","ACTYEAR":"2026","PROJID":"PJ123456","PROJID_NAME":"頂級滷肉製程"},
                {"NUMBER":2,"SOURCE":"R","UUID":"440862af-fd55-4a51-96b6-24e5c6782524","ORD":0,"ITEM_NAME":"計程車資","DESC1":"北車-民生","REASON":"移動","ACTNAME":"旅運費","ESTPRICE":"300","ESTPRICE_FMT":"300","ACTYEAR":2026,"PROJID":"PJ123456","PROJID_NAME":"PJ123456_頂級滷肉製程 2026/12/31_補助"},
                {"NUMBER":3,"SOURCE":"A","UUID":"a0c28fee-247a-4abc-8257-8f6609801abe","FORMID":"DC26010208","ORD":2,"ITEM_NAME":"雜費","DESC1":"每日上限為 400 元","REASON":null,"ACTNAME":"旅運費","ACTYEAR":"2026","PROJID":"PJ123456","PROJID_NAME":"頂級滷肉製程","ESTPRICE":400,"ESTPRICE_FMT":"400","VALID_FLAG":null,"UD_ADD":null}
            ],
            "BasicData": {"FORM_TYPE":"DC","APY_EMP":"260107","APY_NAME":"王小明","APY_DEPT":"R0","APY_DEPT_NAME":"秘方醬汁院","FILL_EMP":"260107","FILL_NAME":"王小明","FILL_DEPT":"R0","FILL_DEPT_NAME":"","ORG_FORMID":"DC26010208","FORMID":"DC26010208","PREPAYMENT":"N","ACC_AMT":0,"REASON":"王小明 2026/01/12 至  2026/01/12 出差至 223","IS_DISPATCH":"0","IS_SUBMIT":"N"},
            "ChgInfo": {},
            "InWorkCont": {"REASON":"123","APY_NAME":"王小明","EMP_TITLE":"\\n  助理工程師\\n","APY_EMPNO":"260107","ADDRESS":"223","BDATE":"2026/01/12","EDATE":"2026/01/12","OUTDAYS":"1","PROJID":"PJ123456","ALL_PROJID_CHK":"N","NO_PROJID_CHK":"N","NO_PROJID_DESC":"","COMMENTS":""},
            "InWorkDrive": [],
            "InWorkRoute": [
                {"NUMBER":1,"SOURCE":"R","UUID":"428895b8-943c-4aea-86e4-93136ac6a7f1","FORMID":"DC26010208","ORD":1,"BDATE":"2026/01/12","MOVER":"A","MOVER_NAME":"高鐵","MOVER_OTHER":"","BPLACE":"台中","EPLACE":"台北","REASON":null,"PRICE":700,"PRICE_FMT":"700","VALID_FLAG":"1","UD_ADD":null},
                {"NUMBER":2,"SOURCE":"R","UUID":"440862af-fd55-4a51-96b6-24e5c6782524","FORMID":"","ORD":0,"BDATE":"2026/01/12","MOVER":"Y","MOVER_NAME":"計程車","MOVER_OTHER":"","BPLACE":"北車","EPLACE":"民生","REASON":"移動","PRICE":"300","PRICE_FMT":"300","ACTYEAR":2026,"PROJID":"PJ123456","PROJID_NAME":"PJ123456_頂級滷肉製程 2026/12/31_補助","VALID_FLAG":"1","UD_ADD":"Y"}
            ],
            "SignData": [],
            "prepay": {"feetype":"","feereason":"","PrePay2":[],"PrePay3":[]}
        }

        欄位說明：
        - AppData：流程狀態（IS_SUBMIT=N 表示暫存，不提交簽核）           > 固定帶入 IS_SUBMIT=N
        - ApplyItem：全部費用申請項目 (再確定SOURCE:A的項目會不會自動帶入FORMID / UUID會不會自動帶入) > 用InWorkRoute修改並加入雜費
        - BasicData：表單基本資料（員編、姓名、部門、表單編號、出差事由等） > 自動帶入
        - InWorkCont：出差內容（地點、日期、專案等）                      > 部分自動帶入(自行填寫:事由、地點、日期、計畫編號)
        - InWorkRoute：非自行開車逐段路線與費用(高鐵、台鐵、計程車...)     > 由LLM生成
        - SignData / InWorkDrive / ChgInfo：簽核、駕車、變更資訊         > 可留空
        - prepay：預支資訊。
    """
    import requests
    import json

    # ===============================
    # 1. 基本設定
    # ===============================

    FORM_URL = "https://expapply.iii.org.tw/expApply/Apply/DC.aspx"
    SAVE_URL = "https://expapply.iii.org.tw/expApply/Apply/DC.aspx/SaveDC"  # ⚠️請確認 Network 中實際暫存 URL

    session = requests.Session()

    HEADERS = {
        "User-Agent": "Mozilla/5.0",
        "X-Requested-With": "XMLHttpRequest",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"
    }

    # ===============================
    # 2. 先 GET 表單頁（建立 session / 取得基本資料）
    # ===============================

    post_headers = get_post_headers()
    resp = session.get(SAVE_URL, headers=post_headers)
    resp.raise_for_status()
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
    all_projid_chk = "N" #是否用顯示全部計畫
    no_projid_chk = "N"  #是否用顯示全部計畫
    comments = ""

    is_submit = "N"

    # 依 InWorkRoute 逐筆建立 ApplyItem（簡單映射、維持原順序，不額外抽函式）
    apply_items = []
    #三個空白加上一個預填寫(其實也是空白)
    sign_data = []
    inwork_drive = []
    chg_info = {}
    prepay_obj = {"feetype": "", "feereason": "", "PrePay2": [], "PrePay3": []}

    # 依 InWorkRoute 自動計算期間：outdays = edate - bdate + 1（yyyy/mm/dd）(還是其實會自己算?)
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

    payload = {
        # ---- 系統狀態 ----
        "AppData": json.dumps({
            "IS_SUBMIT": is_submit
        }, ensure_ascii=False),

        # ---- 表單主檔 ---- 自動帶入
        "BasicData": json.dumps({
            "FORM_TYPE": "DC",
            # 以下為系統自動帶入欄位，統一填空字串
            "APY_EMP": "",
            "APY_NAME": "",
            "FILL_EMP": "",
            "FILL_NAME": "",
            "APY_DEPT": "",
            "APY_DEPT_NAME": "",
            "FILL_DEPT": "",
            "FILL_DEPT_NAME": "",
            "ORG_FORMID": "",
            "FORMID": "",
            "PREPAYMENT": "",
            "ACC_AMT": "",
            "REASON": "",
            "IS_DISPATCH":"",
            "IS_SUBMIT": is_submit
        }, ensure_ascii=False),

        # ---- 出差內容 ----
        "InWorkCont": json.dumps({
            "REASON": cont_reason,
            # 系統自動帶入者改為空字串
            "APY_NAME": "",
            "EMP_TITLE": "",
            "APY_EMPNO": "",
            # 使用者可提供的非自動欄位
            "ADDRESS": address,
            "BDATE": bdate,
            "EDATE": edate,     # 預設當地來回
            "OUTDAYS": outdays, # 不知道會不會自己帶入
            "PROJID": projid,
            "ALL_PROJID_CHK": all_projid_chk, #預設N
            "NO_PROJID_CHK": no_projid_chk,   #預設N
            "COMMENTS": comments              #預設""
        }, ensure_ascii=False),

        # ---- 費用項目(從InWorkRoute建立) ----
        # {"NUMBER":2,"SOURCE":"R","UUID":"440862af-fd55-4a51-96b6-24e5c6782524","FORMID":"","ORD":0,"BDATE":"2026/01/12","MOVER":"Y","MOVER_NAME":"計程車","MOVER_OTHER":"",
        # "BPLACE":"北車","EPLACE":"民生","REASON":"移動","PRICE":"300","PRICE_FMT":"300","ACTYEAR":2026,"PROJID":"PJ123456","PROJID_NAME":"PJ123456_頂級滷肉製程 2026/12/31_補助",
        # "VALID_FLAG":"1","UD_ADD":"Y"}
        "ApplyItem": json.dumps(apply_items, ensure_ascii=False),

        # ---- 交通路線 ----
        "InWorkRoute": json.dumps(parsed_route, ensure_ascii=False),

        # ---- 按照預設空白處理的欄位 ----
        "SignData": json.dumps(sign_data, ensure_ascii=False),
        "InWorkDrive": json.dumps(inwork_drive, ensure_ascii=False),
        "ChgInfo": json.dumps(chg_info, ensure_ascii=False),
        "prepay": json.dumps(prepay_obj, ensure_ascii=False)
    }
    print("組成的 payload 如下：")
    print(json.dumps(payload, ensure_ascii=False, indent=4))
    # ===============================
    # 4. 設定 cookies, 處理登入認證, POST 暫存（不送出）
    # ===============================

    # 設定重要的認證 cookies
    cookie_values = {
        'ASP.NET_SessionId': os.getenv("ASP_NET_SESSION_ID", ""),
        'clientTicket': os.getenv("CLIENT_TICKET", ""),
        'clientUserName': os.getenv("CLIENT_USERNAME", ""),
    }
    missing_cookies = [name for name, value in cookie_values.items() if not value]
    if missing_cookies:
        print(f"[yellow].env 中缺少 cookie 值: {', '.join(missing_cookies)}，請先執行 get_token.py[/yellow]", file=sys.stderr)
    else:
        print("[green]已從 .env 讀取登入 cookie。[/green]", file=sys.stderr)

    for name, value in cookie_values.items():
        if value:
            session.cookies.set(name, value, domain='expapply.iii.org.tw')
    
    viewstate = soup.find('input', {'name': '__VIEWSTATE'})
    viewstate_generator = soup.find('input', {'name': '__VIEWSTATEGENERATOR'})
    event_validation = soup.find('input', {'name': '__EVENTVALIDATION'})
    
    if not all([viewstate, viewstate_generator, event_validation]):
        print("[bold red] 無法找到必要的隱藏欄位，可能需要重新登入[/bold red]", file=sys.stderr)
        print(f"[red]找到 __VIEWSTATE: {viewstate is not None}[/red]", file=sys.stderr)
        print(f"[red]找到 __VIEWSTATEGENERATOR: {viewstate_generator is not None}[/red]", file=sys.stderr)
        print(f"[red]找到 __EVENTVALIDATION: {event_validation is not None}[/red]", file=sys.stderr)
        return None, None
    
    # 使用從網頁取得的最新隱藏欄位更新表單資料
    payload['__VIEWSTATE'] = viewstate['value']
    payload['__VIEWSTATEGENERATOR'] = viewstate_generator['value']
    payload['__EVENTVALIDATION'] = event_validation['value']
    
    print("[bold green] 成功取得所有隱藏欄位[/bold green]", file=sys.stderr)
    
    save_resp = session.post(SAVE_URL, data=payload, headers=HEADERS)
    save_resp.raise_for_status()

    print("暫存狀態碼:", save_resp.status_code)
    print("暫存回應內容:")
    print(save_resp.text)

    # ===============================
    # 5. 提示使用者開啟官方頁面
    # ===============================

    print("\n✅ 暫存完成")
    print("👉 請使用者登入後打開以下頁面查看並自行送出：")
    print(FORM_URL)

if __name__ == "__main__":
    # 簡單執行入口：從命令列傳入 JSON 字串或檔案路徑，否則使用示範資料
    import sys, os, json

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
        InWorkRoute = [
            {
                "NUMBER": 1,
                "SOURCE": "R",
                "UUID": "",
                "FORMID": "",
                "ORD": 0,
                "BDATE": "2026/01/12",
                "MOVER": "Y",
                "MOVER_NAME": "計程車",
                "MOVER_OTHER": "",
                "BPLACE": "北車",
                "EPLACE": "民生",
                "REASON": "移動",
                "PRICE": "300",
                "PRICE_FMT": "300",
                "ACTYEAR": "2026",
                "PROJID": "",
                "PROJID_NAME": "",
                "VALID_FLAG": "1",
                "UD_ADD": "Y"
            }
        ]

    dc_apply(InWorkRoute)

