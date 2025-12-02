# ClockMate 工時填報助手

自動化工時表單填寫工具，支援批次處理和智慧填入。

## 安裝

```bash
git init
git pull https://github.com/stoday/CLOCKMATE.git ssh
pip install -e .
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
clockmate
```

### 2. 使用者

#### 1.確認ssh server已開啟後進行連線
```bash
ssh admin@127.0.0.1 -p 2222
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
password123
```

#### 成功登入後即可看到Clockmate介面

```
╭───────────── ClockMate 工時小幫手 ──────────────╮
│    ________           __   __  ___      __      │
│   / ____/ /___  _____/ /__/  |/  /___ _/ /____  │
│  / /   / / __ \/ ___/ //_/ /|_/ / __ `/ __/ _ \ │
│ / /___/ / /_/ / /__/ ,< / /  / / /_/ / /_/  __/ │
│ \____/_/\____/\___/_/|_/_/  /_/\__,_/\__/\___/  │
╰─────────────────────────────────────────────────╯
處理範圍：本月 1 日至今日
預設時間 09:00-18:00
預設原因：忘刷
 - 直接按 [Enter]：將使用預設值
 - 輸入 'exit'： 退出系統
請輸入工時資料
>:
```

## 使用範例

### 1. 輸入工時資訊
```
請輸入工時資料
>:今天公出
```

### 2. 等待語言模型生成工時表單
```
工時正確生成.
{'2025-12-01': {'arrival_time': '09:00', 'leave_time': '18:00', 'reason': '忘刷', 'remark': ''}, '2025-12-02': {'arrival_time': '09:00', 'leave_time': '18:00', 'reason': '公出', 'remark': ''}}
是否繼續並生成表單資料？ [Y/n]:
```
可以看到當天(2025/12/2)的未打卡原因從預設值:忘刷改成了公出，若表單符合您的要求，輸入 `Y` 或是 直接按 [Enter] (預設值為`Y`) ，會啟動瀏覽器，待使用者登入會內後獲取cookie以進行自動填寫

### 3. 結束應用
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

