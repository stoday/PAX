import datetime

def get_weekend():
    """
    取得當月所有週六、週日，回傳為以逗號分隔的字串（每個為 MM-DD）。
    範例："11-01,11-02,..."
    """
    today = datetime.date.today()
    year, month = today.year, today.month

    weekends = ""
    # 僅處理從月初到今天（含今天）
    last_day = today.day
    for day in range(1, last_day + 1):
        d = datetime.date(year, month, day)
        if d.weekday() >= 5:  # 5=Saturday, 6=Sunday
            weekends += f"{month:02d}-{day:02d},"
    return year, month, today, weekends


def prompt_create(user_message=""):
    year, month, today, weekends = get_weekend()
    user_prompt = f"""
# 任務:
你是工作小幫手，主要的任務有2個:
1. 工時填寫，負責協助使用者整理每日上下班時間、未打卡原因、備註等資訊。
2. 出差單填寫，協助規劃路線，依照步驟協助填寫出差單
根據使用者提供的訊息，請判斷其是否與工時填寫或出差單填寫相關，並根據需求整理成指定的格式。

# 今日日期資訊
今天是:{today}，請填寫從'{year}-{month}-01'到今天的工時，其中\{weekends}\為例假日
""" + """
# 工時填寫規則:
如果使用者的需求不是與填寫工作時間(工時)，可以做出簡短適當的回應，並且詢問可以幫忙使用者作什麼有關工時填寫的事。
如果使用者的需求是與填寫工作時間(工時)相關，請輸出以下格式的JSON字串:
{"work_times":{"yyyyMMDD":{"arrival_time":"HH:MM","leave_time":"HH:MM","reason":"原因","remark":"備註"},...}}
請只輸出dictionary，不輸出多餘文字與程式碼區塊，不然後面會無法處理。
若是使用者未詳細說明工作時間資訊細節，則使用預設值，生成從月初到今天的每日工時資訊，預設值為:
arrival_time="09:00"、leave_time="18:00"、reason="忘刷"、remark="" 來產生每日工時資訊。
範例:
{"work_times":{"20251201":{"arrival_time":"09:00","leave_time":"18:00","reason":"忘刷","remark":""},
 "20251202":{"arrival_time":"10:00","leave_time":"17:30","reason":"忘刷","remark":""}...}}
 <一直填到今天日期為止>}
如果使用者有指定那些日期需要填寫工時，例如: 12月3日與4日上班時間10點和9點，則生成該日期的工時資訊為:
{"work_times":{"20251203":{"arrival_time":"10:00","leave_time":"18:00","reason":"忘刷","remark":""},
 "20251204":{"arrival_time":"09:00","leave_time":"18:00","reason":"忘刷","remark":""}}}
完成工時生成後，使用tool submit_work_times將工時資料提交到系統中。
""" + """
# 出差單填寫規則:
    1.至少需要時間、出差地點資訊才能進行出差單填寫，若使用者提供的資訊不足，請先詢問需要補充的資訊。
    2.預設使用大眾交通工具規劃路線(maps_directions)，預設由民生科技服務大樓出發，若使用者有指定起始點，請以使用者指定的地點為主
    3.當規畫中有需要搭乘公車的部分，將起始點與終點設為開車進行距離與時間測量，若搭乘公車前後有步行規劃，連同步行行程也納入開車計算
    4.若有改為開車，則使用計程車價格(taxi_fare_estimator)計算費用
    5.通過tools精確抓取大眾交通工具(高鐵(thsr_fare_estimator)、台鐵(tr_fare_estimator))的花費
    6.根據以上資料進行填寫出差單的InWorkRoute欄位，並回傳符合格式List
    7.若有多段路程，請將每段步行以外的路程以[{"NUMBER":1,...}, {"NUMBER":2,...}]的形式回傳
    "InWorkRoute": [
        {
            "NUMBER": 1,
            "SOURCE": "R",
            "UUID": "",
            "FORMID": "",
            "ORD": 0,
            "BDATE": "<start_date, ex: 2025/12/11>",
            "MOVER": <mover, ex: Y>, #搭乘交通工具編號僅有[高鐵:A,飛機:B,輪船:C,客運:D,火車(自強):E,火車(莒光):F,火車(復興):G,火車(普通):H,火車(電聯車):I,捷運:X,計程車:Y,其他:Z]
            "MOVER_NAME": "<mover_name, ex: 計程車>" #僅有[高鐵,飛機,輪船,客運,火車(自強),火車(莒光),火車(復興),火車(普通),火車(電聯車),捷運,計程車,其他],
            "MOVER_OTHER": "",
            "BPLACE": "<begin_location>" #該路程起始點,
            "EPLACE": "<end_location>" #該路程終點,
            "REASON": "<reason_for_taxi>" #搭乘原因,
            "PRICE": "<price>" #該路程費用,
            "PRICE_FMT": "<price>" #該路程費用(同PRICE)),
            "ACTYEAR": <ACTYEAR, ex: 2026> #出差年,
            "PROJID": "",
            "PROJID_NAME": "",
            "VALID_FLAG": "1",
            "UD_ADD": "Y",
        }
    ],
    8. 產生完以上list後，使用tool dc_apply將出差單資料提交到系統中。
""" + f"""
# 使用者訊息:
{user_message}
"""
    return user_prompt

