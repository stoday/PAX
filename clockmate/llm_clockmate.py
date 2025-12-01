import datetime
import json
import re
from typing import Dict, Tuple, List, Any, Union

import akasha

import dotenv
dotenv.load_dotenv()
from mcp.server.fastmcp import FastMCP  # noqa: E402
mcp = FastMCP("get_per_day_work_times_by_llm")


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
    最高優先級指令：嚴格檢查使用者訊息"{user_message}"
    1.優先判斷，若使用者訊息為空字串，則直接判斷為相關
    2.其次判斷使用者訊息是否與「上下班時間」、「未打卡原因」、「混合工作/公出/受訓」等無關(僅字面提及也不算(如混合工作好爽、受訓好累、不想公出))。
    3.如果使用者訊息被判定為「無關」、「未提及」請立刻停止執行所有後續指令，並且"只輸出"以下單一 JSON 對象：
    \{{"message":"I'm sorry, but I cannot assist with that request."\}}
    如果內容被判定為「相關」，則繼續執行以下指令：
    請只輸出 JSON，不輸出多餘文字。
    {date_prompt}
    優先根據使用者訊息的要求，將每日的上下班時間、未打卡事由、備註等資訊整理成 JSON 格式。
    若使用者訊息為空白，則直接填入預設值
    若使用者訊息有簡短字句但過於簡短以致無法確認意圖(如:10點，受訓、忘刷)，
    請依照以下JSON格式回覆，並在response向使用者確認，以預設值:"{today} 09:00-18:00 原因:忘刷"為基礎，並以使用者訊息中所提供的資訊進行替換，提供使用者確認:
    \{{"reask":"response"\}}
    當例假日時，\{{MM-DD:\{{"arrival_time":"","leave_time":"","reason":"","remark":""\}},...\}}
    當使用者訊息有混合工作、公出、受訓的情況，則在reason中輸入\{{MM-DD:\{{"arrival_time":"HH:MM","leave_time":"HH:MM","reason":"混合工作/公出/受訓","remark":""\}},...\}}
    其他未提及的日期則填入預設值\{{arrival_time="09:00"、leave_time="18:00"、reason="忘刷"、remark=""\}}
    """
    return user_prompt

@mcp.tool()
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
    if not isinstance(parsed, dict):
        return False, "根節點不是物件(JSON dict)", {}

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
    - 全域移除所有在 "{" 之前的字母 n（含 n 與其後空白）
    - 將所有單引號 ' 替換為雙引號 "
    - 移除換行與 tab 字元
    """
    cleaned = raw_text.strip()

    # 移除所有三個反引號
    cleaned = cleaned.replace("```", "")

    # 全域移除 { 前的 n（允許空白）：例如 "n   {" -> "{"
    cleaned = re.sub(r"[nN]\s*\{", "{", cleaned)

    # 先移除換行與 tab
    cleaned = re.sub(r"[\n\t]", "", cleaned)

    # 將所有單引號替換為雙引號
    cleaned = cleaned.replace("'", '"')

    # 標準化冒號、逗號周邊空白，以及花括號周邊空白
    cleaned = re.sub(r"\s*:\s*", ":", cleaned)
    cleaned = re.sub(r"\s*,\s*", ",", cleaned)
    cleaned = re.sub(r"\s*\{\s*", "{", cleaned)
    cleaned = re.sub(r"\s*\}\s*", "}", cleaned)

    try:
        parsed = json.loads(cleaned)
        if isinstance(parsed, dict):
            return True, parsed
        return False, raw_text
    except Exception:
        return False, raw_text

def parse_llm_output(raw_text: str) -> Union[str, Dict[str, Dict[str, str]]]:
    """
    解析模型輸出：
    - 若為 {"message": "..."}，直接回傳該訊息字串（不再做驗證）。
    - 否則執行格式驗證，通過則回傳日期→工時的 dict，失敗則拋出 ValueError。
    """
    ok_parse, parsed = _clean_and_parse(raw_text)
    if not ok_parse:
        # 嘗試將輸出視為 list，再轉成 dict，並統一走相同判斷邏輯
        try:
            cleaned = raw_text.strip().replace("```", "")
            cleaned = re.sub(r"[\n\t]", "", cleaned)
            cleaned = cleaned.replace("'", '"')
            cleaned = re.sub(r"\s*:\s*", ":", cleaned)
            cleaned = re.sub(r"\s*,\s*", ",", cleaned)
            maybe_list = json.loads(cleaned)
            if isinstance(maybe_list, list):
                converted: Dict[str, Dict[str, str]] = {}
                for entry in maybe_list:
                    if not isinstance(entry, dict):
                        continue
                    date_val = entry.get('date') or entry.get('day') or entry.get('日期')
                    if not date_val:
                        continue
                    converted[str(date_val)] = {
                        "arrival_time": str(entry.get('arrival_time', '')),
                        "leave_time": str(entry.get('leave_time', '')),
                        "reason": str(entry.get('reason', '')),
                        "remark": str(entry.get('remark', '')),
                    }
                if not converted:
                    return "很抱歉，麻煩再試一次"
                parsed = converted
            else:
                return "很抱歉，麻煩再試一次"
        except Exception:
            return "很抱歉，麻煩再試一次"

    # 統一檢查：message-only（與工作無關）
    if set(parsed.keys()) == {"message"} and isinstance(parsed.get("message"), str):
        return "提供資訊與出勤無關聯"
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