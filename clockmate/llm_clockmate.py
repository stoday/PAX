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
    優先根據使用者訊息的要求，將每日的上下班時間、未打卡事由、備註等資訊整理成 JSON 格式。
    {date_prompt}
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
            return False, f"日期 {date_key} 的值不是 dict", {}

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
    """移除 code fence、多餘空白換行，並嘗試解析為 JSON 物件(dict)。

    流程：
    1) 移除 code fence
    2) 移除 JSON 內容中的換行與 tab
    3) 移除 JSON key-value 分隔符號(:)後的空白
    4) 嚴格 json.loads 嘗試
    5) 失敗則做一次單引號→雙引號替換再嘗試
    """
    cleaned = raw_text.strip()
    # 若出現前綴的單一 'n' 緊接 JSON 起始，移除 (例如: n{"key":...} 或 n[ {...} ])
    if cleaned and cleaned[0] in ('n', 'N'):
        # 找到第一個非空白字元後若是 { 或 [ ，則視為誤前綴
        # 允許中間有少量空白: n   {
        m = re.match(r'^[nN]\s*([\[{])', cleaned)
        if m:
            # 去除前導 n 及其後的空白，只保留起始符號及之後
            # 找到起始符號位置
            start_idx = cleaned.find(m.group(1))
            cleaned = cleaned[start_idx:]
    if "```" in cleaned:
        parts = cleaned.split("```")
        if len(parts) >= 3:
            mid = parts[1]
            # 移除 optional language specifier, e.g., "json"
            if "\n" in mid:
                mid = "\n".join(mid.split("\n")[1:])
            cleaned = mid.strip()

    # 移除 JSON 字串內部的換行、tab、以及冒號後的空白
    cleaned = re.sub(r'[\n\t]', '', cleaned)
    cleaned = re.sub(r':\s+', ':', cleaned)
    try:
        parsed = json.loads(cleaned)
        if isinstance(parsed, dict):
            return True, parsed
        return False, raw_text
    except Exception:
        # 寬鬆處理：嘗試將單引號替換為雙引號再解析
        try:
            alt = cleaned.replace("'", '"')
            parsed = json.loads(alt)
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
        # 嘗試將輸出視為 list，再轉成 dict
        try:
            cleaned = raw_text.strip()
            if "```" in cleaned:
                parts = cleaned.split("```")
                if len(parts) >= 3:
                    mid = parts[1]
                    if "\n" in mid:
                        mid = "\n".join(mid.split("\n")[1:])
                    cleaned = mid.strip()
            cleaned = re.sub(r'[\n\t]', '', cleaned)
            cleaned = re.sub(r':\s+', ':', cleaned)
            maybe_list = json.loads(cleaned)
            if isinstance(maybe_list, list):
                converted: Dict[str, Dict[str, str]] = {}
                for entry in maybe_list:
                    if not isinstance(entry, dict):
                        continue
                    # 嘗試取得日期欄位
                    date_val = entry.get('date') or entry.get('day') or entry.get('日期')
                    if not date_val:
                        continue
                    converted[str(date_val)] = {
                        "arrival_time": str(entry.get('arrival_time', '')),
                        "leave_time": str(entry.get('leave_time', '')),
                        "reason": str(entry.get('reason', '')),
                        "remark": str(entry.get('remark', '')),
                    }
                if converted:
                    ok2, err2, data2 = validate_llm_json(converted)
                    if ok2:
                        return data2
                    else:
                        return err2 or "格式驗證失敗"
        except Exception:
            pass
        print(raw_text)
        return "JSON 解析失敗或根節點非物件"

    # 步驟 2：message-only（與工作無關）
    if set(parsed.keys()) == {"message"} and isinstance(parsed.get("message"), str):
        return "提供資訊與出勤無關聯"

    # 步驟 3：其餘檢查只回傳第一個錯誤
    ok, err, data = validate_llm_json(parsed)
    if not ok:
        return err or "格式驗證失敗"
    return data

if __name__ == "__main__":
    mcp.run(transport="stdio")