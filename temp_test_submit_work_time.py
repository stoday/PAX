# -*- coding: utf-8 -*-
import os
import sys
import json
import datetime
import dotenv

# 確保路徑正確
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

from core.actions.submit_work_time import submit_work_time
from core.actions.utils import get_auth_cookies

# 強制設定 stdout 為 UTF-8，解決 Windows 終端機亂碼問題
if sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except:
        pass

def run_test():
    print("=== Pax Work Time Submission Test CLI ===")
    
    # 強制重新載入 .env
    dotenv.load_dotenv(override=True)
    
    cookies = get_auth_cookies()
    print(f"Current Cookies in .env:")
    for k, v in cookies.items():
        val_display = f"{v[:10]}...{v[-5:]}" if v and len(v) > 15 else v
        print(f"  {k}: {val_display}")
        
    if not cookies.get('ASP.NET_SessionId'):
        print("Error: Missing ASP.NET_SessionId in .env!")
        return

    # 準備一個簡單的測試資料 (今天 09:00 - 18:00)
    # today = datetime.datetime.now().strftime("%Y%m%d")
    today = "20260116"
    test_params = {
        "work_times": {
            today: {
                "arrival_time": "08:30",
                "leave_time": "18:29",
                "reason": "忘刷",
                "remark": "Test from CLI"
            }
        }
    }
    
    print(f"\nTarget Date: {today}")
    
    # 這裡我們模擬 submit_work_time 內部的步驟，以便顯示 payload
    from core.actions.submit_work_time import generate_form_payload, BASE_TIMESHEET_URL
    import requests
    from bs4 import BeautifulSoup
    
    session = requests.Session()
    for name, value in cookies.items():
        if value: session.cookies.set(name, value, domain='hrwt.iii.org.tw')
    
    print("Fetching form fields (GET)...")
    resp = session.get(BASE_TIMESHEET_URL, timeout=20)
    # 這裡也要處理編碼
    resp.encoding = resp.apparent_encoding or "utf-8"
    soup = BeautifulSoup(resp.text, 'html.parser')
    
    year_month = f"{datetime.datetime.now().year}/{datetime.datetime.now().month:02d}"
    payload = generate_form_payload(year_month, test_params["work_times"], soup)
    
    if payload:
        print("\n--- GENERATED PAYLOAD (Partial) ---")
        for k, v in payload.items():
            if (v and "txtArr_" in k) or (v and "txtLev_" in k) or (v and "Dp_" in k) or k.startswith("__"):
                val_display = str(v)
                if len(val_display) > 30:
                    val_display = f"{val_display[:20]}..."
                
                # 嘗試安全打印
                try:
                    print(f"  {k}: {val_display}")
                except UnicodeEncodeError:
                    # 如果環境編碼有問題，至少不崩潰
                    print(f"  {k}: [Value containing CJK characters]")
        print("-----------------------------------\n")
    
    print("Submitting (POST)...")
    # 呼叫原本的函式來執行最後的動作 (會再跑一次流程，但在測試時沒關係)
    result = submit_work_time(cookies=cookies, **test_params)
    
    print("\n" + "="*40)
    print(f"RESULT STATUS: {result.get('status')}")
    print(f"RESULT MESSAGE: {result.get('message')}")
    if 'details' in result:
        print(f"DETAILS: {result.get('details')}")
    print("="*40)
    
    if result.get('status') == 'success':
        print("\n[OK] 提交動作已完成。請立即開啟網頁檢查該日(today)的工時。")
    else:
        print("\n[FAIL] 提交失敗。可能是 Session 已失效或表單欄位不吻合。")

if __name__ == "__main__":
    run_test()
