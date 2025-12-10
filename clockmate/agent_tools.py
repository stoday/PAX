
import akasha
from access_hr_web_tool import get_fresh_form_for_target_dates, get_fresh_form_for_util_today
from datetime import datetime

# 創建工具
form_util_today_tool = akasha.create_tool(
    tool_description="""
    這是一個可以自動填寫工作時間(工時)的工具，可以根據**這個月到今天的日期與填寫工時需求**來生成對應的表單資料，然後送到指定的系統。一般來說，如果沒有特別指定填寫日期的需求，就使用這個工具填寫這個月從月初到今日的工時。這個工具需要的兩個參數，分別是`year_month`與`work_times`，參數內容說明如下：
        year_month (str): 年月，格式如 "2025/11"，如果未提供則使用當前月份
        work_times (dict): 預設工作時間設定，範例如下：
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


# 創建工具
for_target_dates_tool = akasha.create_tool(
    tool_description="""
    這是一個可以自動填寫工作時間(工時)的工具，可以根據使用者**指定的日期與需求**，或是**上下班時間非預設想自由調整**來生成對應的表單資料，然後送到指定的系統。這個工具需要的兩個參數，分別是`year_month`與`target_dates`，參數內容說明如下：
        year_month (str): 年月，格式如 "2025/11"，如果未提供則使用當前月份
        target_dates (dict): 自訂的指定日期及其上下班時間和原因等資訊，格式如：
            {
                '20251101': {'arrival_time': '09:00', 'leave_time': '18:00', 'reason': '忘刷', 'remark': ''},
                '20251102': {'arrival_time': '09:15', 'leave_time': '18:15', 'reason': '忘刷', 'remark': ''},
                ...
            }
    如果使用者指定`year_month`為某年某月，則會填寫該月份的表單；如果沒有指定，則會填寫當前月份的表單。
    如果使用者指定`target_dates`，則會使用這些時間來填寫表單；如果沒有指定，則使用預設值。預設值為上班時間09:00，下班時間18:00，原因為忘刷，備註為空字串。
    這個工具會回傳一個字串，內容包含送出表單的結果訊息。如果這個工具回傳的status為200，表示成功填寫表單；如果status為400，表示填寫失敗，會有錯誤訊息在message中。
    """,
    func=get_fresh_form_for_target_dates,
    tool_name="for_target_dates_tool",
)


# 創建 agent 並使用工具
agent = akasha.agents(
    tools=[form_util_today_tool,
           for_target_dates_tool],
    model="gemini:gemini-2.5-flash",
    temperature=1.0,
    verbose=False,
    # verbose=True, # for debug
    keep_logs=True,
)


def main():
    # 問問題並使用工具回答
    prompt_for_today_date = datetime.now().strftime("今天是 %Y 年 %m 月 %d 日。")
    response = agent("""
    # 資訊:
    {today_date_info}
    
    # 任務
    協助使用者填寫工作時間(工時)紀錄表單。根據使用者所描述的需求，蒐集判斷使用者需要填寫哪些日期的工時，並使用預設或依據使用者指定的上下班時間、原因與備註來完成表單資訊。最後使用適合的工具將表單資訊填寫完成後送出給系統。
    
    # 使用者需求                   
    {user_prompt}
    """.format(today_date_info=prompt_for_today_date, 
               user_prompt="可以幫我改12/02的下班時間是空的嗎? 因為現在還沒到下班時間我就填了，不太正確")) 
    print(response)
    
    
if __name__ == "__main__":
    main()


## 測試案例
# "幫我填11月5日的工時，然後上班時間要接近9點，因為我那天有點晚到。"
# "填寫12月工時，上下班時間幫我取個接近早上九點與下午六點的亂數時間，原因就填忘刷，備註就不需要了。"
# "可以幫我改12/02的下班時間是空的嗎? 因為現在還沒到下班時間我就填了，不太正確"