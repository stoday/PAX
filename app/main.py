
import requests
from urllib.parse import quote
from urllib.parse import urlparse
import dotenv
from bs4 import BeautifulSoup
import platform
import sys
import datetime
import calendar


# 自動處理資料表單填寫與送出
year_month = "2025/10"
encoded_ym = quote(year_month)
URL = f"https://hrwt.iii.org.tw/TSM/MyWorkTime.aspx?YM={encoded_ym}"

# 使用 POST 送出表單資料
FORM_DATA = {
    # 填入從瀏覽器開發者工具觀察到的表單資料
    "__EVENTTARGET": "ctl00$ContentPlaceHolder1$btnEdit",
    "__EVENTARGUMENT": "",
    "__VIEWSTATE": "<GET_FROM_BROWSER>",
    "__VIEWSTATEGENERATOR": "<GET_FROM_BROWSER>",
    "__EVENTVALIDATION": "<GET_FROM_BROWSER>",
    "ctl00$ContentPlaceHolder1$txb_StDay": "2025/10",
    "ctl00$ContentPlaceHolder1$txtArr_20251001": "09:00",
    "ctl00$ContentPlaceHolder1$txtLev_20251001": "18:00",
    "ctl00$ContentPlaceHolder1$Dp_20251001": "忘刷",
    "ctl00$ContentPlaceHolder1$txtR_20251001": "",
    "ctl00$ContentPlaceHolder1$txtArr_20251002": "09:00",
    "ctl00$ContentPlaceHolder1$txtLev_20251002": "18:00",
    "ctl00$ContentPlaceHolder1$Dp_20251002": "忘刷",
    "ctl00$ContentPlaceHolder1$txtR_20251002": "",
    "ctl00$ContentPlaceHolder1$txtArr_20251003": "09:00",
    "ctl00$ContentPlaceHolder1$txtLev_20251003": "18:00",
    "ctl00$ContentPlaceHolder1$Dp_20251003": "忘刷",
    "ctl00$ContentPlaceHolder1$txtR_20251003": "",
    "ctl00$ContentPlaceHolder1$txtArr_20251004": "",
    "ctl00$ContentPlaceHolder1$txtLev_20251004": "",
    "ctl00$ContentPlaceHolder1$Dp_20251004": "",
    "ctl00$ContentPlaceHolder1$txtR_20251004": "",
    "ctl00$ContentPlaceHolder1$txtArr_20251005": "",
    "ctl00$ContentPlaceHolder1$txtLev_20251005": "",
    "ctl00$ContentPlaceHolder1$Dp_20251005": "",
    "ctl00$ContentPlaceHolder1$txtR_20251005": "",
    "ctl00$ContentPlaceHolder1$txtArr_20251006": "",
    "ctl00$ContentPlaceHolder1$txtLev_20251006": "",
    "ctl00$ContentPlaceHolder1$Dp_20251006": "",
    "ctl00$ContentPlaceHolder1$txtR_20251006": "",
    "ctl00$ContentPlaceHolder1$txtArr_20251007": "08:30",
    "ctl00$ContentPlaceHolder1$txtLev_20251007": "18:36",
    "ctl00$ContentPlaceHolder1$Dp_20251007": "忘刷",
    "ctl00$ContentPlaceHolder1$txtR_20251007": "",
    "ctl00$ContentPlaceHolder1$txtArr_20251008": "09:00",
    "ctl00$ContentPlaceHolder1$txtLev_20251008": "18:00",
    "ctl00$ContentPlaceHolder1$Dp_20251008": "忘刷",
    "ctl00$ContentPlaceHolder1$txtR_20251008": "",
    "ctl00$ContentPlaceHolder1$txtArr_20251009": "09:00",
    "ctl00$ContentPlaceHolder1$txtLev_20251009": "18:00",
    "ctl00$ContentPlaceHolder1$Dp_20251009": "忘刷",
    "ctl00$ContentPlaceHolder1$txtR_20251009": "",
    "ctl00$ContentPlaceHolder1$txtArr_20251010": "",
    "ctl00$ContentPlaceHolder1$txtLev_20251010": "",
    "ctl00$ContentPlaceHolder1$Dp_20251010": "",
    "ctl00$ContentPlaceHolder1$txtR_20251010": "",
    "ctl00$ContentPlaceHolder1$txtArr_20251011": "",
    "ctl00$ContentPlaceHolder1$txtLev_20251011": "",
    "ctl00$ContentPlaceHolder1$Dp_20251011": "",
    "ctl00$ContentPlaceHolder1$txtR_20251011": "",
    "ctl00$ContentPlaceHolder1$txtArr_20251012": "",
    "ctl00$ContentPlaceHolder1$txtLev_20251012": "",
    "ctl00$ContentPlaceHolder1$Dp_20251012": "",
    "ctl00$ContentPlaceHolder1$txtR_20251012": "",
    "ctl00$ContentPlaceHolder1$txtArr_20251013": "09:00",
    "ctl00$ContentPlaceHolder1$txtLev_20251013": "18:00",
    "ctl00$ContentPlaceHolder1$Dp_20251013": "忘刷",
    "ctl00$ContentPlaceHolder1$txtR_20251013": "",
    "ctl00$ContentPlaceHolder1$txtArr_20251014": "09:00",
    "ctl00$ContentPlaceHolder1$txtLev_20251014": "18:00",
    "ctl00$ContentPlaceHolder1$Dp_20251014": "忘刷",
    "ctl00$ContentPlaceHolder1$txtR_20251014": "",
    "ctl00$ContentPlaceHolder1$txtArr_20251015": "08:59",
    "ctl00$ContentPlaceHolder1$txtLev_20251015": "18:00",
    "ctl00$ContentPlaceHolder1$Dp_20251015": "忘刷",
    "ctl00$ContentPlaceHolder1$txtR_20251015": "",
    "ctl00$ContentPlaceHolder1$txtArr_20251016": "09:00",
    "ctl00$ContentPlaceHolder1$txtLev_20251016": "18:35",
    "ctl00$ContentPlaceHolder1$Dp_20251016": "忘刷",
    "ctl00$ContentPlaceHolder1$txtR_20251016": "",
    "ctl00$ContentPlaceHolder1$txtArr_20251017": "09:00",
    "ctl00$ContentPlaceHolder1$txtLev_20251017": "18:40",
    "ctl00$ContentPlaceHolder1$Dp_20251017": "忘刷",
    "ctl00$ContentPlaceHolder1$txtR_20251017": "",
    "ctl00$ContentPlaceHolder1$txtArr_20251018": "",
    "ctl00$ContentPlaceHolder1$txtLev_20251018": "",
    "ctl00$ContentPlaceHolder1$Dp_20251018": "",
    "ctl00$ContentPlaceHolder1$txtR_20251018": "",
    "ctl00$ContentPlaceHolder1$txtArr_20251019": "",
    "ctl00$ContentPlaceHolder1$txtLev_20251019": "",
    "ctl00$ContentPlaceHolder1$Dp_20251019": "",
    "ctl00$ContentPlaceHolder1$txtR_20251019": "",
    "ctl00$ContentPlaceHolder1$txtArr_20251020": "08:36",
    "ctl00$ContentPlaceHolder1$txtLev_20251020": "18:23",
    "ctl00$ContentPlaceHolder1$Dp_20251020": "忘刷",
    "ctl00$ContentPlaceHolder1$txtR_20251020": "",
    "ctl00$ContentPlaceHolder1$HidWkHCtrl": "20251004;20251005;20251006;20251010;20251011;20251012;20251018;20251019",
    "ctl00$ContentPlaceHolder1$HidWkACtrl": "20251001;20251002;20251003;20251008;20251009;20251013;20251014;20251015;20251016;20251017;20251020",
    "ctl00$ContentPlaceHolder1$HideStTimes": "",
    "ctl00$ContentPlaceHolder1$HidEdTimes": ""
}

def generate_form_data(year_month=None, default_work_times=None):
    """
    自動生成 FORM_DATA
    
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
    
    # 生成每一天的表單欄位
    work_days = []  # 記錄工作日
    holidays = []   # 記錄假日
    
    for day in range(1, days_in_month + 1):
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
    
    print(f"📅 生成 {year_month} 的表單資料")
    print(f"📊 工作日: {len(work_days)} 天")
    print(f"🏖️ 假日: {len(holidays)} 天")
    print(f"⏰ 預設上班時間: {default_work_times['arrival_time']}")
    print(f"⏰ 預設下班時間: {default_work_times['leave_time']}")
    
    return form_data

bearer_token = dotenv.get_key(".env", "TEL_BEARER_TOKEN")
parsed_url = urlparse(URL)
origin = f"{parsed_url.scheme}://{parsed_url.netloc}"

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
    
    print(f"🌐 使用動態 User-Agent: {user_agent}")
    print(f"💻 平台資訊: {platform_info}")
    
    # 設定重要的認證 cookies
    session.cookies.set('ASP.NET_SessionId', 'ixhecp5h5eyglywk52u4452s', domain='hrwt.iii.org.tw')
    session.cookies.set('clientTicket', 'acecc412-c129-4534-a52b-b5746b307421', domain='hrwt.iii.org.tw')
    session.cookies.set('clientUserName', '970123', domain='hrwt.iii.org.tw')
    
    print("正在獲取最新的頁面資料...")
    
    # 如果有指定年月，更新 URL
    if year_month:
        encoded_ym = quote(year_month)
        url = f"https://hrwt.iii.org.tw/TSM/MyWorkTime.aspx?YM={encoded_ym}"
    else:
        url = URL
        
    response = session.get(url, headers=headers)
    
    if response.status_code != 200:
        print(f"無法訪問頁面，狀態碼: {response.status_code}")
        return None, None
    
    print(f"成功取得頁面，長度: {len(response.text)} 字元")
    
    # 顯示從伺服器收到的 cookies
    if response.cookies:
        print("🍪 從伺服器收到的 cookies:")
        for cookie in session.cookies:
            print(f"  {cookie.name}={cookie.value}")
    
    # 解析 HTML 取得隱藏欄位
    soup = BeautifulSoup(response.text, 'html.parser')
    
    viewstate = soup.find('input', {'name': '__VIEWSTATE'})
    viewstate_generator = soup.find('input', {'name': '__VIEWSTATEGENERATOR'})
    event_validation = soup.find('input', {'name': '__EVENTVALIDATION'})
    
    if not all([viewstate, viewstate_generator, event_validation]):
        print("❌ 無法找到必要的隱藏欄位，可能需要重新登入")
        print(f"找到 __VIEWSTATE: {viewstate is not None}")
        print(f"找到 __VIEWSTATEGENERATOR: {viewstate_generator is not None}")
        print(f"找到 __EVENTVALIDATION: {event_validation is not None}")
        return None, None
    
    print("✅ 成功取得所有隱藏欄位")
    print(f"__VIEWSTATE 長度: {len(viewstate['value'])}")
    print(f"__VIEWSTATEGENERATOR: {viewstate_generator['value']}")
    print(f"__EVENTVALIDATION 長度: {len(event_validation['value'])}")
    
    # 動態生成表單資料
    fresh_form_data = generate_form_data(year_month, work_times)
    
    # 使用從網頁取得的最新隱藏欄位更新表單資料
    fresh_form_data['__VIEWSTATE'] = viewstate['value']
    fresh_form_data['__VIEWSTATEGENERATOR'] = viewstate_generator['value']
    fresh_form_data['__EVENTVALIDATION'] = event_validation['value']
    
    return fresh_form_data, session

def get_post_headers():
    """取得 POST 提交時的完整 headers（根據當前系統環境）"""
    user_agent = get_dynamic_user_agent()
    platform_info = get_dynamic_platform_info()
    
    return {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "Accept-Language": "zh-TW,zh;q=0.9,en;q=0.8",
        "Cache-Control": "max-age=0",
        "Connection": "keep-alive",
        "Content-Type": "application/x-www-form-urlencoded",
        "Host": "hrwt.iii.org.tw",
        "Origin": origin,
        "Referer": URL,
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

# 主要執行流程
if __name__ == "__main__":
    # 可以自訂年月和工作時間
    target_year_month = "2025/10"  # 或者設為 None 使用當前月份
    
    # 自訂工作時間（可選）
    custom_work_times = {
        'arrival_time': '09:00',
        'leave_time': '18:00', 
        'reason': '忘刷',
        'remark': ''
    }
    
    print(f"🚀 開始處理 {target_year_month or '當前月份'} 的工時表單")
    
    # 獲取最新的表單資料
    fresh_form_data, session = get_fresh_form_data(target_year_month, custom_work_times)
    
    if fresh_form_data and session:
        print("\n" + "="*50)
        print("📝 正在提交表單...")
        
        # 取得 POST 的完整 headers
        post_headers = get_post_headers()
        print(f"📋 使用 headers: {list(post_headers.keys())}")
        
        # 更新 URL 以匹配目標年月
        if target_year_month:
            encoded_ym = quote(target_year_month)
            submit_url = f"https://hrwt.iii.org.tw/TSM/MyWorkTime.aspx?YM={encoded_ym}"
        else:
            submit_url = URL
        
        # 使用相同的 session 提交表單（維持 cookie 狀態）
        response = session.post(submit_url, data=fresh_form_data, headers=post_headers, allow_redirects=False)
        
        print(f"✅ 提交完成！狀態碼: {response.status_code}")
        
        if response.status_code == 302:
            location = response.headers.get('Location', '未知')
            print(f"🔄 重定向到: {location}")
            
            # 如果重定向不是到登入頁面，表示可能成功
            if 'Default.aspx' not in location:
                print("🎉 表單提交可能成功！")
            else:
                print("❌ 被重定向到登入頁面，可能需要重新認證")
        elif response.status_code == 200:
            print("📄 收到回應內容:")
            print(response.text[:300] + "..." if len(response.text) > 300 else response.text)
        else:
            print(f"❓ 未預期的狀態碼: {response.status_code}")
            print(f"回應內容: {response.text[:200]}")
            
        print(f"\n📊 回應標頭: {dict(response.headers)}")
    else:
        print("❌ 無法獲取表單資料，請檢查網路連線或認證狀態")
