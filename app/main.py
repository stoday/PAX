
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


def generate_form_data(year_month=None, 
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
    
    console.print(f"[bold green]📅 生成 {year_month} 的表單資料[/bold green]")
    console.print(f"[cyan]📊 工作日: {len(work_days)} 天[/cyan]")
    console.print(f"[cyan]🏖️ 假日: {len(holidays)} 天[/cyan]")
    console.print(f"[magenta]⏰ 預設上班時間: {default_work_times['arrival_time']}[/magenta]")
    console.print(f"[magenta]⏰ 預設下班時間: {default_work_times['leave_time']}[/magenta]")
    
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

def get_fresh_form_data(year_month=None, work_times=None):
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
        "Authorization": f"Bearer {os.getenv('TEL_BEARER_TOKEN', '')}",
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
    
    cookies = {
        "token": os.getenv("TEL_COOKIE_TOKEN", ""),
    }
    if not cookies["token"]:
        console.print("[yellow]⚠️ .env 中缺少 token Cookie，請執行 get_token.py 更新。[/yellow]")
    session.cookies.update(cookies)
    
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
    
    if not event_validation:
        event_validation = soup.find('input', {'id': '__EVENTVALIDATION'})
        if event_validation:
            console.print("[yellow]⚠️ 注意: 使用了 id 來尋找 __EVENTVALIDATION，可能是頁面結構異常。[/yellow]")
        else:
            console.print("[red]❌ 無法找到 __EVENTVALIDATION 欄位。[/red]")
            event_validation = {'value':'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'}
    
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
    fresh_form_data = generate_form_data(year_month, work_times)
    
    # 使用從網頁取得的最新隱藏欄位更新表單資料
    fresh_form_data['__VIEWSTATE'] = viewstate['value']
    fresh_form_data['__VIEWSTATEGENERATOR'] = viewstate_generator['value']
    fresh_form_data['__EVENTVALIDATION'] = event_validation['value']
    
    return fresh_form_data, session

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


def run_cli():
    display_welcome_banner()
    now = datetime.datetime.now()
    default_year_month = f"{now.year}/{now.month:02d}"

    console.print("[bold]請輸入工時資料，直接按 Enter 會使用預設值。[/bold]")
    target_year_month = prompt_with_default("填寫年月 (YYYY/MM)", default_year_month)
    arrival_time = prompt_with_default("預設上班時間 (HH:MM)", "09:00")
    leave_time = prompt_with_default("預設下班時間 (HH:MM)", "18:00")
    reason = prompt_with_default("預設原因", "忘刷")
    remark = console.input("[bold white]預設備註 (可留空)[/bold white]: ").strip()

    custom_work_times = {
        'arrival_time': arrival_time,
        'leave_time': leave_time,
        'reason': reason,
        'remark': remark
    }

    summary_table = Table(show_header=False, box=box.SIMPLE_HEAVY)
    summary_table.add_row("✨ 年月", target_year_month)
    summary_table.add_row("⏰ 上班/下班", f"{arrival_time} - {leave_time}")
    summary_table.add_row("📝 原因", reason)
    summary_table.add_row("💬 備註", remark or "（無）")

    console.rule("[bold cyan]設定摘要[/bold cyan]")
    console.print(summary_table)

    if not prompt_yes_no("是否繼續並生成表單資料？", True):
        console.print("[yellow]⚠️ 已取消操作。[/yellow]")
        return

    fetch_hidden = prompt_yes_no("要自動從系統取得最新的隱藏欄位嗎？", True)

    form_data = None
    session = None

    if fetch_hidden:
        console.print("[cyan]🔍 嘗試從遠端抓取最新表單設定...[/cyan]")
        form_data, session = get_fresh_form_data(target_year_month, custom_work_times)
        if not form_data:
            console.print("[yellow]⚠️ 遠端資料抓取失敗，改用離線方式生成。[/yellow]")
            form_data = generate_form_data(target_year_month, custom_work_times)
    else:
        form_data = generate_form_data(target_year_month, custom_work_times)

    if not form_data:
        console.print("[bold red]❌ 無法生成表單資料，請稍後再試。[/bold red]")
        return

    console.rule("[bold green]表單資料已完成建立[/bold green]")
    if fetch_hidden and session:
        if prompt_yes_no("需要立即提交表單嗎？", False):
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


if __name__ == "__main__":
    run_cli()
