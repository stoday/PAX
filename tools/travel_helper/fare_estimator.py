from mcp.server.fastmcp import FastMCP  # noqa: E402

mcp = FastMCP("math")

@mcp.tool()
def txai_fare_estimator(distance, city):
    """
    city: 縣市名稱 (string)，用於決定計價規則
    distance: 距離 (float)，單位為公里
    根據距離與縣市估算計程車費用，公式: 起跳價 + 續程費用 + 20% 彈性金額
    計算方式:
    1) 依縣市取得「起跳價」與「起程距離」 與 「續程單位距離」
    2) 若實際距離超過起程距離，續程距離 = (距離 - 起程距離)
    3) 小計 = 起跳價 + ceil(續程距離 / 每5元續程距離) * 5
    4) 總價 = 小計 * 1.2
    回傳格式: int 整數
    """
    # if distance is None or distance < 0:
    #     raise ValueError("distance 必須為非負數")

    # if not city:
    #     raise ValueError("city 不可為空")

    # 列出所有縣市與其對應的參數
    # 每縣市: start_fare(起跳價), start_distance(起程距離), unit_distance_per_5(每5元的續程距離)
    CITY_PRICING = {
        # 示例：起跳 85；起程 1.5km；每 0.25km 加 5 元
        "臺北市":   {"start_fare": 85, "start_distance": 1.25, "unit_distance_per_5": 0.2},
        "新北市":   {"start_fare": 85, "start_distance": 1.25, "unit_distance_per_5": 0.2},
        "基隆市":   {"start_fare": 85, "start_distance": 1.25, "unit_distance_per_5": 0.2},

        # 示例：起跳 90；起程 2.0km；每 0.30km 加 5 元
        "桃園市":   {"start_fare": 90, "start_distance": 1.25, "unit_distance_per_5": 0.2},
        "新竹市":   {"start_fare": 100, "start_distance": 1.25, "unit_distance_per_5": 0.2},
        "新竹縣":   {"start_fare": 100, "start_distance": 1.25, "unit_distance_per_5": 0.2},
        "苗栗縣":   {"start_fare": 100, "start_distance": 1.25, "unit_distance_per_5": 0.2},

        "臺中市":   {"start_fare": 85, "start_distance": 1.5, "unit_distance_per_5": 0.2},
        "彰化縣":   {"start_fare": 85, "start_distance": 1.25, "unit_distance_per_5": 0.2},
        "南投縣":   {"start_fare": 100, "start_distance": 1.5, "unit_distance_per_5": 0.25},

        "雲林縣":   {"start_fare": 100, "start_distance": 1.25, "unit_distance_per_5": 0.22},
        "嘉義市":   {"start_fare": 100, "start_distance": 1.25, "unit_distance_per_5": 0.22},
        "嘉義縣":   {"start_fare": 100, "start_distance": 1.25, "unit_distance_per_5": 0.22},
        "臺南市":   {"start_fare": 85, "start_distance": 1.25, "unit_distance_per_5": 0.2},

        "高雄市":   {"start_fare": 85, "start_distance": 1.25, "unit_distance_per_5": 0.2},
        "屏東縣":   {"start_fare": 100, "start_distance": 1.0, "unit_distance_per_5": 0.2},

        "宜蘭縣":   {"start_fare": 120, "start_distance": 1.5, "unit_distance_per_5": 0.25},
        "花蓮縣":   {"start_fare": 100, "start_distance": 1.0, "unit_distance_per_5": 0.23},
        "臺東縣":   {"start_fare": 100, "start_distance": 1.0, "unit_distance_per_5": 0.23},
        "連江縣":   {"start_fare": 120, "start_distance": 1.25, "unit_distance_per_5": 0.2},
        "金門縣":   {"start_fare": 100, "start_distance": 1.0, "unit_distance_per_5": 0.2},
        "澎湖縣":   {"start_fare": 120, "start_distance": 1.0, "unit_distance_per_5": 0.2},
    }

    # 查找前將 '台' 正規化為 '臺'，避免不同寫法導致查找失敗
    city_key = str(city).strip().replace("台", "臺")
    # 預設值：若找不到對應縣市，使用這組參數
    DEFAULT_PRICING = {"start_fare": 100, "start_distance": 1.0, "unit_distance_per_5": 0.25}
    cfg = CITY_PRICING.get(city_key, DEFAULT_PRICING)

    start_fare = cfg["start_fare"]
    start_distance = cfg["start_distance"]
    unit_distance = cfg["unit_distance_per_5"]

    # 計算續程距離
    import math
    extra_distance = max(0.0, float(distance) - float(start_distance))
    blocks = math.ceil(extra_distance / float(unit_distance)) if extra_distance > 0 else 0
    continuation_price = blocks * 5
    subtotal = float(start_fare) + continuation_price
    total = int(round(subtotal * 1.2))

    # 回傳整數（四捨五入）
    return total

@mcp.tool()
def thsr_fare_estimator(start, end):
    """
    高鐵(high speed railway, HSR)票價計算，
    start: 出發站 (string)
    end: 終點站 (string)
    以單一函式嘗試：
    1) 先從高鐵官方頁面抓取票價資訊（若可解析）
    2) 解析失敗則回退到內建票價表查詢
    回傳格式: dict:{"標準車廂":int, "商務車廂":int, "自由座車廂":int}
    """

    # 先將站名正規化（高鐵以 '台' 為主）
    start_key = str(start).strip().replace("臺", "台")
    end_key = str(end).strip().replace("臺", "台")

    # 中文站名轉英文代碼（THSR 查詢 API 常見代碼）
    zh_to_en = {
        "南港": "NanGang",
        "台北": "TaiPei",
        "板橋": "BanQiao",
        "桃園": "TaoYuan",
        "新竹": "XinZhu",
        "苗栗": "MiaoLi",
        "台中": "TaiZhong",
        "彰化": "ZhangHua",
        "雲林": "YunLin",
        "嘉義": "JiaYi",
        "台南": "TaiNan",
        "左營": "ZuoYing",
    }

    # 英文別名到官方代碼的對應（不分大小寫）
    en_aliases = {
        "nangang": "NanGang",
        "taipei": "TaiPei",
        "banqiao": "BanQiao",
        "taoyuan": "TaoYuan",
        "hsinchu": "XinZhu",
        "xinchu": "XinZhu",
        "miaoli": "MiaoLi",
        "taichung": "TaiZhong",
        "changhua": "ZhangHua",
        "zhanghua": "ZhangHua",
        "yunlin": "YunLin",
        "chiayi": "JiaYi",
        "tainan": "TaiNan",
        "zuoying": "ZuoYing",
    }

    start_en = zh_to_en.get(start_key)
    end_en = zh_to_en.get(end_key)

    # 若中文對應不到，嘗試英文別名（大小寫不敏感）
    if not start_en:
        start_en = en_aliases.get(str(start).strip().lower())
    if not end_en:
        end_en = en_aliases.get(str(end).strip().lower())

    # 若使用者直接傳官方代碼（如 TaiPei），也接受
    official_codes = set(zh_to_en.values())
    if not start_en and str(start).strip() in official_codes:
        start_en = str(start).strip()
    if not end_en and str(end).strip() in official_codes:
        end_en = str(end).strip()
    if not start_en or not end_en:
        raise ValueError(f"不支援的站名：{start} 或 {end}")

    import requests
    from datetime import datetime

    url = "https://www.thsrc.com.tw/TimeTable/Search"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
    }

    # 若未傳入日期，預設為今天（格式 YYYY/MM/DD）
    out_date = datetime.today().strftime("%Y/%m/%d")

    payload = {
        "SearchType": "S",
        "Lang": "TW",
        "StartStation": start_en,
        "EndStation": end_en,
        "OutWardSearchDate": out_date,
        "OutWardSearchTime": "11:30",
        "ReturnSearchDate": out_date,
        "ReturnSearchTime": "11:30",
    }

    res = requests.post(url, headers=headers, data=payload)

    # 回傳是 JSON
    data = res.json()
    price = {"標準車廂": data["data"]["PriceTable"]["Coach"][0], "商務車廂": data["data"]["PriceTable"]["Business"][0], "自由座車廂": data["data"]["PriceTable"]["Unreserved"][0]}
    return price

@mcp.tool()
def tr_fare_estimator(start, end, traintype):
    """
    台鐵票價計算
    start: 出發站 (string)
    end: 終點站 (string)
    traintype: 車種 (string)，如 "自強"、"莒光"、"復興"、"區間"等
    回傳格式: int 整數
    """

    # 先將站名正規化
    start_key = str(start).strip().replace("台", "臺")
    end_key = str(end).strip().replace("台", "臺")

    station_list=['0900-基隆','0910-三坑','0920-八堵','0930-七堵','0940-百福','0950-五堵','0960-汐止','0970-汐科','0980-南港','0990-松山','1000-臺北','1001-臺北-環島','1010-萬華','1020-板橋','1030-浮洲','1040-樹林','1050-南樹林','1060-山佳','1070-鶯歌','1075-鳳鳴','1080-桃園','1090-內壢','1100-中壢','1110-埔心','1120-楊梅','1130-富岡','1140-新富','1150-北湖','1160-湖口','1170-新豐','1180-竹北','1190-北新竹','1191-千甲','1192-新莊','1193-竹中','1194-六家','1201-上員','1202-榮華','1203-竹東','1204-橫山','1205-九讚頭','1206-合興','1207-富貴','1208-內灣','1210-新竹','1220-三姓橋','1230-香山','1240-崎頂','1250-竹南','2110-談文','2120-大山','2130-後龍','2140-龍港','2150-白沙屯','2160-新埔','2170-通霄','2180-苑裡','2190-日南','2200-大甲','2210-臺中港','2220-清水','2230-沙鹿','2240-龍井','2250-大肚','2260-追分','3140-造橋','3150-豐富','3160-苗栗','3170-南勢','3180-銅鑼','3190-三義','3210-泰安','3220-后里','3230-豐原','3240-栗林','3250-潭子','3260-頭家厝','3270-松竹','3280-太原','3290-精武','3300-臺中','3310-五權','3320-大慶','3330-烏日','3340-新烏日','3350-成功','3360-彰化','3370-花壇','3380-大村','3390-員林','3400-永靖','3410-社頭','3420-田中','3430-二水','3431-源泉','3432-濁水','3433-龍泉','3434-集集','3435-水里','3436-車埕','3450-林內','3460-石榴','3470-斗六','3480-斗南','3490-石龜','4050-大林','4060-民雄','4070-嘉北','4080-嘉義','4090-水上','4100-南靖','4110-後壁','4120-新營','4130-柳營','4140-林鳳營','4150-隆田','4160-拔林','4170-善化','4180-南科','4190-新市','4200-永康','4210-大橋','4220-臺南','4250-保安','4260-仁德','4270-中洲','4271-長榮大學','4272-沙崙','4290-大湖','4300-路竹','4310-岡山','4320-橋頭','4330-楠梓','4340-新左營','4350-左營','4360-內惟','4370-美術館','4380-鼓山','4390-三塊厝','4400-高雄','4410-民族','4420-科工館','4430-正義','4440-鳳山','4450-後庄','4460-九曲堂','4470-六塊厝','5000-屏東','5010-歸來','5020-麟洛','5030-西勢','5040-竹田','5050- 潮州','5060-崁頂','5070-南州','5080-鎮安','5090-林邊','5100-佳冬','5110-東海','5120-枋寮','5130-加祿','5140-內獅','5160-枋山','5190-大武','5200-瀧溪','5210-金崙','5220-太麻里','5230-知本','5240-康樂','6000-臺東','6010-山里','6020-鹿野','6030-瑞源','6040-瑞和','6050-關山','6060-海端','6070-池上','6080-富里','6090-東竹','6100-東里','6110-玉里','6120-三民','6130-瑞穗','6140-富源','6150-大富','6160-光復','6170-萬榮','6180-鳳林','6190-南平','6200-林榮新光','6210-豐田','6220-壽豐','6230-平和','6240-志學','6250-吉安','7000-花蓮','7010-北埔','7020-景美','7030-新城','7040-崇德','7050-和仁','7060-和平','7070-漢本','7080-武塔','7090-南澳','7100-東澳','7110-永樂','7120-蘇澳','7130-蘇澳新','7150-冬山','7160-羅東','7170-中里','7180-二結','7190-宜蘭','7200-四城','7210-礁溪','7220-頂埔','7230-頭城','7240-外澳','7250-龜山','7260-大溪','7270-大里','7280-石城','7290-福隆','7300-貢寮','7310-雙溪','7320-牡丹','7330-三貂嶺','7331-大華','7332-十分','7333-望古','7334-嶺腳','7335-平溪','7336-菁桐','7350-猴硐','7360-瑞芳','7361-海科館','7362-八斗子','7380-四腳亭','7390-暖暖']

    start_station = None
    end_station = None
    for s in station_list:
        if start_key in s:      # 中文部分包含即可
            start_station = s
        if end_key in s:
            end_station = s

    if not start_station or not end_station:
        raise ValueError(f"找不到對應的站名，start: {start}, end: {end}")

    # 車種與編號的對應表
    traintype_id_map = {
        "自強(3000)": "11",
        "太魯閣": "1",
        "普悠瑪": "2",
        "自強": "3",
        "莒光": "4",
        "復興": "5",
        "區間快": "10",
        "區間": "6"
    }

    from datetime import datetime
    train_type_code = traintype_id_map.get(str(traintype).strip(), str(traintype).strip())
    out_date = datetime.today().strftime("%Y/%m/%d")

    import requests
    from bs4 import BeautifulSoup

    # === Step 1: 建立 Session，保持 Cookie ===
    session = requests.Session()

    # === Step 2: 先 GET 頁面，取得 CSRF ===
    init_url = "https://www.railway.gov.tw/tra-tip-web/tip/tip001/tip114/query"
    r = session.get(init_url)

    soup = BeautifulSoup(r.text, "html.parser")
    csrf = soup.find("input", {"name": "_csrf"})["value"]
    print("取得 CSRF:", csrf)

    url = "https://www.railway.gov.tw/tra-tip-web/tip/tip001/tip114/query"

    data = {
        "_csrf": csrf,
        # "_csrf": "e906e410-14e1-48b4-8141-c58cfac5cd2e",
        "tip114QueryVOs[0].ticketDeadlineType": "ELECTRONIC_TICKET",
        "tip114QueryVOs[0].trnDate": out_date,
        "tip114QueryVOs[0].SpecLineExtEnum": "TIP_SPEC_LINE_OTHERS",
        "tip114QueryVOs[0].directionExtEnum": "TIP_DIR_UNUSED",
        "tip114QueryVOs[0].startStation": start_station,
        "tip114QueryVOs[0].endStation": end_station,
        "tip114QueryVOs[0].trainType": train_type_code,
        "tip114QueryVOs[0].ticketPriceType": "1",
        "tip114QueryVOs[0].ticketCount": "1",
        "query": ""
    }

    headers = {
        "Content-Type": "application/x-www-form-urlencoded"
    }

    res = requests.post(url, data=data, headers=headers)
    # print(res.text)

    html = res.text  # 你查詢後的回傳 HTML
    response = BeautifulSoup(html, "html.parser")

    # 找到 class="total" 的 tr
    total_row = response.find("tr", class_="total")

    if total_row:
        # 找到第二個 span 中的 strong
        price_tag = total_row.find("span", class_="red").find("strong")
        total_price = price_tag.text.strip()
        print(total_price)


    return total_price



if __name__ == "__main__":
    # # 測試範例
    # test_cases = [
    #     (5.0, "臺北市"),
    #     (10.0, "高雄市"),
    #     (3.5, "花蓮縣"),
    #     (8.2, "未知市"),  # 使用預設計價
    # ]
    # for distance, city in test_cases:
    #     fare = fare_estimator(distance, city)
    #     print(f"距離: {distance} km, 縣市: {city} => 計程車費用: {fare} 元")

        # # 測試範例
    # test_cases = [
    #     ("南港", "左營"),
    #     ("台北", "台中"),
    #     ("板橋", "左營"),
    #     ("桃園", "左營"),
    # ]
    # for start, end in test_cases:
    #     fare = thsr_fare_estimator(start, end)
    #     print(f"出發站: {start}, 終點站: {end} => 高鐵票價: {fare} 元")
 
    # tr_fare_estimator("台北", "台中")
        
    mcp.run(transport="stdio")
