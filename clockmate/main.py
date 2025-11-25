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

import akasha
try:
    from .llm_clockmate import prompt_create, parse_llm_output
except:
    from llm_clockmate import prompt_create, parse_llm_output

#MCP錯誤處理
import os
import sys

# 優先在最前面設定環境變數（若 adapter 支援，最好從 connection_info 傳入 PYTHONIOENCODING/PYTHONUNBUFFERED）
os.environ.setdefault("PYTHONIOENCODING", "utf-8")
os.environ.setdefault("PYTHONUNBUFFERED", "1")
os.environ.setdefault("PYTHONUTF8", "1")

# 在 Python 層面重新設定 stdout/stderr 的編碼與 newline（Python 3.7+ 有 reconfigure）
try:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", newline="\n")
        sys.stderr.reconfigure(encoding="utf-8", newline="\n")
    else:
        # fallback for older envs
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", newline="\n")
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", newline="\n")
except Exception:
    # 不要把錯誤印到 stdout（會污染協定），寫到 stderr
    print("Failed to reconfigure stdio", file=sys.stderr)

# 載入環境變數
dotenv.load_dotenv()

BASE_TIMESHEET_URL = "https://hrwt.iii.org.tw/TSM/MyWorkTime.aspx"
TIMESHEET_ORIGIN = "https://hrwt.iii.org.tw"
console = Console()
figlet = Figlet(font="slant")


def build_timesheet_url(year_month=None):
    """Construct the timesheet URL optionally bound to a specific year/month."""
    if year_month:
        encoded_ym = quote(year_month)
        return f"{BASE_TIMESHEET_URL}?YM={encoded_ym}"
    return BASE_TIMESHEET_URL


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

def display_welcome_banner():
    ascii_banner = figlet.renderText("ClockMate")
    panel = Panel.fit(
        ascii_banner.rstrip(),
        border_style="cyan",
        title="ClockMate 工時小幫手",
        # subtitle="填報助手",
        style="bold magenta",
    )
    console.print(panel)
    # console.rule("[bold cyan]開始設定[/bold cyan]")


def prompt_with_default(prompt_text, default_value=None):
    if default_value:
        prompt = f"[bold white]{prompt_text}[/bold white] [[cyan]{default_value}[/cyan]]: "
    else:
        prompt = f"[bold white]{prompt_text}[/bold white]: "
    user_input = console.input(prompt).strip()
    return user_input or default_value


def prompt_yes_no(prompt_text, default=True):
    return Confirm.ask(f"[bold white]{prompt_text}[/bold white]", default=default)

def run_llm_cli():
    display_welcome_banner()
    now = datetime.datetime.now()
    target_year_month = f"{now.year}/{now.month:02d}"

    console.print("[bold]請輸入工時資料，直接按 Enter 會使用預設值。[/bold]")
    user_message = prompt_with_default("填寫本月出勤狀況", "")
    user_prompt = prompt_create(user_message=user_message)

    # 定義 MCP 伺服器連接資訊
    import sys
    connection_info = {
        "math": {
            "command": sys.executable,  # 使用當前 env 的 python
            "args": ["-u", "clockmate\llm_clockmate.py"],
            # "args": ["-u", "clockmate\llm_clockmate.py", "--mcp-stdio"],
            "transport": "stdio",
        },
    }

    # 使用 MCP 工具
    agent = akasha.agents(
        model="gemini:gemini-2.5-flash",
        temperature=1.0,
    )
    response = agent.mcp_agent(connection_info, "使用llm_clockmate取得工時資料")
    parsed_or_msg = parse_llm_output(response)

    # custom_work_times = get_per_day_work_times_by_llm(user_prompt=user_prompt)
    # parsed_or_msg = parse_llm_output(custom_work_times)

    if isinstance(parsed_or_msg, str):
        console.print(f"[yellow]I'm sorry, but I cannot assist with that request.{parsed_or_msg}[/yellow]")
        return
    else:
        console.print("[yellow]json正確生成.[/yellow]")

    if not prompt_yes_no("是否繼續並生成表單資料？", True):
        console.print("[yellow]⚠️ 已取消操作。[/yellow]")
        return

    form_data, session = get_fresh_form_llm_data(target_year_month, custom_work_times)
    if not form_data:
        console.print("[bold red]❌ 無法生成表單資料，請稍後再試。[/bold red]")
        return

    console.rule("[bold green]表單資料已完成建立[/bold green]")
    # if fetch_hidden and session:
    if session:
        if prompt_yes_no("需要立即提交表單嗎？", True):
            console.rule("[bold magenta]提交表單[/bold magenta]")
            console.print("📝 正在提交表單...")
            post_headers = get_post_headers(target_year_month)
            console.print(f"[dim]📋 使用 headers: {list(post_headers.keys())}[/dim]")

            submit_url = build_timesheet_url(target_year_month)
            response = session.post(submit_url, data=form_data, headers=post_headers, allow_redirects=False)

            console.print(f"[bold green]✅ 提交完成！狀態碼: {response.status_code}[/bold green]")

            if response.status_code == 302:
                location = response.headers.get('Location', '未知')
                console.print(f"[cyan]🔄 重定向到: {location}[/cyan]")

                if 'Default.aspx' not in location:
                    console.print("[bold green]🎉 表單提交可能成功！[/bold green]")
                else:
                    console.print("[bold red]❌ 被重定向到登入頁面，可能需要重新認證[/bold red]")
            elif response.status_code == 200:
                console.print("[cyan]📄 收到回應內容:[/cyan]")
                console.print(response.text[:300] + "..." if len(response.text) > 300 else response.text)
            else:
                console.print(f"[yellow]❓ 未預期的狀態碼: {response.status_code}[/yellow]")
                console.print(f"[yellow]回應內容: {response.text[:200]}[/yellow]")

            console.print(f"[dim]\n📊 回應標頭: {dict(response.headers)}[/dim]")
        else:
            console.print("[green]👌 表單資料已準備好，您可以稍後手動提交。[/green]")
    else:
        console.print("[blue]📦 表單資料已生成，請記得自行補上隱藏欄位後再提交。[/blue]")
        
def get_fresh_form_llm_data(year_month=None, work_times=None):
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
    
    console.print(f"[bold cyan]🌐 使用動態 User-Agent:[/bold cyan] {user_agent}")
    console.print(f"[bold cyan]💻 平台資訊:[/bold cyan] {platform_info}")
    
    # 設定重要的認證 cookies
    cookie_values = {
        'ASP.NET_SessionId': os.getenv("ASP_NET_SESSION_ID", ""),
        'clientTicket': os.getenv("CLIENT_TICKET", ""),
        'clientUserName': os.getenv("CLIENT_USERNAME", ""),
    }
    missing_cookies = [name for name, value in cookie_values.items() if not value]
    if missing_cookies:
        console.print(f"[yellow]⚠️ .env 中缺少 cookie 值: {', '.join(missing_cookies)}，請先執行 get_token.py[/yellow]")
    else:
        console.print("[green]✅ 已從 .env 讀取登入 cookie。[/green]")

    for name, value in cookie_values.items():
        if value:
            session.cookies.set(name, value, domain='hrwt.iii.org.tw')
    
    target_url = build_timesheet_url(year_month)
    console.print(f"[cyan]正在獲取最新的頁面資料: {target_url}[/cyan]")
    
    # 發送 GET 請求取得頁面
    response = session.get(target_url, headers=headers)
    
    if response.status_code != 200:
        console.print(f"[bold red]無法訪問頁面，狀態碼: {response.status_code}[/bold red]")
        return None, None
    
    console.print(f"[green]成功取得頁面，長度: {len(response.text)} 字元[/green]")
    
    # 顯示從伺服器收到的 cookies
    if response.cookies:
        console.print("[yellow]🍪 從伺服器收到的 cookies:[/yellow]")
        for cookie in session.cookies:
            console.print(f"  {cookie.name}={cookie.value}")
    
    # 解析 HTML 取得隱藏欄位
    soup = BeautifulSoup(response.text, 'html.parser')
    
    viewstate = soup.find('input', {'name': '__VIEWSTATE'})
    viewstate_generator = soup.find('input', {'name': '__VIEWSTATEGENERATOR'})
    event_validation = soup.find('input', {'name': '__EVENTVALIDATION'})
    
    if not all([viewstate, viewstate_generator, event_validation]):
        console.print("[bold red]❌ 無法找到必要的隱藏欄位，可能需要重新登入[/bold red]")
        console.print(f"[red]找到 __VIEWSTATE: {viewstate is not None}[/red]")
        console.print(f"[red]找到 __VIEWSTATEGENERATOR: {viewstate_generator is not None}[/red]")
        console.print(f"[red]找到 __EVENTVALIDATION: {event_validation is not None}[/red]")
        return None, None
    
    console.print("[bold green]✅ 成功取得所有隱藏欄位[/bold green]")
    console.print(f"[green]__VIEWSTATE 長度: {len(viewstate['value'])}[/green]")
    console.print(f"[green]__VIEWSTATEGENERATOR: {viewstate_generator['value']}[/green]")
    console.print(f"[green]__EVENTVALIDATION 長度: {len(event_validation['value'])}[/green]")
    
    # 動態生成表單資料
    fresh_form_data = generate_form_llm_data(year_month, work_times)
    
    # 使用從網頁取得的最新隱藏欄位更新表單資料
    fresh_form_data['__VIEWSTATE'] = viewstate['value']
    fresh_form_data['__VIEWSTATEGENERATOR'] = viewstate_generator['value']
    fresh_form_data['__EVENTVALIDATION'] = event_validation['value']
    
    return fresh_form_data, session

def generate_form_llm_data(year_month=None, 
                       default_work_times=None,
                       until_date=None):
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
    per_day_mode = False
    if isinstance(default_work_times, dict):
        base_keys = {"arrival_time", "leave_time", "reason", "remark"}
        if not base_keys.issubset(default_work_times.keys()):
            per_day_mode = True

    for day in range(1, (until_date) + 1):
        date_str = f"{year}{month:02d}{day:02d}"  # 格式: 20251001
        
        # 判斷是否為工作日 (週一到週五)
        date_obj = datetime.date(year, month, day)
        is_workday = date_obj.weekday() < 5  # 0-4 是週一到週五
        
        if per_day_mode:
            # 支援多種日期鍵格式：YYYYMMDD / YYYY-MM-DD / YYYY/MM/DD / MM-DD
            d_keys = [
                f"{year}{month:02d}{day:02d}",
                f"{year}-{month:02d}-{day:02d}",
                f"{year}/{month:02d}/{day:02d}",
                f"{month:02d}-{day:02d}",
            ]
            day_cfg = None
            for k in d_keys:
                if k in default_work_times:
                    day_cfg = default_work_times[k]
                    break

            if isinstance(day_cfg, dict):
                arr = day_cfg.get('arrival_time', '')
                lev = day_cfg.get('leave_time', '')
                rea = day_cfg.get('reason', '')
                rem = day_cfg.get('remark', '')
            else:
                arr = lev = rea = rem = ''

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
    
    console.print(f"[bold green]📅 生成 {year_month} 的表單資料[/bold green]")
    console.print(f"[cyan]📊 工作日: {len(work_days)} 天[/cyan]")
    console.print(f"[cyan]🏖️ 假日: {len(holidays)} 天[/cyan]")
    console.print(f"[magenta]⏰ 預設上班時間: {default_work_times['arrival_time']}[/magenta]")
    console.print(f"[magenta]⏰ 預設下班時間: {default_work_times['leave_time']}[/magenta]")
    
    return form_data


if __name__ == "__main__":
    run_llm_cli()
