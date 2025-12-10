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

# subprocess.Popen(
#         ["cmd.exe", "/K", f"mcp-google-map -p 3000 -k %{key_name}%"],
#         env=env,
#         creationflags=CREATE_NEW_CONSOLE
#     )
# print("已啟動新的 cmd 視窗（繼承 .env 變數）。")
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
# prompt = """從摩斯漢堡民生店到台北101的距離?"""               
# # 從摩斯漢堡民生店到臺北101的距離是4.6公里，開車大約需要19分鐘。
# prompt = """從摩斯漢堡民生店到台北101的時間?"""               
# # 從摩斯漢堡民生店到臺北101開車時間約19分鐘。
# prompt = """從摩斯漢堡民生店到台北101坐大眾交通工具的時間?"""  
# # 從摩斯漢堡民生店到臺北101搭乘大眾交通工具約需要 33 分鐘。
# prompt = """從摩斯漢堡民生店到台北101再到台北小巨蛋?"""       # tokens 16000/16000
"""從摩斯漢堡民生店開車到臺北101約3.7公里，預計需要16分鐘。接著從臺北101開車到臺北小巨蛋約3.4公里，預計需要12分鐘。"""
# prompt = """台北怎麼去台中?"""                              # tokens 16000/16000
"""從臺北到臺中，開車約需2小時4分鐘 (165公里)，主要會經過國道3號和國道1號。"""
# prompt = """現在從台北101怎麼去台中火車站?"""                    # tokens 16000/16000
"""
從臺北101到臺中火車站的交通方式如下：

1. **步行**：從臺北101步行6分鐘（0.2公里）到臺北101/世貿站。
2. **捷運**：從臺北101/世貿站搭乘淡水信義線（往淡水方向）捷運，經過7站，約14分鐘（6.5公里）到達臺北車站。
3. **步行**：從臺北車站步行4分鐘（0.1公里）到臺灣高鐵臺北站。
4. **高鐵**：從臺灣高鐵臺北站搭乘高鐵（往臺中方向），經過5站，約1小時（160公里）到達臺灣高鐵臺中站。
5. **步行**：從臺灣高鐵臺中站步行3分鐘（0.3公里）到臺灣高鐵臺中站公車站牌（靠近出口5）。
6. **公車**：從臺灣高鐵臺中站搭乘公車（往干城站方向），經過3站，約21分鐘（8.0公里）到達臺中車站（民族路口）。

總計旅程約1小時57分鐘，總距離約175公里。
"""
# prompt = """現在從松山機場怎麼去大直捷運站?"""                    # 
"""
從松山機場到大直捷運站，您可以搭乘捷運。全程約2.8公里，預計16分鐘。   # tokens default

**詳細步驟：**
1. 從松山機場站搭乘文湖線（往南港展覽館方向）。
2. 搭乘1站，約4分鐘，在「大直」站下車。
3. 從大直站出站（請走2號出口），步行約65公尺（約2分鐘）即可到達大直捷運站周邊。
"""
# prompt = """現在從台北火車站怎麼去大直捷運站?"""                 # tokens 8000/8000
"""
從臺北火車站前往大直捷運站，您可以搭乘捷運：

1.  從臺北火車站步行至捷運臺北車站，從M5入口進站。
2.  搭乘板南線 (藍線) 往南港展覽館方向，行經3站，在忠孝復興站下車。
3.  在忠孝復興站內轉乘文湖線 (棕線)。
4.  搭乘文湖線 (棕線) 往南港展覽館方向，行經4站，在大直站下車。
5.  從大直站2號出口出站，步行即可抵達目的地。

整個行程大約需要38分鐘，總距離約9.6公里。
"""
# prompt = "從台北101站到台中火車站" # 2500/2500
p = "從摩斯漢堡民生店到國立臺灣體育運動大學"
# p = "從摩斯漢堡民生店到南京復興捷運站"
prompt = p
prompt = f"""
        你是一個協助規劃路線的助手，依照以下步驟協助填寫出差單
        1.預設使用大眾交通工具規劃路線(maps_directions){p}
        2.當規畫中有需要搭乘公車的部分，將起始點與終點設為開車進行距離與時間測量，若搭乘公車前後有步行規劃，連同步行行程也納入開車計算
        3.若有改為開車，則使用計程車價格(taxi-budget)計算費用
        """

"""
從摩斯漢堡民生店到國立臺灣體育運動大學，預計搭乘大眾交通工具的路線總距離約183公里，總時長約2小時10分鐘，票價約新臺幣792 元。您預計在10:53 AM出發，並於1:03 PM抵達。路線涉及步行、公車、臺鐵區間車、高鐵和再次公車轉乘。詳細步驟包括：
1. 步行2分鐘（0.1公里）到介壽國中（小學）站。
2. 搭乘63號公車（往瑞湖街口方向）11分鐘（3.0公里），在松山車站（八德）下車。
3. 步行4分鐘（0.2公里）到松山車站。
4. 搭乘臺鐵區間車（往苗栗方向）7分鐘（6.3公里），在臺北車站下車。
5. 步行1分鐘（29公尺）到臺北高鐵站。
6. 搭乘高鐵（往左營方向）47分鐘（160公里），在臺中高鐵站下車。
7. 步行3分鐘（0.3公里）到臺灣高鐵臺中站。
8. 搭乘6882號公車（往干城站方向）24分鐘（11.5公里），在干城站下車。
9. 搭乘50號公車（往文英兒童公園方向）5分鐘（1.0公里），在臺中一中站下車。
10. 步行2分鐘（0.1公里）到國立臺灣體育運動大學。
"""

connection_info = {
    "google-map": {
        "url": "http://localhost:3000/mcp",
        "transport": "streamable_http",
    },
    "taxi-budget": {
        "command": "python",
        # "args": ["-m", "google_map.taxi_budget"],
        "args": ["google_map\\taxi_budget.py"],
        "transport": "stdio",
    },
}

## connection_info is the information of multiple MCP servers and  agent can use them to get the tools
## call_mcp_agent will call the agent and return the response
agent = akasha.agents(
    model=MODEL,
    temperature=0.3,
    verbose=True,
    keep_logs=True,
    max_input_tokens=20000,
    max_output_tokens=20000
)
response = agent.mcp_agent(connection_info, prompt)
print("Final response:")
print(response)

