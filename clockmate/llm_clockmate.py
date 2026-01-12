import datetime
import json
import re
from typing import Dict, Tuple, List, Any, Union

import akasha
import traceback
import json_repair
from urllib.parse import quote
from bs4 import BeautifulSoup
import platform
import calendar
import os
import sys
import requests

import dotenv
dotenv.load_dotenv()
from mcp.server.fastmcp import FastMCP  # noqa: E402
mcp = FastMCP("parse_llm_output")


MODEL = "gemini:gemini-2.5-flash"
BASE_TIMESHEET_URL = "https://hrwt.iii.org.tw/TSM/MyWorkTime.aspx"
TIMESHEET_ORIGIN = "https://hrwt.iii.org.tw"

def reset_session_state():
    """重置會話初始化狀態（供 SSH 連線開始時呼叫）。"""
    global SESSION_INITIALIZED
    SESSION_INITIALIZED = False

# 可選的 I/O 掛勾（供 SSH 路徑覆寫互動輸入確認）
INPUT_FUNC = None  # Callable[[str, object], str]
CONFIRM_FUNC = None  # Callable[[str, bool], bool]


def build_timesheet_url(year_month=None):
    """Construct the timesheet URL optionally bound to a specific year/month."""
    if year_month:
        encoded_ym = quote(year_month)
        return f"{BASE_TIMESHEET_URL}?YM={encoded_ym}"
    return BASE_TIMESHEET_URL


def get_weekend():
    """
    取得當月所有週六、週日，回傳為以逗號分隔的字串（每個為 MM-DD）。
    範例："11-01,11-02,..."
    """
    today = datetime.date.today()
    year, month = today.year, today.month

    weekends = ""
    # 僅處理從月初到今天（含今天）
    last_day = today.day
    for day in range(1, last_day + 1):
        d = datetime.date(year, month, day)
        if d.weekday() >= 5:  # 5=Saturday, 6=Sunday
            weekends += f"{month:02d}-{day:02d},"
    return year, month, today, weekends

def prompt_create(user_message = ""):
    year, month, today, weekends = get_weekend()
    date_prompt = f"今天是:{today}，請填寫從'{year}-{month}-01'到今天的工時，其中\{weekends}\為例假日"
    # user_prompt = f"""
    # # 任務:
    # 你是工時填寫小幫手，負責協助使用者整理每日上下班時間、未打卡原因、備註等資訊。
    # 根據使用者提供的訊息，請判斷其是否與工時填寫相關，並根據需求整理成指定的 JSON 格式。
    
    # # 規則:
    # 最高優先級指令：僅可輸出dictionary格式
    # 1.嚴格檢查使用者訊息"{user_message}"
    # 2.優先判斷，若使用者訊息為空字串，則直接判斷為相關
    # 3.其次判斷使用者訊息是否與「上下班時間」、「未打卡原因」、「混合工作/公出/受訓」等無關(僅字面提及也不算(如混合工作好爽、受訓好累、不想公出))。
    # 4.如果使用者訊息被判定為「無關」、「未提及」請立刻停止執行所有後續指令，並且"只輸出"以下單一 JSON 對象：
    # \{{"message":""\}} 該message對應的value請使用友善且禮貌的口吻提醒使用者你是負責填寫工時的小幫手，無法協助，如果有填寫工時的需要歡迎找你
    # 如果內容被判定為「相關」，則繼續執行以下指令：
    # 請只輸出dictionary，不輸出多餘文字與程式碼區塊。
    # {date_prompt}
    # 優先根據使用者訊息的要求，將每日的上下班時間、未打卡事由、備註等資訊整理成 JSON 格式。
    # 若使用者訊息為空白，則直接填入預設值
    # 若使用者訊息有簡短字句但過於簡短以致無法確認意圖(如:10點，受訓、忘刷)，
    # 請依照\{{"reask":"請問..."\}}格式回覆，根據針對簡短輸入的回問策略，產生一個簡潔、禮貌且具體的回問語句，引導使用者提供缺失的關鍵資訊（日期與時間及原因），提供使用者確認:
    
    # 當例假日時，\{{MM-DD:\{{"arrival_time":"","leave_time":"","reason":"","remark":""\}},...\}} 
    # 當使用者訊息有混合工作、公出、受訓的情況，則在reason中輸入\{{MM-DD:\{{"arrival_time":"HH:MM","leave_time":"HH:MM","reason":"混合工作/公出/受訓(擇一)","remark":""\}},...\}}
    # 其他未提及的日期則填入預設值\{{arrival_time="09:00"、leave_time="18:00"、reason="忘刷"、remark=""\}}

    # # 對話紀錄:
    # """
    
    user_prompt = f"""
# 任務:
你是工作小幫手，主要的任務有2個:
1. 工時填寫，負責協助使用者整理每日上下班時間、未打卡原因、備註等資訊。
2. 出差單填寫，協助規劃路線，依照步驟協助填寫出差單
根據使用者提供的訊息，請判斷其是否與工時填寫或出差單填寫相關，並根據需求整理成指定的格式。

# 今日日期資訊
今天是:{today}，請填寫從'{year}-{month}-01'到今天的工時，其中\{weekends}\為例假日
""" + """
# 工時填寫規則:
如果使用者的需求不是與填寫工作時間(工時)，可以做出簡短適當的回應，並且詢問可以幫忙使用者作什麼有關工時填寫的事。
如果使用者的需求是與填寫工作時間(工時)相關，請輸出以下格式的JSON字串:
{"work_times":{"yyyyMMDD":{"arrival_time":"HH:MM","leave_time":"HH:MM","reason":"原因","remark":"備註"},...}}
請只輸出dictionary，不輸出多餘文字與程式碼區塊，不然後面會無法處理。
若是使用者未詳細說明工作時間資訊細節，則使用預設值，生成從月初到今天的每日工時資訊，預設值為:
arrival_time="09:00"、leave_time="18:00"、reason="忘刷"、remark="" 來產生每日工時資訊。
範例:
{"work_times":{"20251201":{"arrival_time":"09:00","leave_time":"18:00","reason":"忘刷","remark":""},
 "20251202":{"arrival_time":"10:00","leave_time":"17:30","reason":"忘刷","remark":""}...}}
 <一直填到今天日期為止>}
如果使用者有指定那些日期需要填寫工時，例如: 12月3日與4日上班時間10點和9點，則生成該日期的工時資訊為:
{"work_times":{"20251203":{"arrival_time":"10:00","leave_time":"18:00","reason":"忘刷","remark":""},
 "20251204":{"arrival_time":"09:00","leave_time":"18:00","reason":"忘刷","remark":""}}
就好。
""" + """
# 出差單填寫規則:
    1.預設使用大眾交通工具規劃路線(maps_directions)
    2.當規畫中有需要搭乘公車的部分，將起始點與終點設為開車進行距離與時間測量，若搭乘公車前後有步行規劃，連同步行行程也納入開車計算
    3.若有改為開車，則使用計程車價格(taxi_fare_estimator)計算費用
    4.通過tools精確抓取大眾交通工具(高鐵(thsr_fare_estimator)、台鐵(tr_fare_estimator))的花費
    5.根據以上資料進行填寫出差單的InWorkRoute欄位，並回傳符合格式List
    6.若有多段路程，請將每段步行以外的路程以[{"NUMBER":1,...}, {"NUMBER":2,...}]的形式回傳
    "InWorkRoute": [
        {
            "NUMBER": 1,
            "SOURCE": "R",
            "UUID": "",
            "FORMID": "",
            "ORD": 0,
            "BDATE": "<start_date, ex: 2025/12/11>",
            "MOVER": <mover, ex: Y>, #搭乘交通工具編號僅有[高鐵:A,飛機:B,輪船:C,客運:D,火車(自強):E,火車(莒光):F,火車(復興):G,火車(普通):H,火車(電聯車):I,捷運:X,計程車:Y,其他:Z]
            "MOVER_NAME": "<mover_name, ex: 計程車>" #僅有[高鐵,飛機,輪船,客運,火車(自強),火車(莒光),火車(復興),火車(普通),火車(電聯車),捷運,計程車,其他],
            "MOVER_OTHER": "",
            "BPLACE": "<begin_location>" #該路程起始點,
            "EPLACE": "<end_location>" #該路程終點,
            "REASON": "<reason_for_taxi>" #搭乘原因,
            "PRICE": "<price>" #該路程費用,
            "PRICE_FMT": "<price>" #該路程費用(同PRICE)),
            "ACTYEAR": <ACTYEAR, ex: 2026> #出差年,
            "PROJID": "",
            "PROJID_NAME": "",
            "VALID_FLAG": "1",
            "UD_ADD": "Y",
        }
    ],
""" + f"""
# 使用者訊息:
{user_message}
"""
    return user_prompt

def get_per_day_work_times_by_llm(
        model: str = "gemini:gemini-2.5-flash",
        user_prompt: str = "",
        info: str = "",
    ):
    user_prompt = prompt_create()
    model = "gemini:gemini-2.5-flash"
    ak = akasha.ask(model=model, max_input_tokens=8000, max_output_tokens=20000)
    res = ak(prompt=user_prompt)
    return res

TIME_PATTERN = re.compile(r"^([01]\d|2[0-3]):[0-5]\d$")

def validate_llm_json(parsed: Dict[str, Any]) -> Tuple[bool, str, Dict[str, Dict[str, str]]]:
    """
    驗證已解析的 JSON 物件（dict）。
    規則簡化：
    1) 期望是一個日期→物件 的 dict（message-only 應在 parse_llm_output 前置處理）。
    2) 每個日期的物件需包含四鍵：arrival_time, leave_time, reason, remark。
    3) arrival_time/leave_time 若非空字串，需為 HH:MM 格式。

    回傳: (ok, first_error_str, data_dict)
    """
    required_fields = ["arrival_time", "leave_time", "reason", "remark"]
    result: Dict[str, Dict[str, str]] = {}

    for date_key, payload in parsed.items():
        if not isinstance(payload, dict):
            return False, f"日期 {date_key} 的值不是 dict", parsed

        missing = [f for f in required_fields if f not in payload]
        if missing:
            return False, f"日期 {date_key} 缺少欄位: {','.join(missing)}", {}

        arrival = str(payload.get("arrival_time", ""))
        leave = str(payload.get("leave_time", ""))
        reason = str(payload.get("reason", ""))
        remark = str(payload.get("remark", ""))

        if arrival and not TIME_PATTERN.match(arrival):
            return False, f"{date_key} arrival_time 格式錯誤: {arrival}", {}
        if leave and not TIME_PATTERN.match(leave):
            return False, f"{date_key} leave_time 格式錯誤: {leave}", {}

        result[date_key] = {
            "arrival_time": arrival,
            "leave_time": leave,
            "reason": reason,
            "remark": remark,
        }

    return True, "", result

def _clean_and_parse(raw_text: str) -> Tuple[bool, Dict[str, Any]]:
    """標準化並嘗試解析為 JSON 物件(dict)。

    清理規則：
    - 移除多餘空白（標準化空白，去除冒號、逗號、花括號周邊空白）
    - 移除所有三個反引號 "```"
    """
    cleaned = raw_text.strip()
    # 移除所有三個反引號
    cleaned = cleaned.replace("```", "")

    # 標準化冒號、逗號周邊空白，以及花括號周邊空白
    cleaned = re.sub(r"\s*:\s*", ":", cleaned)
    cleaned = re.sub(r"\s*,\s*", ",", cleaned)
    cleaned = re.sub(r"\s*\{\s*", "{", cleaned)
    cleaned = re.sub(r"\s*\}\s*", "}", cleaned)

    try:
        maybe = json.loads(cleaned)
        if isinstance(maybe, dict):
            return True, maybe
        return False, raw_text
    except Exception as e:
        return False, e


def parse_llm_output(raw_text: str) -> Union[str, Dict[str, Dict[str, str]]]:
    """
    解析模型輸出：
    - 若為 {"message": "..."}，直接回傳該訊息字串（不再做驗證）。
    - 否則執行格式驗證，通過則回傳日期→工時的 dict，失敗則拋出 ValueError。
    """
    ok_parse, parsed = _clean_and_parse(raw_text)
    
    try:
        if not ok_parse:
            return f"很抱歉，麻煩再試一次:{parsed}"

        if ok_parse:
            # 統一檢查：message-only（與工作無關）
            if set(parsed.keys()) == {"message"} and isinstance(parsed.get("message"), str):
                return {"message": parsed.get("message")}
            # 統一檢查：reask 需求
            if set(parsed.keys()) == {"reask"} and isinstance(parsed.get("reask"), str):
                return {"reask": parsed.get("reask")}

        # 檢查格式有效性
        ok, err, data = validate_llm_json(parsed)
        if not ok:
            return err or "格式驗證失敗"
        return data
    
    except Exception as e:
        print(traceback.format_exc(), file=sys.stderr)
        # 發生例外，回傳原始文字以供調試
        return {'message': raw_text}

def generate_form_llm_data(year_month=None, 
                       default_work_times=None,
                       until_date=None,
                       mode="llm"):
    """
    自動生成工時表單資料
    
    Args:
        year_month (str): 年月，格式如 "2025/10"，如果不提供則使用當前月份
        default_work_times (dict): 預設工作時間設定，格式如：
            {
                'arrival_time': '09:00',    # 預設上班時間
                'leave_time': '18:00',      # 預設下班時間
                'reason': '忘刷',           # 預設原因
                'remark': ''                # 預設備註
            }
    
    Returns:
        dict: 完整的表單資料
    """
    # 如果沒有提供年月，使用當前年月
    if year_month is None:
        now = datetime.datetime.now()
        year_month = f"{now.year}/{now.month:02d}"
    
    # 預設工作時間設定
    if default_work_times is None:
        default_work_times = {
            'arrival_time': '09:00',
            'leave_time': '18:00', 
            'reason': '忘刷',
            'remark': ''
        }
    
    # 解析年月
    try:
        year, month = year_month.split('/')
        year = int(year)
        month = int(month)
    except ValueError:
        raise ValueError("年月格式錯誤，請使用 'YYYY/MM' 格式，例如 '2025/10'")
    
    # 基本表單資料（隱藏欄位會在後續動態更新）
    form_data = {
        "__EVENTTARGET": "ctl00$ContentPlaceHolder1$btnEdit",
        "__EVENTARGUMENT": "",
        "__VIEWSTATE": "<GET_FROM_BROWSER>",
        "__VIEWSTATEGENERATOR": "<GET_FROM_BROWSER>",
        "__EVENTVALIDATION": "<GET_FROM_BROWSER>",
        "ctl00$ContentPlaceHolder1$txb_StDay": year_month,
    }
    
    # 取得該月的天數
    days_in_month = calendar.monthrange(year, month)[1]
    if until_date is None or until_date > days_in_month:
        until_date = days_in_month

    # 生成每一天的表單欄位
    work_days = []  # 記錄工作日
    holidays = []   # 記錄假日

    # 判斷是否為「逐日設定」：若提供之 dict 並非單純 arrival/leave/reason/remark 四鍵，
    # 則視為 {date: {arrival_time, leave_time, reason, remark}, ...}

    for day in range(1, (until_date) + 1):
        date_str = f"{year}{month:02d}{day:02d}"  # 格式: 20251001
        
        # 判斷是否為工作日 (週一到週五)
        date_obj = datetime.date(year, month, day)
        is_workday = date_obj.weekday() < 5  # 0-4 是週一到週五
        
        if mode =="llm":
            # if isinstance(day_cfg, dict):
                # arr = day_cfg.get('arrival_time', '')
                # lev = day_cfg.get('leave_time', '')
                # rea = day_cfg.get('reason', '')
                # rem = day_cfg.get('remark', '')
            if isinstance(default_work_times, dict):
                arr = default_work_times.get(date_str, {}).get('arrival_time', '')
                lev = default_work_times.get(date_str, {}).get('leave_time', '')
                rea = default_work_times.get(date_str, {}).get('reason', '')
                rem = default_work_times.get(date_str, {}).get('remark', '')
            else:
                arr = lev = rea = rem = ''
                
            # for check in [arr, lev]:

            form_data[f"ctl00$ContentPlaceHolder1$txtArr_{date_str}"] = arr
            form_data[f"ctl00$ContentPlaceHolder1$txtLev_{date_str}"] = lev
            form_data[f"ctl00$ContentPlaceHolder1$Dp_{date_str}"] = rea
            form_data[f"ctl00$ContentPlaceHolder1$txtR_{date_str}"] = rem

            # 工作日/假日清單仍依平日定義
            if is_workday:
                work_days.append(date_str)
            else:
                holidays.append(date_str)
        else:
            if is_workday:
                # 工作日：填入預設時間
                form_data[f"ctl00$ContentPlaceHolder1$txtArr_{date_str}"] = default_work_times['arrival_time']
                form_data[f"ctl00$ContentPlaceHolder1$txtLev_{date_str}"] = default_work_times['leave_time']
                form_data[f"ctl00$ContentPlaceHolder1$Dp_{date_str}"] = default_work_times['reason']
                form_data[f"ctl00$ContentPlaceHolder1$txtR_{date_str}"] = default_work_times['remark']
                work_days.append(date_str)
            else:
                # 假日：空白
                form_data[f"ctl00$ContentPlaceHolder1$txtArr_{date_str}"] = ""
                form_data[f"ctl00$ContentPlaceHolder1$txtLev_{date_str}"] = ""
                form_data[f"ctl00$ContentPlaceHolder1$Dp_{date_str}"] = ""
                form_data[f"ctl00$ContentPlaceHolder1$txtR_{date_str}"] = ""
                holidays.append(date_str)
    
    # 添加隱藏的控制欄位（根據你原本的資料格式）
    form_data["ctl00$ContentPlaceHolder1$HidWkHCtrl"] = ";".join(holidays)
    form_data["ctl00$ContentPlaceHolder1$HidWkACtrl"] = ";".join(work_days)
    form_data["ctl00$ContentPlaceHolder1$HideStTimes"] = ""
    form_data["ctl00$ContentPlaceHolder1$HidEdTimes"] = ""
    
    # 友善展示預設上下班時間：優先使用傳入的平鋪預設，否則嘗試從首筆資料取值，避免缺鍵報錯
    if isinstance(default_work_times, dict) and 'arrival_time' in default_work_times and 'leave_time' in default_work_times:
        arrival_default = default_work_times.get('arrival_time', '')
        leave_default = default_work_times.get('leave_time', '')
    else:
        first_item = next(iter(default_work_times.values()), {}) if isinstance(default_work_times, dict) else {}
        arrival_default = first_item.get('arrival_time', '')
        leave_default = first_item.get('leave_time', '')

    print(f"[bold green] 生成 {year_month} 的表單資料[/bold green]", file=sys.stderr)
    print(f"[cyan] 工作日: {len(work_days)} 天[/cyan]", file=sys.stderr)
    print(f"[cyan] 假日: {len(holidays)} 天[/cyan]", file=sys.stderr)
    print(f"[magenta] 預設上班時間: {arrival_default}[/magenta]", file=sys.stderr)
    print(f"[magenta] 預設下班時間: {leave_default}[/magenta]", file=sys.stderr)
    
    return form_data


def get_fresh_form_llm_data(year_month=None, work_times=None, mode="llm"):
    """自動從網頁抓取最新的隱藏欄位和 headers，並生成表單資料"""
    # 建立 session 維持 cookie
    session = requests.Session()
    
    # 自動設定完整的瀏覽器 headers（根據當前系統環境）
    user_agent = get_dynamic_user_agent()
    platform_info = get_dynamic_platform_info()
    
    headers = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "Accept-Language": "zh-TW,zh;q=0.9,en;q=0.8",
        "Cache-Control": "max-age=0",
        # "Authorization": f"Bearer {os.getenv('TEL_BEARER_TOKEN', '')}", # 這個網站不需要 Bearer Token
        "Connection": "keep-alive",
        "Host": "hrwt.iii.org.tw",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "same-origin",
        "Sec-Fetch-User": "?1",
        "Upgrade-Insecure-Requests": "1",
        "User-Agent": user_agent,
        "sec-ch-ua": '"Chromium";v="130", "Google Chrome";v="130", "Not?A_Brand";v="99"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": platform_info
    }
    
    print(f"[bold cyan] 使用動態 User-Agent:[/bold cyan] {user_agent}", file=sys.stderr)
    print(f"[bold cyan] 平台資訊:[/bold cyan] {platform_info}", file=sys.stderr)
    
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
            session.cookies.set(name, value, domain='hrwt.iii.org.tw')
    
    target_url = build_timesheet_url(year_month)
    print(f"[cyan]正在獲取最新的頁面資料: {target_url}[/cyan]", file=sys.stderr)
    
    # 發送 GET 請求取得頁面
    response = session.get(target_url, headers=headers)
    
    if response.status_code != 200:
        print(f"[bold red]無法訪問頁面，狀態碼: {response.status_code}[/bold red]", file=sys.stderr)
        return None, None

    print(f"[green]成功取得頁面，長度: {len(response.text)} 字元[/green]", file=sys.stderr)
    
    # 顯示從伺服器收到的 cookies
    if response.cookies:
        print("[yellow] 從伺服器收到的 cookies:[/yellow]", file=sys.stderr)
        for cookie in session.cookies:
            print(f"  {cookie.name}={cookie.value}", file=sys.stderr)
    
    # 解析 HTML 取得隱藏欄位
    soup = BeautifulSoup(response.text, 'html.parser')
    
    viewstate = soup.find('input', {'name': '__VIEWSTATE'})
    viewstate_generator = soup.find('input', {'name': '__VIEWSTATEGENERATOR'})
    event_validation = soup.find('input', {'name': '__EVENTVALIDATION'})
    
    if not all([viewstate, viewstate_generator, event_validation]):
        print("[bold red] 無法找到必要的隱藏欄位，可能需要重新登入[/bold red]", file=sys.stderr)
        print(f"[red]找到 __VIEWSTATE: {viewstate is not None}[/red]", file=sys.stderr)
        print(f"[red]找到 __VIEWSTATEGENERATOR: {viewstate_generator is not None}[/red]", file=sys.stderr)
        print(f"[red]找到 __EVENTVALIDATION: {event_validation is not None}[/red]", file=sys.stderr)
        return None, None
    
    print("[bold green] 成功取得所有隱藏欄位[/bold green]", file=sys.stderr)
    print(f"[green]__VIEWSTATE 長度: {len(viewstate['value'])}[/green]", file=sys.stderr)
    print(f"[green]__VIEWSTATEGENERATOR: {viewstate_generator['value']}[/green]", file=sys.stderr)
    print(f"[green]__EVENTVALIDATION 長度: {len(event_validation['value'])}[/green]", file=sys.stderr)
    
    # 動態生成表單資料
    fresh_form_data = generate_form_llm_data(year_month, work_times, mode=mode)
    
    # 使用從網頁取得的最新隱藏欄位更新表單資料
    fresh_form_data['__VIEWSTATE'] = viewstate['value']
    fresh_form_data['__VIEWSTATEGENERATOR'] = viewstate_generator['value']
    fresh_form_data['__EVENTVALIDATION'] = event_validation['value']
    
    return fresh_form_data, session


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


def get_post_headers(year_month=None):
    """取得 POST 提交時的完整 headers（根據當前系統環境）"""
    user_agent = get_dynamic_user_agent()
    platform_info = get_dynamic_platform_info()
    referer_url = build_timesheet_url(year_month)
    
    return {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "Accept-Language": "zh-TW,zh;q=0.9,en;q=0.8",
        "Cache-Control": "max-age=0",
        "Connection": "keep-alive",
        "Content-Type": "application/x-www-form-urlencoded",
        "Host": "hrwt.iii.org.tw",
        "Origin": TIMESHEET_ORIGIN,
        "Referer": referer_url,
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "same-origin",
        "Sec-Fetch-User": "?1",
        "Upgrade-Insecure-Requests": "1",
        "User-Agent": user_agent,
        "sec-ch-ua": '"Chromium";v="130", "Google Chrome";v="130", "Not?A_Brand";v="99"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": platform_info
    }


@mcp.tool()
def submit_work_times(work_times: dict) -> str:
    """
    提交工時資料的動作。
    
    回傳成功訊息。
    """
    job_working_time = work_times
    
    # 取得當前年月
    now = datetime.datetime.now()
    target_year_month = f"{now.year}/{now.month:02d}"
    final_work_time = job_working_time

    form_data, session = get_fresh_form_llm_data(target_year_month, final_work_time, mode="llm")
    if not form_data:
        print("[bold red]無法生成表單資料，請稍後再試。[/bold red]", file=sys.stderr)
        return

    print("[bold green]表單資料已完成建立[/bold green]", file=sys.stderr)
    # if fetch_hidden and session:
    if session:
        print("[bold magenta]提交表單[/bold magenta]", file=sys.stderr)
        print(" 正在提交表單...", file=sys.stderr)
        post_headers = get_post_headers(target_year_month)
        print(f"[dim] 使用 headers: {list(post_headers.keys())}[/dim]", file=sys.stderr)

        submit_url = build_timesheet_url(target_year_month)
        response = session.post(submit_url, data=form_data, headers=post_headers, allow_redirects=False)

        print(f"[bold green] 提交完成！狀態碼: {response.status_code}[/bold green]", file=sys.stderr)

        if response.status_code == 302:
            location = response.headers.get('Location', '未知')
            print(f"[cyan] 重定向到: {location}[/cyan]", file=sys.stderr)
            if 'Default.aspx' not in location:
                print("[bold green] 表單提交可能成功！[/bold green]", file=sys.stderr)
            else:
                print("[bold red] 被重定向到登入頁面，可能需要重新認證[/bold red]", file=sys.stderr)
        elif response.status_code == 200:
            print("[cyan] 收到回應內容:[/cyan]", file=sys.stderr)
            print(response.text[:300] + "..." if len(response.text) > 300 else response.text, file=sys.stderr)
        else:
            print(f"[yellow] 未預期的狀態碼: {response.status_code}[/yellow]", file=sys.stderr)
            print(f"[yellow] 回應內容: {response.text[:200]}[/yellow]", file=sys.stderr)

        print(f"[dim]\n 回應標頭: {dict(response.headers)}[/dim]", file=sys.stderr)
            

    return "工時資料已成功提交！"


if __name__ == "__main__":
    mcp.run(transport="stdio")
