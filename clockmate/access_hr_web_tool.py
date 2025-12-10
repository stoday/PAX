import requests
from urllib.parse import quote
from bs4 import BeautifulSoup
import platform
import datetime
import calendar
from pyfiglet import Figlet
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm
from rich.table import Table
from rich import box
import dotenv
import os
import logging
from pathlib import Path

# import akasha
# MODEL = "gemini:gemini-2.5-flash"
# try:
#     from .agent_tools import prompt_create, parse_llm_output
# except:
#     from agent_tools import prompt_create, parse_llm_output

# 載入環境變數
dotenv.load_dotenv()

BASE_TIMESHEET_URL = "https://hrwt.iii.org.tw/TSM/MyWorkTime.aspx"
TIMESHEET_ORIGIN = "https://hrwt.iii.org.tw"
# 將 log 檔案統一輸出到專案根目錄的 logs 資料夾，避免與套件內部路徑混淆
LOG_DIR = Path(__file__).resolve().parents[1] / "logs"
LOG_FILE = LOG_DIR / f"access_hr_web_tool_{datetime.datetime.now().strftime('%Y%m%d')}.log"

LOG_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    filename=str(LOG_FILE),
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    encoding="utf-8",
    force=True,  # Ensure file handler is set even if logging was configured elsewhere
)
console = Console()
# figlet = Figlet(font="slant")

# # 可選的 I/O 掛勾（供 SSH 路徑覆寫互動輸入確認）
INPUT_FUNC = None  # Callable[[str, object], str]
CONFIRM_FUNC = None  # Callable[[str, bool], bool]


def build_timesheet_url(year_month=None):
    """Construct the timesheet URL optionally bound to a specific year/month."""
    if year_month:
        encoded_ym = quote(year_month)
        return f"{BASE_TIMESHEET_URL}?YM={encoded_ym}"
    return BASE_TIMESHEET_URL


def generate_form_data_for_target_dates(year_month=None, 
                                       target_dates:dict=None, # ex: {'20251101':{'arrival_time': '09:00', 'leave_time': '18:00', 'reason': '忘刷', 'remark': ''}, ...}
                                       default_work_times=None):
    """
    自動生成工時表單資料，**僅針對指定日期列表修改**，並填入預設工作時間。
    """
    # 先生成至今的所有日期資料
    full_form_data = generate_form_util_today(year_month=year_month,
                                       default_work_times=default_work_times)
    
    # 根據目標日期來更新相關欄位
    if target_dates:
        for date_str, times in target_dates.items():
            if len(date_str) != 8 or not date_str.isdigit():
                # console.print(f"[red]⚠️ 日期格式錯誤: {date_str}，應為 YYYYMMDD 格式，跳過此日期。[/red]")
                logging.warning("日期格式錯誤: %s，應為 YYYYMMDD 格式，跳過此日期。", date_str)
                continue
            # 更新對應欄位
            full_form_data[f"ctl00$ContentPlaceHolder1$txtArr_{date_str}"] = times.get('arrival_time', '')
            full_form_data[f"ctl00$ContentPlaceHolder1$txtLev_{date_str}"] = times.get('leave_time', '')
            full_form_data[f"ctl00$ContentPlaceHolder1$Dp_{date_str}"] = times.get('reason', '')
            full_form_data[f"ctl00$ContentPlaceHolder1$txtR_{date_str}"] = times.get('remark', '')
        
        # 紀錄 full_form_data 資訊
        logging.info("已更新目標日期的表單資料: %s", str(full_form_data))
        return full_form_data
    
    else:
        # console.print("[yellow]⚠️ 未提供目標日期資料，無法更新表單。[/yellow]")
        logging.warning("未提供目標日期資料，無法更新表單。")
        return full_form_data


def generate_form_util_today(year_month=None,
                             default_work_times=None,
                             until_date=None):
    """
    自動生成工時表單資料，從年月開始到指定日期（或月底），並填入預設工作時間。
    
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

    for day in range(1, (until_date) + 1):
        date_str = f"{year}{month:02d}{day:02d}"  # 格式: 20251001
        
        # 判斷是否為工作日 (週一到週五)
        date_obj = datetime.date(year, month, day)
        is_workday = date_obj.weekday() < 5  # 0-4 是週一到週五
        
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
    
    # console.print(f"[bold green]📅 生成 {year_month} 的表單資料[/bold green]")
    # console.print(f"[cyan]📊 工作日: {len(work_days)} 天[/cyan]")
    # console.print(f"[cyan]🏖️ 假日: {len(holidays)} 天[/cyan]")
    # console.print(f"[magenta]⏰ 預設上班時間: {default_work_times['arrival_time']}[/magenta]")
    # console.print(f"[magenta]⏰ 預設下班時間: {default_work_times['leave_time']}[/magenta]")
    
    return form_data


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


def prompt_with_default(prompt_text, default_value=None):
    # 若有自訂輸入掛勾，使用簡單文字提示(花俏顯示使用)
    if default_value is not None:
        prompt_plain = f"{prompt_text} 預設值: [{default_value}]: "
    else:
        prompt_plain = f"{prompt_text}: "
    if INPUT_FUNC:
        try:
            val = INPUT_FUNC(prompt_plain, default_value)
        except Exception:
            val = ""
        return (val or default_value) if default_value is not None else (val or "")
    # 始終使用 Rich 標記以確保渲染樣式
    if default_value:
        prompt = f"[bold white]{prompt_text}[/bold white] [[cyan]{default_value}[/cyan]]: "
    else:
        prompt = f"[bold white]{prompt_text}[/bold white]: "
    user_input = console.input(prompt).strip()
    return user_input or (default_value if default_value is not None else "")


def prompt_yes_no(prompt_text, default=True):
    """使用者確認提示，回傳布林值"""
    if CONFIRM_FUNC:
        try:
            return CONFIRM_FUNC(prompt_text, default)
        except Exception:
            return default
    return Confirm.ask(f"[bold white]{prompt_text}[/bold white]", default=default)


def set_output_stream(stream):
    """Set a custom stream for Rich console output.
    Provide an object with a `.write(str)` method.
    """
    global console
    try:
        # 啟用 ANSI 顏色與樣式並強制解析 Rich 標記
        console = Console(
            file=stream,
            force_terminal=True,
            no_color=False,
            soft_wrap=False,
            markup=True,
        )
    except Exception:
        # Fallback to default console if stream invalid
        console = Console()


def set_io_hooks(input_func=None, confirm_func=None):
    """設定互動 I/O 掛勾（SSH 模式可覆寫輸入/確認）。"""
    global INPUT_FUNC, CONFIRM_FUNC
    INPUT_FUNC = input_func
    CONFIRM_FUNC = confirm_func


def run_cli(output_stream=None):
    """主要的 CLI 互動流程"""
    if output_stream is not None:
        set_output_stream(output_stream)
    now = datetime.datetime.now()
    target_year_month = f"{now.year}/{now.month:02d}"
 
    target_year_month = prompt_with_default("填寫年月 (YYYY/MM)", target_year_month)
    arrival_time = prompt_with_default("預設上班時間 (HH:MM)", "09:00")
    leave_time = prompt_with_default("預設下班時間 (HH:MM)", "18:00")
    reason = prompt_with_default("預設原因", "忘刷")
    remark = prompt_with_default("預設備註 (可留空)", "").strip()

    custom_work_times = {
        'arrival_time': arrival_time,
        'leave_time': leave_time,
        'reason': reason,
        'remark': remark
    }

    # summary_table = Table(show_header=False, box=box.SIMPLE_HEAVY)
    # summary_table.add_row("✨ 年月", target_year_month)
    # summary_table.add_row("⏰ 上班/下班", f"{arrival_time} - {leave_time}")
    # summary_table.add_row("📝 原因", reason)
    # summary_table.add_row("💬 備註", remark or "（無）")

    # console.rule("[bold cyan]設定摘要[/bold cyan]")
    # console.print(summary_table)

    final_work_time = custom_work_times

    # if not prompt_yes_no("是否繼續並生成表單資料？", True):
    #     console.print("[yellow]已取消操作。[/yellow]")
    #     return
    
    # 生成表單資料: 針對指定日期
    # form_data, session = get_fresh_form_for_target_dates(target_year_month, final_work_time)
    
    # 生成表單資料: 到今天為止
    form_data, session = get_fresh_form_for_util_today(target_year_month, final_work_time)
    
    if not form_data:
        # console.print("[bold red]無法生成表單資料，請稍後再試。[/bold red]")
        return

    post_headers = get_post_headers(target_year_month)
    submit_url = build_timesheet_url(target_year_month)
    response = session.post(submit_url, data=form_data, headers=post_headers, allow_redirects=False)
    logging.info("response status: %s", response.status_code)
    logging.info("response text: %s", response.text)

    # console.rule("[bold green]表單資料已完成建立[/bold green]")
    # # if fetch_hidden and session:
    # if session:
    #     if prompt_yes_no("需要立即提交表單嗎？", True):
    #         console.rule("[bold magenta]提交表單[/bold magenta]")
    #         console.print("📝 正在提交表單...")
    #         post_headers = get_post_headers(target_year_month)
    #         console.print(f"[dim]📋 使用 headers: {list(post_headers.keys())}[/dim]")

    #         submit_url = build_timesheet_url(target_year_month)
    #         response = session.post(submit_url, data=form_data, headers=post_headers, allow_redirects=False)

    #         console.print(f"[bold green]✅ 提交完成！狀態碼: {response.status_code}[/bold green]")

    #         if response.status_code == 302:
    #             location = response.headers.get('Location', '未知')
    #             console.print(f"[cyan]🔄 重定向到: {location}[/cyan]")

    #             if 'Default.aspx' not in location:
    #                 console.print("[bold green]🎉 表單提交可能成功！[/bold green]")
    #             else:
    #                 console.print("[bold red]❌ 被重定向到登入頁面，可能需要重新認證[/bold red]")
    #         elif response.status_code == 200:
    #             console.print("[cyan]📄 收到回應內容:[/cyan]")
    #             console.print(response.text[:300] + "..." if len(response.text) > 300 else response.text)
    #         else:
    #             console.print(f"[yellow]❓ 未預期的狀態碼: {response.status_code}[/yellow]")
    #             console.print(f"[yellow]回應內容: {response.text[:200]}[/yellow]")

    #         console.print(f"[dim]\n📊 回應標頭: {dict(response.headers)}[/dim]")
    #     else:
    #         console.print("[green]👌 表單資料已準備好，您可以稍後手動提交。[/green]")
    # else:
    #     console.print("[blue]📦 表單資料已生成，請記得自行補上隱藏欄位後再提交。[/blue]")


def process_headers_cookies(year_month=None):
    """自動從網頁抓取最新的隱藏欄位和 headers，並生成表單資料
    Args:
        year_month (str): 年月，格式如 "2025/10"
        work_times (dict): 自訂的上下班時間和原因等資訊
    returns:
        tuple: (form_data dict, requests.Session object)
    """
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
    
    # console.print(f"[bold cyan]🌐 使用動態 User-Agent:[/bold cyan] {user_agent}")
    # console.print(f"[bold cyan]💻 平台資訊:[/bold cyan] {platform_info}")
    
    # 設定重要的認證 cookies
    cookie_values = {
        'ASP.NET_SessionId': os.getenv("ASP_NET_SESSION_ID", ""),
        'clientTicket': os.getenv("CLIENT_TICKET", ""),
        'clientUserName': os.getenv("CLIENT_USERNAME", ""),
    }
    
    missing_cookies = [name for name, value in cookie_values.items() if not value]
    if missing_cookies:
        # console.print(f"[yellow].env 中缺少 cookie 值: {', '.join(missing_cookies)}，請先執行 get_token.py[/yellow]")
        logging.warning(".env 中缺少 cookie 值: %s，請先執行 get_token.py", ", ".join(missing_cookies))
    else:
        # console.print("[green]已從 .env 讀取登入 cookie。[/green]")
        logging.info("已從 .env 讀取登入 cookie。")

    for name, value in cookie_values.items():
        if value:
            session.cookies.set(name, value, domain='hrwt.iii.org.tw')
    
    target_url = build_timesheet_url(year_month)
    # console.print(f"[cyan]正在獲取最新的頁面資料: {target_url}[/cyan]")
    logging.info("正在獲取最新的頁面資料: %s", target_url)
    
    # 發送 GET 請求取得頁面
    response = session.get(target_url, headers=headers)
    
    if response.status_code != 200:
        console.print(f"[bold red]無法訪問頁面，狀態碼: {response.status_code}[/bold red]")
        logging.error("無法訪問頁面，狀態碼: %s", response.status_code)
        return None, None
    
    # console.print(f"[green]成功取得頁面，長度: {len(response.text)} 字元[/green]")
    logging.info("成功取得頁面，長度: %s 字元", len(response.text))
    
    # 顯示從伺服器收到的 cookies
    if response.cookies:
        # console.print("[yellow]🍪 從伺服器收到的 cookies:[/yellow]")
        logging.info("從伺服器收到的 cookies:")
        for cookie in session.cookies:
            # console.print(f"  {cookie.name}={cookie.value}")
            logging.info("  %s=%s", cookie.name, cookie.value)
    
    # 解析 HTML 取得隱藏欄位
    soup = BeautifulSoup(response.text, 'html.parser')
    # soup = BeautifulSoup(response.content, 'lxml')
    
    viewstate = soup.find('input', {'name': '__VIEWSTATE'})
    viewstate_generator = soup.find('input', {'name': '__VIEWSTATEGENERATOR'})
    event_validation = soup.find('input', {'name': '__EVENTVALIDATION'})
    
    if not all([viewstate, viewstate_generator, event_validation]):
        # console.print("[bold red]❌ 無法找到必要的隱藏欄位，可能需要重新登入[/bold red]")
        # console.print(f"[red]找到 __VIEWSTATE: {viewstate is not None}[/red]")
        # console.print(f"[red]找到 __VIEWSTATEGENERATOR: {viewstate_generator is not None}[/red]")
        # console.print(f"[red]找到 __EVENTVALIDATION: {event_validation is not None}[/red]")
        logging.error("無法找到必要的隱藏欄位，可能需要重新登入")
        return None, None, None, None
    
    # console.print("[bold green]✅ 成功取得所有隱藏欄位[/bold green]")
    # console.print(f"[green]__VIEWSTATE 長度: {len(viewstate['value'])}[/green]")
    # console.print(f"[green]__VIEWSTATEGENERATOR: {viewstate_generator['value']}[/green]")
    # console.print(f"[green]__EVENTVALIDATION 長度: {len(event_validation['value'])}[/green]")
    logging.info("成功取得所有隱藏欄位")

    return viewstate, viewstate_generator, event_validation, session


def get_fresh_form_for_util_today(year_month=None, work_times=None):
    """生成表單資料
    Args:
        year_month (str): 年月，格式如 "2025/10"
        work_times (dict): 自訂的上下班時間和原因等資訊，格式如：
            {
                'arrival_time': '09:00',    # 預設上班時間
                'leave_time': '18:00',      # 預設下班時間
                'reason': '忘刷',           # 預設原因
                'remark': ''                # 預設備註
            }
    returns:
        tuple: (form_data dict, requests.Session object)
    """
    viewstate, viewstate_generator, event_validation, session = process_headers_cookies(year_month)
    if not all([viewstate, viewstate_generator, event_validation, session]):
        raise Exception("無法取得必要的隱藏欄位或 session，請檢查登入狀態。")
        # return None, None

    # 動態生成表單資料，自動填到今天為止
    fresh_form_data = generate_form_util_today(year_month,
                                               work_times)

    # 使用從網頁取得的最新隱藏欄位更新表單資料
    fresh_form_data['__VIEWSTATE'] = viewstate['value']
    fresh_form_data['__VIEWSTATEGENERATOR'] = viewstate_generator['value']
    fresh_form_data['__EVENTVALIDATION'] = event_validation['value']

    # return fresh_form_data, session. # 回傳給呼叫端進行後續提交 (命令互動使用)
    
    form_data = fresh_form_data
    if not form_data:
        logging.error("無法生成表單資料，請稍後再試。")
        # console.print("[bold red]無法生成表單資料，請稍後再試。[/bold red]")
        return

    post_headers = get_post_headers(year_month)
    submit_url = build_timesheet_url(year_month)
    response = session.post(submit_url, data=form_data, headers=post_headers, allow_redirects=False)
    logging.info("response status: %s", response.status_code)
    logging.info("response text: %s", response.text)

    return 'response status: ' + str(response.status_code) + \
        '\n' + 'response text: ' + str(response.text)


def get_fresh_form_for_target_dates(year_month=None, target_dates=None):
    """生成表單資料
    Args:
        year_month (str): 年月，格式如 "2025/10"
        target_dates (dict): 自訂的指定日期及其上下班時間和原因等資訊，格式如：
            {
                '20251101': {'arrival_time': '09:00', 'leave_time': '18:00', 'reason': '忘刷', 'remark': ''},
                '20251102': {'arrival_time': '09:15', 'leave_time': '18:15', 'reason': '忘刷', 'remark': ''},
                ...
            }
    returns:
        tuple: (form_data dict, requests.Session object)
    """
    viewstate, viewstate_generator, event_validation, session = process_headers_cookies(year_month)
    if not all([viewstate, viewstate_generator, event_validation, session]):
        return None, None

    # 動態生成表單資料，針對指定日期
    # target_dates = {
    #     '20251103': {'arrival_time': '09:03', 'leave_time': '18:03', 'reason': '忘刷', 'remark': ''},
    #     '20251105': {'arrival_time': '09:05', 'leave_time': '18:05', 'reason': '忘刷', 'remark': ''},
    # }
    fresh_form_data = generate_form_data_for_target_dates(year_month=year_month, 
                                                          target_dates=target_dates)

    # 使用從網頁取得的最新隱藏欄位更新表單資料
    fresh_form_data['__VIEWSTATE'] = viewstate['value']
    fresh_form_data['__VIEWSTATEGENERATOR'] = viewstate_generator['value']
    fresh_form_data['__EVENTVALIDATION'] = event_validation['value']

    # return fresh_form_data, session  # 回傳給呼叫端進行後續提交 (命令互動使用)

    form_data = fresh_form_data
    if not form_data:
        # console.print("[bold red]無法生成表單資料，請稍後再試。[/bold red]")
        return

    post_headers = get_post_headers(year_month)
    submit_url = build_timesheet_url(year_month)
    response = session.post(submit_url, data=form_data, headers=post_headers, allow_redirects=False)
    logging.info("response status: %s", response.status_code)
    logging.info("response text: %s", response.text)
    
    return 'response status: ' + str(response.status_code) + \
        '\n' + 'response text: ' + str(response.text)


# if __name__ == "__main__":
#     run_cli()

if __name__ == "__main__":
    get_fresh_form_for_util_today(year_month="2025/11",
                             work_times={
                                "arrival_time": "09:00",
                                "leave_time": "18:00",
                                "reason": "忘刷",
                                "remark": ""
                                })
