
import akasha
from access_hr_web_tool import get_fresh_form_for_target_dates, get_fresh_form_for_util_today
from datetime import datetime

# 創建工具
form_util_today_tool = akasha.create_tool(
    tool_description="""這是一個可以自動填寫工作時間的工具，可以根據今天的日期來生成對應的表單資料，然後送到指定的系統。這個工具需要的兩個參數，分別是`year_month`與`work_times`，範例如下：
        year_month (str): 年月，格式如 "2025/10"，如果不提供則使用當前月份
        work_times (dict): 預設工作時間設定，範例如：
            {
                'arrival_time': '09:00',    # 預設上班時間
                'leave_time': '18:00',      # 預設下班時間
                'reason': '忘刷',            # 預設原因(忘記刷卡來記錄上下班時間)
                'remark': ''                # 預設備註
            }
    如果使用者指定`year_month`為某年某月，則會填寫該月份的表單；如果沒有指定，則會填寫當前月份的表單。
    如果使用者指定`work_times`，則會使用這些時間來填寫表單；如果沒有指定，則使用預設值。預設值為上班時間09:00，下班時間18:00，原因為忘刷，備註為空字串。
    這個工具會回傳一個字串，內容包含送出表單的結果訊息。如果這個工具回傳的status為200，表示成功填寫表單；如果status為400，表示填寫失敗，會有錯誤訊息在message中。
    """,
    func=get_fresh_form_for_util_today,
    tool_name="form_util_today_tool",
)

# 創建 agent 並使用工具
agent = akasha.agents(
    tools=[form_util_today_tool],
    model="gemini:gemini-2.5-flash",
    temperature=1.0,
    verbose=True,
    keep_logs=True,
)

# 問問題並使用工具回答
response = agent("幫我填2025年11月份的工時，預設上班時間09:00，下班時間18:00，原因忘刷，備註空白")
print(response)