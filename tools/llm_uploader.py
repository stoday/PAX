import calendar
import datetime
import os
import platform
import sys
from urllib.parse import quote

import requests
from bs4 import BeautifulSoup
import dotenv
from mcp.server.fastmcp import FastMCP


dotenv.load_dotenv()

mcp = FastMCP("submit_work_times")

BASE_TIMESHEET_URL = "https://hrwt.iii.org.tw/TSM/MyWorkTime.aspx"

def build_timesheet_url(year_month=None):
    """Construct the timesheet URL optionally bound to a specific year/month."""
    if year_month:
        encoded_ym = quote(year_month)
        return f"{BASE_TIMESHEET_URL}?YM={encoded_ym}"
    return BASE_TIMESHEET_URL


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

    for day in range(1, (until_date) + 1):
        date_str = f"{year}{month:02d}{day:02d}"  # 格式: 20251001
        
        # 判斷是否為工作日 (週一到週五)
        date_obj = datetime.date(year, month, day)
        is_workday = date_obj.weekday() < 5  # 0-4 是週一到週五
        
        if mode == "llm":
            if isinstance(default_work_times, dict):
                arr = default_work_times.get(date_str, {}).get('arrival_time', '')
                lev = default_work_times.get(date_str, {}).get('leave_time', '')
                rea = default_work_times.get(date_str, {}).get('reason', '')
                rem = default_work_times.get(date_str, {}).get('remark', '')
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
        "Origin": "https://hrwt.iii.org.tw",
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