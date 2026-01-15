# Pax 便利工作助手

自動化工作助手（原名 ClockMate）

## 環境需求
- Python 3.10 以上
- pip（或其他套件管理工具）
- Chrome/Chromium 瀏覽器（供 token 擷取工具使用）
- 可以網路連線至資策會內的電腦 VPN

```bash
git init
git pull https://github.com/stoday/CLOCKMATE.git ssh
pip install -e .
# 或是
pip install git+https://github.com/stoday/CLOCKMATE.git@ssh
```

## 使用方法

### 1. Server端

#### 1. 設置API_KEY

在專案位置新增 `.env` ，包含

```
# 必要
GEMINI_API_KEY={your gemini api key}

# 登入相關 Cookie (執行後自動產生)
ASP_NET_SESSION_ID={your asp net session id}
CLIENT_TICKET={your client ticket}
CLIENT_USERNAME={your client username}

# 其他可選設定
TEL_BEARER_TOKEN={your bearer token}
TEL_COOKIE_TOKEN={your cookie token}
```

#### 2. 啟用服務
```bash
pax
# 或使用舊指令相容方式
clockmate
```
   - 會自動開啟瀏覽器，依指示登入 hrwt；完成後程式會將 `ASP_NET_SESSION_ID`、`CLIENT_TICKET`、`CLIENT_USERNAME` 寫入專案根目錄的 `.env`。
   - 若需要呼叫 LLM 服務，可在 `.env` 內自行加入 `API KEY`。例如: 想要使用 `Gemini` 模型，加入變數 `GEMINI_API_KEY=xxxxx`
3) （選用）若要固定 log 路徑，可將 `CLOCKMATE_LOG_PATH` 指到想要的檔案；預設寫在 `clockmate/logs/access_hr_web_tool_YYYYMMDD.log`。

### 2. 使用者(Windows)

#### 1.確認ssh server已開啟後進行連線
```bash
python -m clockmate.get_token     # 或使用 console script: clockmate-token
```

##### 1.1.系統訊息
如果是第一次連線，系統會彈出以下訊息:
```
Are you sure you want to continue connecting (yes/no/[fingerprint])?
```
輸入 `yes` 即可

##### 1.2.ssh連線問題
如果彈出以下訊息
```
@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
@    WARNING: REMOTE HOST IDENTIFICATION HAS CHANGED!     @
@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
IT IS POSSIBLE THAT SOMEONE IS DOING SOMETHING NASTY!
Someone could be eavesdropping on you right now (man-in-the-middle attack)!
It is also possible that a host key has just been changed.
The fingerprint for the RSA key sent by the remote host is
SHA256:pHJ/nJNs4mzYo/txygFSi7seRAyYFi3GnEdDQJj6Hxk.
Please contact your system administrator.
Add correct host key in C:\\Users\\User/.ssh/known_hosts to get rid of this message.
Offending RSA key in C:\\Users\\User/.ssh/known_hosts:6
Host key for [127.0.0.1]:2222 has changed and you have requested strict checking.
Host key verification failed.
```
只需輸入以下指令後再次嘗試連線即可
```bash
ssh-keygen -R "[127.0.0.1]:2222"
ssh admin@127.0.0.1 -p 2222
yes
```

#### 2.輸入密碼
```bash
# pip 安裝後
clockmate
# 若是從原始碼直接執行（請先依上方「clone 安裝」步驟取得原始碼）
python clockmate/cli.py
```

#### 成功登入後即可看到 Pax 介面

```
╭── Pax 便利工作助手 ──╮
│     ____             │
│    / __ \____ __  __ │
│   / /_/ / __ `/ |/_/ │
│  / ____/ /_/ />  <   │
│ /_/    \__,_/_/|_|   │
╰──────────────────────╯
處理範圍：本月 1 日至今日
預設時間 09:00-18:00
預設原因：忘刷
 - 直接按 [Enter]：將使用預設值
 - 輸入 'exit'： 退出系統
請輸入工時資料
>:
```

## 使用範例

### 1. 登入以獲取cookie
自動啟動瀏覽器，待使用者登入會內後獲取cookie

### 2. 輸入工時資訊
```
請輸入工時資料
>:今天公出
```

### 3. 等待語言模型生成工時表單
```
工時正確生成.
{'2025-12-01': {'arrival_time': '09:00', 'leave_time': '18:00', 'reason': '忘刷', 'remark': ''}, '2025-12-02': {'arrival_time': '09:00', 'leave_time': '18:00', 'reason': '公出', 'remark': ''}}
是否繼續並生成表單資料？ [Y/n]:
```
可以看到當天(2025/12/2)的未打卡原因從預設值:忘刷改成了公出，若表單符合您的要求，輸入 `Y` 或是 直接按 [Enter] (預設值為`Y`) ，會進行自動填寫

### 4. 結束應用
若欲退出應用，在首頁輸入 `exit` 即可
```
請輸入工時資料
>:exit
```

## 功能特色

- 🚀 自動化工時表單填寫
- 🔐 安全的憑證管理
- 📅 智慧日期處理
- 🎨 美觀的命令列介面
- ⚙️ 可自訂工作時間設定

## 系統需求

- Python 3.10+
- Chrome 瀏覽器
- 網路連線

## 授權

MIT License

## 注意事項
- `.env` 內的 cookie 與 API key 屬機敏資訊，請勿外洩。
- log 會依日期分檔，預設路徑為 `clockmate/logs/access_hr_web_tool_YYYYMMDD.log`。
- 若 SSH 連線埠或帳密有自訂，請同步修改連線指令。
- 程式會自動嘗試填入工作日，假日欄位保持空白；提交前請再次確認生成內容是否符合需求。
- 若瀏覽器或網路連線有額外限制，請確保環境允許對 hrwt.iii.org.tw 發送請求。

## 即將開發
- 工具呼叫模式由 call tool 改為 MCP。
- SSH 登入時自動提示是否有未填妥的工時。
- 新增查詢目前工時紀錄的指令。
