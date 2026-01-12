from mcp.server.fastmcp import FastMCP  # noqa: E402
import requests
import json

mcp = FastMCP("math")

DC_APPLY_URL = "https://expapply.iii.org.tw/expapply/Apply/DC.aspx"

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
    from bs4 import BeautifulSoup

    # ===============================
    # 1. 基本設定
    # ===============================

    FORM_URL = "https://expapply.iii.org.tw/expApply/Apply/DC.aspx"
    SAVE_URL = "https://expapply.iii.org.tw/expApply/Apply/SaveTemp"  # ⚠️請確認 Network 中實際暫存 URL

    session = requests.Session()

    HEADERS = {
        "User-Agent": "Mozilla/5.0",
        "X-Requested-With": "XMLHttpRequest",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"
    }

    # ===============================
    # 2. 先 GET 表單頁（建立 session / 取得基本資料）
    # ===============================

    resp = session.get(FORM_URL)
    resp.raise_for_status()

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
            "EDATE": edate,
            "OUTDAYS": outdays, # 不知道會不會自己帶入
            "PROJID": projid,
            "ALL_PROJID_CHK": all_projid_chk, #預設N
            "NO_PROJID_CHK": no_projid_chk,   #預設N
            "COMMENTS": comments              #預設""
        }, ensure_ascii=False),

        # ---- 費用項目 ----
        "ApplyItem": json.dumps(
            apply_items if isinstance(apply_items, list) else [
                {
                    "NUMBER": 1,
                    "SOURCE": "R",
                    "UUID": "",
                    "ORD": 0,
                    "ITEM_NAME": "交通費_高鐵",
                    "DESC1": "台中-台北",  #起點-終點
                    "ACTNAME": "旅運費",
                    "ESTPRICE": "400",
                    "ESTPRICE_FMT": "400",
                    "ACTYEAR": "2026",
                    "PROJID": projid,
                    "PROJID_NAME": ""
                }
            ], ensure_ascii=False
        ),

        # ---- 交通路線 ----
        "InWorkRoute": json.dumps(parsed_route, ensure_ascii=False),

        # ---- 尚未送出 / 簽核 ----
        "SignData": json.dumps(sign_data, ensure_ascii=False),
        "InWorkDrive": json.dumps(inwork_drive, ensure_ascii=False),
        "ChgInfo": json.dumps(chg_info, ensure_ascii=False),

        # ---- 預支 ----
        "prepay": json.dumps(prepay_obj, ensure_ascii=False)
    }

    # ===============================
    # 4. POST 暫存（不送出）
    # ===============================

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

