import datetime
import json
import re
from typing import Dict, Tuple, List, Any, Union

import akasha

import dotenv
dotenv.load_dotenv()
from mcp.server.fastmcp import FastMCP  # noqa: E402
mcp = FastMCP("get_per_day_work_times_by_llm", port=8001)


def get_weekend():
    """
    取得當月所有週六、週日，回傳為字串清單（格式 MM-DD）。
    範例：['11-01', '11-02', ...]
    """
    today = datetime.date.today()
    year, month = today.year, today.month

    weekends = []
    # 僅處理從月初到今天（含今天）
    last_day = today.day
    for day in range(1, last_day + 1):
        d = datetime.date(year, month, day)
        if d.weekday() >= 5:  # 5=Saturday, 6=Sunday
            weekends.append(f"{month:02d}-{day:02d}")
    return year, month, today, weekends

def prompt_create(user_message = ""):
    year, month, today, weekends = get_weekend()
    date_prompt = f"從'{year}-{month}-01'到'{today}'的工時，其中{weekends}為例假日"
    user_prompt = f"""
    高優先級指令：內容檢查
    1.  優先判斷{user_message} 是否與「上下班時間」、「出勤記錄」、「工時資訊」、「打卡/刷卡」、「請假/公出/受訓」等主題相關。
    2.  如果{user_message}被判定為「無關」（例如：問天氣、閒聊、抱怨，請立刻停止執行所有後續指令，並且"只輸出"以下單一 JSON 對象：
    {{"message":"I'm sorry, but I cannot assist with that request."}}

    如果內容被判定為「相關」，則繼續執行以下指令：
    請只輸出 Dict，不輸出多餘文字。
    將每日的上下班時間、未打卡事由、備註等資訊整理成 Dict 格式。
    {date_prompt}
    若{user_message}=""則填入預設值arrival_time="09:00"、leave_time="18:00"、reason="忘刷"、remark=""。
    當例假日時，{{MM-DD:{{"arrival_time":"","leave_time":"","reason":"","remark":""}},...}}
    當有混合工作、公出、受訓的情況，則在reason中輸入{{MM-DD:{{"arrival_time":"HH:MM","leave_time":"HH:MM","reason":"文字","remark":"文字"}},...}}
    """
    return user_prompt

@mcp.tool()
def get_per_day_work_times_by_llm(
        model: str = "gemini:gemini-2.5-flash",
        user_prompt: str = "",
        info: str = "",
    ):
    import dotenv
    dotenv.load_dotenv()
    user_prompt = prompt_create()
    model = "gemini:gemini-2.5-flash"
    ak = akasha.ask(model=model, max_input_tokens=8000, max_output_tokens=20000)
    res = ak(prompt=user_prompt,info=[info])
    return res

TIME_PATTERN = re.compile(r"^([01]\d|2[0-3]):[0-5]\d$")
DATE_KEY_PATTERN = re.compile(r"^(0[1-9]|1[0-2])-(0[1-9]|[12][0-9]|3[01])$")

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

    today = datetime.date.today()
    current_year = today.year
    for date_key, payload in parsed.items():
        # 日期鍵必須是 MM-DD 格式
        if not DATE_KEY_PATTERN.match(date_key):
            return False, f"日期鍵格式錯誤(需 MM-DD): {date_key}", {}
        month_part = int(date_key[:2])
        day_part = int(date_key[3:])
        # 驗證日是否在該月份合法範圍
        try:
            _, max_day = datetime.datetime(current_year, month_part, 1).replace(day=1).timetuple()[:2]  # dummy usage
            # 正確取得月天數
            import calendar as _cal
            max_day = _cal.monthrange(current_year, month_part)[1]
        except Exception:
            return False, f"月份不合法: {date_key}", {}
        if day_part < 1 or day_part > max_day:
            return False, f"日期不合法: {date_key}", {}
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
        return False, {}
    except Exception:
        # 寬鬆處理：嘗試將單引號替換為雙引號再解析
        try:
            alt = cleaned.replace("'", '"')
            parsed = json.loads(alt)
            if isinstance(parsed, dict):
                return True, parsed
            return False, {}
        except Exception:
            return False, {}

def parse_llm_output(raw_text: str) -> Union[str, Dict[str, Dict[str, str]]]:
    """
    解析模型輸出：
    - 若為 {"message": "..."}，直接回傳該訊息字串（不再做驗證）。
    - 否則執行格式驗證，通過則回傳日期→工時的 dict，失敗則拋出 ValueError。
    """
    ok_parse, parsed = _clean_and_parse(raw_text)
    print(parsed)
    if not ok_parse:
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
    mcp.run(transport="sse")

    """
    user_message = ""
    user_prompt = prompt_create(user_message=user_message)
    res = get_per_day_work_times_by_llm(user_prompt=user_prompt)
    parsed_or_msg = parse_llm_output(res)
    print(parsed_or_msg)
    
    if isinstance(parsed_or_msg, str):
        print("🔔 訊息/錯誤：", parsed_or_msg)
    else:
        print("✅ 驗證通過，筆數：", len(parsed_or_msg))
        # 範例顯示前 3 筆
        items = list(parsed_or_msg.items())[:3]
        for k, v in items:
            print(f"  {k}: {v}")
    """
