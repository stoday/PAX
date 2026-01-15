# Pax 便利工作助手

自動化工作助手

## 安裝

```bash
git init
git pull https://github.com/stoday/PAX.git travel-helper
pip install -e .
# 或是
pip install git+https://github.com/stoday/PAX.git@travel-helper
```

## 使用方法

### 1. 設置 API Key

在專案根目錄新增 `.env` ，包含：

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

### 2. 啟動流程（本機終端）

```bash
python -m app.main
```

啟動後即可看到 Pax 介面：

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

### 3. 結束應用

在首頁輸入 `exit` 即可退出。

## 專案結構

```
app/
	main.py            # CLI 入口（本機終端啟動）
	llm_prompt.py      # LLM Prompt 組裝與規則
	get_token.py       # 取得登入 Cookie
	__init__.py        # 對外匯出

tools/
	llm_uploader.py    # 工時提交（MCP 工具與提交流程）
	mcp-google-map/    # Google Map MCP 服務
	travel_helper/     # 出差單相關工具
README.md            # 專案說明
requirements.txt     # Python 依賴
pyproject.toml       # 專案設定
setup.py             # 套件設定
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

