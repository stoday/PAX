import requests
from bs4 import BeautifulSoup
import urllib.parse

class HRWorkTimeSession:
    def __init__(self):
        self.session = requests.Session()
        self.base_url = "https://hrwt.iii.org.tw"
        
    def login(self, username, password):
        """登入系統"""
        # 1. 先取得登入頁面，獲取 ViewState 等隱藏欄位
        login_url = f"{self.base_url}/Default.aspx"
        print(f"正在訪問登入頁面: {login_url}")
        
        response = self.session.get(login_url)
        if response.status_code != 200:
            print(f"無法訪問登入頁面，狀態碼: {response.status_code}")
            return False
            
        # 2. 解析登入頁面，提取隱藏欄位
        soup = BeautifulSoup(response.text, 'html.parser')
        viewstate = soup.find('input', {'name': '__VIEWSTATE'})
        viewstate_generator = soup.find('input', {'name': '__VIEWSTATEGENERATOR'})
        event_validation = soup.find('input', {'name': '__EVENTVALIDATION'})
        
        if not all([viewstate, viewstate_generator, event_validation]):
            print("無法找到必要的隱藏欄位")
            return False
            
        # 3. 準備登入資料
        login_data = {
            '__EVENTTARGET': '',
            '__EVENTARGUMENT': '',
            '__VIEWSTATE': viewstate['value'],
            '__VIEWSTATEGENERATOR': viewstate_generator['value'],
            '__EVENTVALIDATION': event_validation['value'],
            'ctl00$ContentPlaceHolder1$txtAccount': username,
            'ctl00$ContentPlaceHolder1$txtPassword': password,
            'ctl00$ContentPlaceHolder1$btnLogin': '登入'
        }
        
        # 4. 發送登入請求
        print("正在嘗試登入...")
        response = self.session.post(login_url, data=login_data, allow_redirects=False)
        
        print(f"登入回應狀態碼: {response.status_code}")
        if response.status_code == 302:
            location = response.headers.get('Location', '')
            print(f"重定向到: {location}")
            if 'MyWorkTime.aspx' in location or 'Main.aspx' in location:
                print("登入成功！")
                return True
            else:
                print("登入失敗，重定向到錯誤頁面")
                return False
        else:
            print("登入失敗")
            return False
    
    def get_worktime_page(self, year_month="2025/10"):
        """取得工時頁面"""
        encoded_ym = urllib.parse.quote(year_month)
        worktime_url = f"{self.base_url}/TSM/MyWorkTime.aspx?YM={encoded_ym}"
        
        print(f"正在訪問工時頁面: {worktime_url}")
        response = self.session.get(worktime_url)
        
        if response.status_code == 200:
            print("成功取得工時頁面")
            return response.text
        else:
            print(f"無法訪問工時頁面，狀態碼: {response.status_code}")
            return None
    
    def submit_worktime_form(self, form_data):
        """提交工時表單"""
        year_month = form_data.get('ctl00$ContentPlaceHolder1$txb_StDay', '2025/10')
        encoded_ym = urllib.parse.quote(year_month)
        submit_url = f"{self.base_url}/TSM/MyWorkTime.aspx?YM={encoded_ym}"
        
        print("正在提交工時表單...")
        response = self.session.post(submit_url, data=form_data, allow_redirects=False)
        
        print(f"提交回應狀態碼: {response.status_code}")
        if response.status_code == 302:
            location = response.headers.get('Location', '')
            print(f"重定向到: {location}")
        
        return response

# 使用範例
if __name__ == "__main__":
    # 創建 session
    hr_session = HRWorkTimeSession()
    
    # 登入（你需要提供實際的帳號密碼）
    username = input("請輸入帳號: ")
    password = input("請輸入密碼: ")
    
    if hr_session.login(username, password):
        # 取得工時頁面
        worktime_html = hr_session.get_worktime_page("2025/10")
        
        if worktime_html:
            # 解析頁面取得最新的 ViewState
            soup = BeautifulSoup(worktime_html, 'html.parser')
            viewstate = soup.find('input', {'name': '__VIEWSTATE'})
            viewstate_generator = soup.find('input', {'name': '__VIEWSTATEGENERATOR'})
            event_validation = soup.find('input', {'name': '__EVENTVALIDATION'})
            
            if all([viewstate, viewstate_generator, event_validation]):
                print("成功取得最新的隱藏欄位")
                print(f"ViewState 長度: {len(viewstate['value'])}")
                
                # 這裡你可以使用最新的隱藏欄位來提交表單
                # 你的原始表單資料...
            else:
                print("無法解析隱藏欄位")
    else:
        print("登入失敗")