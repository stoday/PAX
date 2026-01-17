# -*- coding: utf-8 -*-
import datetime
import os

def get_weekend():
    """
    取得當月所有週六、週日，回傳為以逗號分隔的字串（每個為 MM-DD）。
    """
    today = datetime.date.today()
    year, month = today.year, today.month

    weekends = ""
    last_day = today.day
    for day in range(1, last_day + 1):
        d = datetime.date(year, month, day)
        if d.weekday() >= 5:  # 5=Saturday, 6=Sunday
            weekends += f"{month:02d}-{day:02d},"
    return year, month, today, weekends


def prompt_create(user_message=""):
    """
    建立 LLM Prompt，會自動判斷當前 PAX_MODE 來調整指令
    """
    year, month, today, weekends = get_weekend()
    pax_mode = os.getenv("PAX_MODE", "local").lower()
    
    # 基礎 Prompt 部分
    base_prompt = f"""
# 任務:
你是工作小幫手，主要的任務有2個:
1. 工時填寫，負責協助使用者整理每日上下班時間、未打卡原因、備註等資訊。
2. 出差單填寫，協助規劃路線，依照步驟協助填寫出差單
根據使用者提供的訊息，請判斷其是否與工時填寫或出差單填寫相關，並根據需求整理成指定的格式。

# 今日日期資訊
今天是:{today}，請填寫從'{year}-{month}-01'到今天的工時，其中\{weekends}\為例假日
"""

    # 針對模式調整指令
    if pax_mode == "cloud":
        mode_instruction = """
# 模式指令 (雲端模式 - Cloud Mode):
你目前正在雲端伺服器運行。你「不具備」直接操作使用者網頁或提交系統的權限。
因此，當你需要執行「提交工時」或「填寫出差單」的操作時，請務必將指令封裝成以下 JSON 格式回傳，
這會讓使用者的本地端收到底稿後自動執行真正的手動/API 操作：

{
  "response": "給使用者的親切回應（說明你幫他準備了什麼）",
  "action": "指令名稱 (例如: submit_work_time 或 apply_travel)",
  "params": { 
      "work_times": { ...工時資料... },
      "InWorkRoute": [ ...出差路線資料... ]
  }
}
*注意：若只是普通對話，action 請填寫 "echo"，params 填寫 {"message": "你的回覆"}。請務必輸出合法的 JSON 字串。*
"""
    else:
        mode_instruction = """
# 模式指令 (本地模式 - Local Mode):
你具備直接呼叫工具的操作權限。
1. 工時填寫：請生成格式如 {"work_times":{...}} 的 JSON 並呼叫 submit_work_times 工具。
2. 出差單填寫：請呼叫 dc_apply 工具。
"""

    rule_sections = """
# 工時填寫規則:
若是使用者未詳細說明工作時間資訊細節，則使用預設值：
arrival_time="09:00"、leave_time="18:00"、reason="忘刷"、remark="" 來產生每日工時資訊。

# 出差單填寫規則:
1. 預設使用大眾交通工具規劃路線(maps_directions)
2. 通過工具精確抓取交通花費，並整理成 InWorkRoute 格式。
"""

    final_prompt = base_prompt + mode_instruction + rule_sections + f"""
# 使用者訊息:
{user_message}
"""
    return final_prompt
