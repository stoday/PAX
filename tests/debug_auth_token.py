# -*- coding: utf-8 -*-
"""
認證資訊手動診斷工具
從 .env 讀取 Cookie 並直接測試存取工時系統
"""

import os
import requests
from bs4 import BeautifulSoup
import dotenv

# 載入 .env
dotenv.load_dotenv()

def debug_check_auth():
    target_url = "https://hrwt.iii.org.tw/TSM/MyWorkTime.aspx"
    
    # 從環境變數讀取
    session_id = os.getenv("ASP_NET_SESSION_ID")
    ticket = os.getenv("CLIENT_TICKET")
    username = os.getenv("CLIENT_USERNAME")
    
    print("=== [認證診斷] ===")
    print(f"ASP.NET_SessionId: {session_id[:10]}..." if session_id else "❌ 缺失")
    print(f"clientTicket: {ticket[:10]}..." if ticket else "❌ 缺失")
    print(f"clientUserName: {username}" if username else "❌ 缺失")
    
    if not all([session_id, ticket, username]):
        print("\n[結果] ❌ 認證資訊不全，請先執行 get_token.py")
        return

    # 建立 Session
    session = requests.Session()
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "zh-TW,zh;q=0.9,en;q=0.8",
    }
    
    # 設定 Cookie (注意 Domain)
    cookies = {
        'ASP.NET_SessionId': session_id,
        'clientTicket': ticket,
        'clientUserName': username
    }
    
    print("\n正在嘗試連接工時系統...")
    try:
        # 這裡不允許重定向，以便觀察是否被踢走
        response = session.get(target_url, headers=headers, cookies=cookies, allow_redirects=False, timeout=15)
        
        print(f"回應狀態碼: {response.status_code}")
        
        if response.status_code == 302:
            location = response.headers.get('Location', '')
            print(f"❌ 認證失敗！伺服器要求重定向至: {location}")
            if "Login.aspx" in location:
                print(">>> 診斷: Cookie 已失效或不適用於此網域。")
        
        elif response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            # 檢查頁面是否包含常用的登入特徵 (例如 '退下' 或 '登出' 或是工時表單)
            if "MyWorkTime" in response.text or soup.find('input', {'name': '__VIEWSTATE'}):
                print("✅ 認證成功！已成功進入工時系統頁面。")
                # 試著抓取姓名
                user_label = soup.find(id="ctl00_lblUserName") # 假設的 ID
                if user_label:
                    print(f"登入身份: {user_label.text}")
            else:
                print("❓ 狀態碼為 200 但內容疑似非工時頁面 (可能仍在登入過程中)。")
                print(f"頁面標題: {soup.title.string if soup.title else '無標題'}")
        
        else:
            print(f"❌ 未預期的錯誤，狀態碼: {response.status_code}")

    except Exception as e:
        print(f"❌ 請求發生異常: {e}")

if __name__ == "__main__":
    debug_check_auth()
