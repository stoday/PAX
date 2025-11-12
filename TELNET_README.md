# Telnet 檔案目錄服務使用說明

這是一個透過 Telnet 連接來瀏覽電腦檔案目錄的範例程式，包含以下組件：

## 組件說明

### 1. FastAPI 服務器 (`clockmate/fastapi_server.py`)
- 提供 REST API 來瀏覽檔案系統
- 端點：
  - `GET /` - 服務狀態檢查
  - `GET /list-directory` - 列出目錄內容
  - `GET /get-file-info` - 獲取檔案詳細資訊
  - `GET /get-drives` - 獲取系統磁碟機列表

### 2. Telnet 服務器 (`clockmate/telnet_server.py`)
- 接受 Telnet 連接
- 將 Telnet 命令轉換為 FastAPI 請求
- 提供類似命令列的介面

### 3. Telnet 客戶端範例 (`examples/telnet_client_example.py`)
- 示範如何連接到 Telnet 服務器
- 支持互動模式和自動演示模式

## 安裝和設置

### 1. 安裝依賴套件
```bash
# Windows PowerShell
pip install -r requirements.txt

# 或使用啟動腳本自動安裝
python start_services.py --install
```

### 2. 啟動服務

#### 方法 1: 使用啟動腳本（推薦）
```bash
python start_services.py
```

#### 方法 2: 分別啟動服務
```bash
# 終端機 1 - 啟動 FastAPI 服務器
python -m clockmate.fastapi_server

# 終端機 2 - 啟動 Telnet 服務器
python -m clockmate.telnet_server
```

## 使用方法

### 1. 透過網頁瀏覽器
- 開啟 http://127.0.0.1:8000/docs 查看 API 文檔
- 直接測試 API 端點

### 2. 透過 Telnet 客戶端

#### 使用內建的客戶端
```bash
# 互動模式
python examples/telnet_client_example.py

# 自動演示模式
python examples/telnet_client_example.py --demo
```

#### 使用系統 Telnet 客戶端
```bash
# Windows
telnet 127.0.0.1 2323

# 如果 Windows 沒有 telnet，可以啟用：
# dism /online /Enable-Feature /FeatureName:TelnetClient
```

## 可用的 Telnet 命令

- `help` - 顯示幫助信息
- `ls` / `dir` - 列出當前目錄內容
- `ls <路徑>` - 列出指定目錄內容
- `cd <路徑>` - 切換到指定目錄
- `pwd` - 顯示當前路徑
- `drives` - 顯示可用磁碟機（Windows）
- `info <路徑>` - 顯示檔案/目錄詳細資訊
- `status` - 顯示服務器狀態
- `quit` / `exit` - 退出連接

## 使用範例

```
> help
=== 可用命令 ===
...

> drives
可用磁碟機:
C:\ (固定磁碟)
D:\ (固定磁碟)

> cd C:\Users
已切換到: C:\Users

> ls
目錄: C:\Users
==================================================
[DIR]    today                          
[DIR]    Public                         
...

> info setup.py
檔案資訊: setup.py
========================================
路徑: C:\...\setup.py
類型: file
大小: 1.23 KB
修改時間: 2025-11-12T10:30:00
...
```

## 安全注意事項

⚠️ **重要安全警告**

這是一個範例程式，**不建議在生產環境中使用**，因為：

1. **沒有身份驗證** - 任何人都可以連接
2. **沒有授權控制** - 可以瀏覽整個檔案系統
3. **沒有加密** - 所有通信都是明文
4. **沒有存取限制** - 沒有限制可存取的目錄

### 如果要在實際環境中使用，建議加入：

- 身份驗證機制
- 存取權限控制
- SSL/TLS 加密
- 日誌記錄
- 速率限制
- 檔案路徑驗證

## 故障排除

### 1. 端口被佔用
如果收到 "Address already in use" 錯誤：
```bash
# 檢查端口使用情況
netstat -ano | findstr :8000
netstat -ano | findstr :2323

# 終止佔用端口的程序
taskkill /PID <PID號碼> /F
```

### 2. 無法連接到服務器
- 確認 FastAPI 服務器是否正在運行
- 檢查防火牆設定
- 確認端口號是否正確

### 3. 權限錯誤
- 某些系統目錄可能需要管理員權限
- 嘗試以管理員身份運行

### 4. 模組導入錯誤
確認已安裝所有依賴套件：
```bash
pip install -r requirements.txt
```

## 擴展功能建議

可以考慮添加的功能：
- 檔案上傳/下載
- 檔案編輯
- 檔案搜尋
- 系統資訊查詢
- 遠端命令執行（需謹慎處理安全性）

## 技術架構

```
[Telnet 客戶端] 
    ↓ (Telnet 協議)
[Telnet 服務器] 
    ↓ (HTTP 請求)
[FastAPI 服務器] 
    ↓ (檔案系統 API)
[作業系統檔案系統]
```

這種架構的好處是：
- 分離關注點
- 可以獨立測試每個組件
- FastAPI 服務器也可以被其他應用程式使用
- 容易擴展和維護