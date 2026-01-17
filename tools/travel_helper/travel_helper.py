import os
import akasha  # noqa: E402
import dotenv
import subprocess
dotenv.load_dotenv()
key_name = "GOOGLE_MAP_API_KEY"
MODEL = "gemini:gemini-2.5-flash"
CREATE_NEW_CONSOLE = subprocess.CREATE_NEW_CONSOLE if hasattr(subprocess, "CREATE_NEW_CONSOLE") else 0x00000010

env = os.environ.copy()
val = env.get(key_name)
if not val:
        print(f"警告：環境變數 {key_name} 在 .env 中找不到（或為空）。仍會開啟 cmd 視窗，但 echo 會是空）。")
    # 傳 env 給子行程，並在新視窗裡 echo 該變數（/K 會保留視窗）
    # 注意：%VAR% 將在子 cmd 中被展開（子 cmd 能看到我們傳的 env）

subprocess.Popen(
        ["cmd.exe", "/K", "npm start"],
        cwd="./mcp-google-map",
        env=env,
        creationflags=CREATE_NEW_CONSOLE
    )
print("已啟動新的 cmd 視窗（繼承 .env 變數）。")
"""
tool:
search_nearby：根據位置搜尋附近地點，並可用關鍵字、距離、評分及營業時間篩選
get_place_details：取得特定地點的詳細資訊，包括聯絡方式、評論、評分與營業時間
maps_geocode：將地址或地名轉換為經緯度座標
maps_reverse_geocode：將經緯度座標轉換為可讀取的地址
maps_distance_matrix：計算多個起點與目的地之間的距離與行程時間
maps_directions：取得兩點之間的逐步導航路線（turn-by-turn）
maps_elevation：取得指定地點的海拔（高度）資料
"""


p = "從摩斯漢堡民生店到國立臺灣體育運動大學，不搭火車"
prompt = f"""
        你是一個協助規劃路線的助手，依照以下步驟協助填寫出差單
        1.預設使用大眾交通工具規劃路線(maps_directions){p}
        2.當規畫中有需要搭乘公車的部分，將起始點與終點設為開車進行距離與時間測量，若搭乘公車前後有步行規劃，連同步行行程也納入開車計算
        3.若有改為開車，則使用計程車價格(taxi_fare_estimator)計算費用
        4.通過tools精確抓取大眾交通工具(高鐵(thsr_fare_estimator)、台鐵(tr_fare_estimator))的花費
        5.根據以上資料進行填寫出差單的InWorkRoute欄位，並回傳符合格式List
        6.若有多段路程，請將每段步行以外的路程以[{{"NUMBER":1,...}}, {{"NUMBER":2,...}}]的形式回傳
        "InWorkRoute": [
        {{
            "NUMBER": 1,
            "SOURCE": "R",
            "UUID": "",
            "FORMID": "",
            "ORD": 0,
            "BDATE": "<start_date, ex: 2025/12/11>",
            "MOVER": "Y",
            "MOVER_NAME": "<mover_name, ex: 計程車>" #僅有[高鐵,飛機,輪船,客運,火車(自強),火車(莒光),火車(復興),火車(普通),火車(電聯車),捷運,計程車,其他],
            "MOVER_OTHER": "",
            "BPLACE": "<begin_location>" #該路程起始點,
            "EPLACE": "<end_location>" #該路程終點,
            "REASON": "<reason_for_taxi>" #搭乘原因,
            "PRICE": "<price>" #該路程費用,
            "PRICE_FMT": "<price>" #該路程費用(同PRICE)),
            "ACTYEAR": <ACTYEAR, ex: 2025> #出差年,
            "PROJID": "",
            "PROJID_NAME": "",
            "VALID_FLAG": "1",
            "UD_ADD": "Y",
        }}
    ],
        """

connection_info = {
    "google-map": {
        "url": "http://localhost:3000/mcp",
        "transport": "streamable_http",
    },
    "fare_estimator": {
        "command": "python",
        # "args": ["-m", "travel_helper.fare_estimator"],
        "args": ["travel_helper\\fare_estimator.py"],
        "transport": "stdio",
    },
}

## connection_info is the information of multiple MCP servers and  agent can use them to get the tools
## call_mcp_agent will call the agent and return the response
agent = akasha.agents(
    model=MODEL,
    temperature=0.3,
    verbose=False,
    keep_logs=False,
    max_input_tokens=20000,
    max_output_tokens=20000
)
response = agent.mcp_agent(connection_info, prompt)
print("Final response:")
print(response)

