import requests
from bs4 import BeautifulSoup
from urllib.parse import quote

def get_fresh_viewstate():
    """取得最新的 ViewState 等隱藏欄位"""
    year_month = "2025/10"
    encoded_ym = quote(year_month)
    url = f"https://hrwt.iii.org.tw/TSM/MyWorkTime.aspx?YM={encoded_ym}"
    
    # 使用 session 維持 cookie
    session = requests.Session()
    
    print("正在取得最新的頁面資料...")
    response = session.get(url)
    
    if response.status_code != 200:
        print(f"無法訪問頁面，狀態碼: {response.status_code}")
        return None, None
    
    # 解析 HTML 取得隱藏欄位
    soup = BeautifulSoup(response.text, 'html.parser')
    
    viewstate = soup.find('input', {'name': '__VIEWSTATE'})
    viewstate_generator = soup.find('input', {'name': '__VIEWSTATEGENERATOR'})
    event_validation = soup.find('input', {'name': '__EVENTVALIDATION'})
    
    if not all([viewstate, viewstate_generator, event_validation]):
        print("無法找到必要的隱藏欄位，可能需要先登入")
        return None, None
    
    fresh_form_data = {
        "__EVENTTARGET": "ctl00$ContentPlaceHolder1$btnEdit",
        "__EVENTARGUMENT": "",
        "__VIEWSTATE": viewstate['value'],
        "__VIEWSTATEGENERATOR": viewstate_generator['value'],
        "__EVENTVALIDATION": event_validation['value'],
        "ctl00$ContentPlaceHolder1$txb_StDay": "2025/10",
        # 這裡加入你的其他表單資料...
        "ctl00$ContentPlaceHolder1$txtArr_20251001": "09:00",
        "ctl00$ContentPlaceHolder1$txtLev_20251001": "18:00",
        "ctl00$ContentPlaceHolder1$Dp_20251001": "忘刷",
        # ... 其他欄位
    }
    
    print("成功取得最新的隱藏欄位")
    print(f"ViewState 長度: {len(viewstate['value'])}")
    
    return fresh_form_data, session

if __name__ == "__main__":
    form_data, session = get_fresh_viewstate()
    
    if form_data and session:
        # 使用最新的表單資料提交
        url = "https://hrwt.iii.org.tw/TSM/MyWorkTime.aspx?YM=2025%2f10"
        
        response = session.post(url, data=form_data, allow_redirects=False)
        print(f"提交結果狀態碼: {response.status_code}")
        
        if response.status_code == 302:
            print(f"重定向到: {response.headers.get('Location')}")
        else:
            print(f"回應內容: {response.text[:200]}...")