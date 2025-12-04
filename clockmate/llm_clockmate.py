import datetime
import json
import re
from typing import Dict, Tuple, List, Any, Union

import akasha

import dotenv
dotenv.load_dotenv()
from mcp.server.fastmcp import FastMCP  # noqa: E402
mcp = FastMCP("parse_llm_output")


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

def prompt_create(user_message = ""):
    year, month, today, weekends = get_weekend()
    date_prompt = f"今天是:{today}，請填寫從'{year}-{month}-01'到今天的工時，其中\{weekends}\為例假日"
    user_prompt = f"""
    最高優先級指令：僅可輸出dictionary格式
    1.嚴格檢查使用者訊息"{user_message}"
    2.優先判斷，若使用者訊息為空字串，則直接判斷為相關
    3.其次判斷使用者訊息是否與「上下班時間」、「未打卡原因」、「混合工作/公出/受訓」等無關(僅字面提及也不算(如混合工作好爽、受訓好累、不想公出))。
    4.如果使用者訊息被判定為「無關」、「未提及」請立刻停止執行所有後續指令，並且"只輸出"以下單一 JSON 對象：
    \{{"message":""\}} 該message對應的value請使用友善且禮貌的口吻提醒使用者你是負責填寫工時的小幫手，無法協助，如果有填寫工時的需要歡迎找你
    如果內容被判定為「相關」，則繼續執行以下指令：
    請只輸出dictionary，不輸出多餘文字與程式碼區塊。
    {date_prompt}
    優先根據使用者訊息的要求，將每日的上下班時間、未打卡事由、備註等資訊整理成 JSON 格式。
    若使用者訊息為空白，則直接填入預設值
    若使用者訊息有簡短字句但過於簡短以致無法確認意圖(如:10點，受訓、忘刷)，
    請依照\{{"reask":"請問..."\}}格式回覆，根據針對簡短輸入的回問策略，產生一個簡潔、禮貌且具體的回問語句，引導使用者提供缺失的關鍵資訊（日期與時間及原因），提供使用者確認:
    
    當例假日時，\{{MM-DD:\{{"arrival_time":"","leave_time":"","reason":"","remark":""\}},...\}} 
    當使用者訊息有混合工作、公出、受訓的情況，則在reason中輸入\{{MM-DD:\{{"arrival_time":"HH:MM","leave_time":"HH:MM","reason":"混合工作/公出/受訓(擇一)","remark":""\}},...\}}
    其他未提及的日期則填入預設值\{{arrival_time="09:00"、leave_time="18:00"、reason="忘刷"、remark=""\}}

    對話紀錄:
    """
    return user_prompt

def get_per_day_work_times_by_llm(
        model: str = "gemini:gemini-2.5-flash",
        user_prompt: str = "",
        info: str = "",
    ):
    user_prompt = prompt_create()
    model = "gemini:gemini-2.5-flash"
    ak = akasha.ask(model=model, max_input_tokens=8000, max_output_tokens=20000)
    res = ak(prompt=user_prompt)
    return res

TIME_PATTERN = re.compile(r"^([01]\d|2[0-3]):[0-5]\d$")

def validate_llm_json(parsed: Dict[str, Any]) -> Tuple[bool, str, Dict[str, Dict[str, str]]]:
    """
    驗證已解析的 JSON 物件（dict）。
    規則簡化：
    1) 期望是一個日期→物件 的 dict（message-only 應在 parse_llm_output 前置處理）。
    2) 每個日期的物件需包含四鍵：arrival_time, leave_time, reason, remark。
    3) arrival_time/leave_time 若非空字串，需為 HH:MM 格式。

    回傳: (ok, first_error_str, data_dict)
    """
    required_fields = ["arrival_time", "leave_time", "reason", "remark"]
    result: Dict[str, Dict[str, str]] = {}

    for date_key, payload in parsed.items():
        if not isinstance(payload, dict):
            return False, f"日期 {date_key} 的值不是 dict", parsed

        missing = [f for f in required_fields if f not in payload]
        if missing:
            return False, f"日期 {date_key} 缺少欄位: {','.join(missing)}", {}

        arrival = str(payload.get("arrival_time", ""))
        leave = str(payload.get("leave_time", ""))
        reason = str(payload.get("reason", ""))
        remark = str(payload.get("remark", ""))

        if arrival and not TIME_PATTERN.match(arrival):
            return False, f"{date_key} arrival_time 格式錯誤: {arrival}", {}
        if leave and not TIME_PATTERN.match(leave):
            return False, f"{date_key} leave_time 格式錯誤: {leave}", {}

        result[date_key] = {
            "arrival_time": arrival,
            "leave_time": leave,
            "reason": reason,
            "remark": remark,
        }

    return True, "", result

def _clean_and_parse(raw_text: str) -> Tuple[bool, Dict[str, Any]]:
    """標準化並嘗試解析為 JSON 物件(dict)。

    清理規則：
    - 移除多餘空白（標準化空白，去除冒號、逗號、花括號周邊空白）
    - 移除所有三個反引號 "```"
    """
    cleaned = raw_text.strip()
    # 移除所有三個反引號
    cleaned = cleaned.replace("```", "")

    # 標準化冒號、逗號周邊空白，以及花括號周邊空白
    cleaned = re.sub(r"\s*:\s*", ":", cleaned)
    cleaned = re.sub(r"\s*,\s*", ",", cleaned)
    cleaned = re.sub(r"\s*\{\s*", "{", cleaned)
    cleaned = re.sub(r"\s*\}\s*", "}", cleaned)

    try:
        maybe = json.loads(cleaned)
        if isinstance(maybe, dict):
            return True, maybe
        return False, raw_text
    except Exception as e:
        return False, e

@mcp.tool()
def parse_llm_output(raw_text: str) -> Union[str, Dict[str, Dict[str, str]]]:
    """
    解析模型輸出：
    - 若為 {"message": "..."}，直接回傳該訊息字串（不再做驗證）。
    - 否則執行格式驗證，通過則回傳日期→工時的 dict，失敗則拋出 ValueError。
    """
    ok_parse, parsed = _clean_and_parse(raw_text)
    if not ok_parse:
        return f"很抱歉，麻煩再試一次:{parsed}"

    if ok_parse:
        # 統一檢查：message-only（與工作無關）
        if set(parsed.keys()) == {"message"} and isinstance(parsed.get("message"), str):
            return {"message": parsed.get("message")}
        # 統一檢查：reask 需求
        if set(parsed.keys()) == {"reask"} and isinstance(parsed.get("reask"), str):
            return {"reask": parsed.get("reask")}

    # 檢查格式有效性
    ok, err, data = validate_llm_json(parsed)
    if not ok:
        return err or "格式驗證失敗"
    return data

if __name__ == "__main__":
    mcp.run(transport="stdio")