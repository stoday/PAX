# ClockMate 工時填報助手

ClockMate 是一個自動化工時填報小幫手，支援在 SSH 互動介面輸入自然語言或手動模式，協助將上下班時間與原因填寫到工時系統（hrwt.iii.org.tw）。

## 環境需求
- Python 3.10 以上
- pip（或其他套件管理工具）
- Chrome/Chromium 瀏覽器（供 token 擷取工具使用）
- 可以網路連線至資策會內的電腦 VPN

## 安裝步驟
1) 直接使用 pip 安裝（ssh-revised 分支）
```bash
pip install git+https://gitlab.com/stoday/clockmate.git@ssh-revised
```

或 clone 後本地安裝（使用 ssh-revised 分支）
```bash
git clone https://gitlab.com/stoday/clockmate.git
cd clockmate
git checkout ssh-revised
python3 -m venv .venv && source .venv/bin/activate  # 選用
pip install -e .
```
2) 取得並寫入環境變數 `.env`
```bash
python get_token.py
```
   - 會自動開啟瀏覽器，依指示登入 hrwt；完成後程式會將 `ASP_NET_SESSION_ID`、`CLIENT_TICKET`、`CLIENT_USERNAME` 寫入專案根目錄的 `.env`。
   - 若需要呼叫 LLM 服務，可在 `.env` 內自行加入 `API KEY`。例如: 想要使用 `Gemini` 模型，加入變數 `GEMINI_API_KEY=xxxxx`
3) （選用）若要固定 log 路徑，可將 `CLOCKMATE_LOG_PATH` 指到想要的檔案；預設寫在 `clockmate/logs/access_hr_web_tool_YYYYMMDD.log`。

## 操作範例
- 啟動後端服務（含 SSH shell 與 FastAPI）
```bash
python start_services.py
```
- 以預設帳密連線 SSH（可在設定中調整）
```bash
ssh admin@127.0.0.1 -p 2222
# 密碼：password123
```
- 進入 shell 後執行 ClockMate
```bash
clockmate              # 預設 LLM 模式
```
- 取得 token（會開啟瀏覽器並寫入 .env）
```bash
clockmate-token
```
- 直接在 CLI 中描述需求，例如：
```
你: 幫我填 12 月 5 日的工時，上班接近 9 點
AI: 12 月的工時已成功填寫至今天 (2025 年 12 月 05 日)。
```

## 注意事項
- `.env` 內的 cookie 與 API key 屬機敏資訊，請勿外洩。
- log 會依日期分檔，預設路徑為 `clockmate/logs/access_hr_web_tool_YYYYMMDD.log`。
- 若 SSH 連線埠或帳密有自訂，請同步修改連線指令。
- 程式會自動嘗試填入工作日，假日欄位保持空白；提交前請再次確認生成內容是否符合需求。
- 若瀏覽器或網路連線有額外限制，請確保環境允許對 hrwt.iii.org.tw 發送請求。
