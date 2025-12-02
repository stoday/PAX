# ClockMate 工時填報助手

自動化工時表單填寫工具，支援批次處理和智慧填入。

## 安裝

### 從 GitLab 安裝
```bash
pip install git+https://gitlab.com/your-username/clockmate.git
```

### 從本地安裝
```bash
git init
git pull https://gitlab.com/your-username/clockmate.git ssh
cd clockmate
pip install -e .
```

## 使用方法

### 1. Server端

#### 1. 設置API_KEY

在專案位置新增 `.env`
並保存API_KEY

#### 2. 啟用服務
```bash
cd clockmate
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
```

#### 2.輸入密碼
```bash
password123
```

#### 成功登入後即可看到Clockmate介面，直接輸入出勤狀況並等待資料生成

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

