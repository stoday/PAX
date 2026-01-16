# Pax 本地模式（Local Mode）詳細說明

## 📋 目錄
1. [什麼是本地模式](#什麼是本地模式)
2. [系統需求](#系統需求)
3. [安裝步驟](#安裝步驟)
4. [配置說明](#配置說明)
5. [使用方式](#使用方式)
6. [故障排除](#故障排除)
7. [更新與維護](#更新與維護)

---

## 什麼是本地模式

本地模式（Local Mode）是 Pax 的完全離線運行模式，所有業務邏輯（LLM 處理、MCP 工具）都在使用者電腦上執行。

### 適用情境

✅ **適合以下用戶**：
- 需要離線使用（無穩定網路連線）
- 對資料隱私要求極高
- 願意自行管理 API Keys
- 有能力安裝和維護環境

❌ **不適合以下用戶**：
- 希望快速安裝即用
- 不想安裝額外軟體
- 電腦儲存空間有限
- 不熟悉環境配置

### 與雲端模式對比

| 項目 | 本地模式 | 雲端模式 |
|------|---------|---------|
| 安裝大小 | ~150 MB（依賴） | ~20 MB |
| 安裝時間 | 3-5 分鐘 | < 1 分鐘 |
| 需要網路 | 只在安裝時 | 使用時需要 |
| 離線使用 | ✅ 可以 | ❌ 不行 |
| API Keys | 本地管理 | 後端管理 |
| 更新 | 需要重新安裝 | 自動更新 |
| 隱私保護 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |

---

## 系統需求

### 硬體需求

| 項目 | 最低需求 | 建議配置 |
|------|---------|---------|
| CPU | 雙核心 2.0 GHz | 四核心 2.5 GHz+ |
| RAM | 4 GB | 8 GB+ |
| 硬碟空間 | 2 GB 可用空間 | 5 GB+ |
| 網路 | 安裝時需要 | 安裝時需要 |

### 軟體需求

| 軟體 | 版本 | 用途 |
|------|------|------|
| Windows | 10/11 (64-bit) | 作業系統 |
| Node.js | LTS (v20.x) | 執行 MCP Google Map |
| uv | 最新版 | Python 套件管理器（會自動安裝 Python 3.10） |

**注意**：安裝腳本會自動安裝 Node.js 和 uv，無需手動安裝。uv 會自動下載並管理 Python 3.10。

---

## 安裝步驟

### 方法 1：使用安裝腳本（推薦）

#### 步驟 1：下載安裝腳本

從 GitHub Releases 下載 `setup_local.ps1`：
```
https://github.com/stoday/PAX/releases/latest/download/setup_local.ps1
```

#### 步驟 2：執行安裝腳本

1. 右鍵點擊 `setup_local.ps1`
2. 選擇「以系統管理員身分執行」
3. 如果出現安全提示，選擇「執行」

#### 步驟 3：等待安裝完成

安裝腳本會自動：
- ✅ 安裝 Chocolatey（套件管理器）
- ✅ 安裝 Node.js LTS
- ✅ 安裝 uv（Python 套件管理器）
- ✅ 使用 uv 建立 Python 3.10 虛擬環境
- ✅ 下載 Pax 程式碼
- ✅ 使用 uv 安裝 Python 依賴（超快！）
- ✅ 安裝 npm 依賴
- ✅ 建立桌面捷徑

**預計時間**：2-4 分鐘（uv 讓安裝更快！）

#### 步驟 4：驗證安裝

安裝完成後，執行以下指令驗證：

```powershell
# 驗證 Node.js
node --version
# 應顯示：v20.x.x

# 驗證 Python
python --version
# 應顯示：Python 3.10.x

# 驗證虛擬環境
cd "C:\Program Files\Pax"
.\.venv\Scripts\python.exe --version
# 應顯示：Python 3.10.x

# 驗證 Pax
.\.venv\Scripts\python.exe -c "from core.llm.handler import LLMHandler; print('✓ Pax 安裝成功')"
```

**注意**：Pax 使用 Python 虛擬環境（`.venv`）來隔離依賴，避免污染系統 Python 環境。

---

### 方法 2：手動安裝

如果自動安裝腳本失敗，可以手動安裝：

#### 步驟 1：安裝 Node.js

1. 下載：https://nodejs.org/（選擇 LTS 版本）
2. 執行安裝檔，全部使用預設選項
3. 驗證：開啟 PowerShell，執行 `node --version`

#### 步驟 2：安裝 Python

1. 下載：https://www.python.org/downloads/（選擇 3.10 或更新版本）
2. 執行安裝檔，**勾選「Add Python to PATH」**
3. 驗證：開啟 PowerShell，執行 `python --version`

#### 步驟 3：下載 Pax

```powershell
# 建立安裝目錄
New-Item -ItemType Directory -Path "C:\Program Files\Pax" -Force

# 下載程式碼
cd "C:\Program Files\Pax"
Invoke-WebRequest -Uri "https://github.com/stoday/PAX/releases/latest/download/pax-local.zip" -OutFile "pax.zip"
Expand-Archive -Path "pax.zip" -DestinationPath "." -Force
Remove-Item "pax.zip"
```

#### 步驟 4：安裝依賴

```powershell
# 安裝 Python 依賴
cd "C:\Program Files\Pax"
pip install -r requirements.txt

# 安裝 npm 依賴
cd "tools\mcp-google-map"
npm install
```

#### 步驟 5：建立捷徑

手動建立桌面捷徑，指向 `C:\Program Files\Pax\PaxTrayApp.exe`

---

## 配置說明

### 環境變數配置

本地模式需要配置 `.env` 檔案來設定 API Keys 和其他參數。

#### 步驟 1：複製範例檔案

```powershell
cd "C:\Program Files\Pax"
Copy-Item "config\local.env.example" -Destination ".env"
```

#### 步驟 2：編輯 `.env` 檔案

使用記事本或其他文字編輯器開啟 `.env`：

```bash
# Pax 本地模式配置

# === 運行模式 ===
PAX_MODE=local

# === LLM API Keys ===
# Gemini API Key（必要）
GEMINI_API_KEY=your_gemini_api_key_here

# === Google Map API Key（可選） ===
GOOGLE_MAPS_API_KEY=your_google_maps_api_key_here

# === 工時系統認證（會自動從瀏覽器取得） ===
# ASP_NET_SESSION_ID=（自動取得）
# CLIENT_TICKET=（自動取得）
# CLIENT_USERNAME=（自動取得）

# === 其他設定 ===
# Log 等級（DEBUG, INFO, WARNING, ERROR）
LOG_LEVEL=INFO

# Log 檔案路徑
LOG_PATH=logs/pax.log
```

#### 步驟 3：取得 API Keys

##### Gemini API Key
1. 訪問：https://makersuite.google.com/app/apikey
2. 登入 Google 帳號
3. 點擊「Create API Key」
4. 複製 API Key 並貼到 `.env` 的 `GEMINI_API_KEY`

##### Google Maps API Key（可選）
1. 訪問：https://console.cloud.google.com/
2. 建立新專案或選擇現有專案
3. 啟用「Maps JavaScript API」
4. 建立憑證（API Key）
5. 複製 API Key 並貼到 `.env` 的 `GOOGLE_MAPS_API_KEY`

---

## 使用方式

### 啟動 Pax

#### 方法 1：使用桌面捷徑
雙擊桌面上的「Pax」圖示

#### 方法 2：使用指令
```powershell
cd "C:\Program Files\Pax"
.\PaxTrayApp.exe
```

### 系統匣操作

啟動後，右下角系統匣會出現 Pax 圖示（綠色圓點）。

右鍵點擊圖示，會出現選單：
- **打開 Pax**：開啟 Console 介面
- **執行邏輯**：啟動背景邏輯（如果有）
- **停止執行**：停止背景邏輯
- **結束常駐**：完全關閉 Pax

### Console 介面使用

點擊「打開 Pax」後，會開啟一個 Console 視窗：

```
╭── Pax 便利工作助手 ──╮
│                        │
│  處理範圍：本月 1 日至今日
│  預設時間 09:00-18:00
│  預設原因：忘刷
│
│  請問我可以為您做什麼呢
╰────────────────────────╯

>
```

#### 範例對話

```
> 幫我填今天的工時，上班 9 點，下班 6 點
思考中...
將為您填寫 2026-01-16 的工時（09:00-18:00）
是否確認？(y/n) y
✓ 工時提交成功

> 查詢台北到新竹的距離
思考中...
台北到新竹的距離約 72 公里

> exit
再見！
```

---

## 故障排除

### 問題 1：安裝腳本執行失敗

**錯誤訊息**：
```
無法載入檔案 setup_local.ps1，因為這個系統上已停用指令碼執行。
```

**解決方法**：
```powershell
# 以系統管理員身分執行 PowerShell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# 然後重新執行安裝腳本
```

---

### 問題 2：Node.js 或 Python 安裝失敗

**解決方法**：
1. 手動下載並安裝（參考「方法 2：手動安裝」）
2. 確認安裝時勾選「Add to PATH」
3. 重新啟動電腦
4. 驗證安裝：`node --version` 和 `python --version`

---

### 問題 3：找不到 Gemini API Key

**錯誤訊息**：
```
Error: GEMINI_API_KEY not found in environment
```

**解決方法**：
1. 確認 `.env` 檔案存在於 `C:\Program Files\Pax\`
2. 確認 `.env` 中有 `GEMINI_API_KEY=...`
3. 確認 API Key 正確（無多餘空格）
4. 重新啟動 Pax

---

### 問題 4：MCP Google Map 無法啟動

**錯誤訊息**：
```
Error: Cannot find module 'express'
```

**解決方法**：
```powershell
cd "C:\Program Files\Pax\tools\mcp-google-map"
npm install
```

---

### 問題 5：工時提交失敗

**錯誤訊息**：
```
Error: 認證失敗，請重新登入
```

**解決方法**：
1. Pax 會自動開啟瀏覽器
2. 在瀏覽器中登入 hrwt.iii.org.tw
3. 登入成功後，Pax 會自動取得 Cookie
4. 重新嘗試提交工時

---

### 問題 6：程式無法啟動

**解決方法**：
1. 檢查 `logs/pax.log` 查看錯誤訊息
2. 確認所有依賴都已安裝
3. 嘗試重新安裝

---

## 更新與維護

### 更新 Pax

#### 方法 1：使用更新腳本

```powershell
cd "C:\Program Files\Pax"
.\update.ps1
```

#### 方法 2：手動更新

```powershell
# 1. 備份配置
Copy-Item ".env" -Destination ".env.backup"

# 2. 下載新版本
Invoke-WebRequest -Uri "https://github.com/stoday/PAX/releases/latest/download/pax-local.zip" -OutFile "pax-new.zip"
Expand-Archive -Path "pax-new.zip" -DestinationPath "." -Force
Remove-Item "pax-new.zip"

# 3. 恢復配置
Copy-Item ".env.backup" -Destination ".env"

# 4. 更新依賴
pip install -r requirements.txt --upgrade
cd "tools\mcp-google-map"
npm update
```

---

### 清理與卸載

#### 完全卸載

```powershell
# 1. 停止 Pax
taskkill /F /IM "PaxTrayApp.exe" /T

# 2. 刪除程式檔案
Remove-Item -Recurse -Force "C:\Program Files\Pax"

# 3. 刪除桌面捷徑
Remove-Item "$env:USERPROFILE\Desktop\Pax.lnk"

# 4. （可選）卸載 Node.js 和 Python
choco uninstall nodejs-lts python310 -y
```

---

## 常見問題 FAQ

### Q1：本地模式會消耗多少 LLM API 配額？

**A**：與雲端模式相同。每次對話都會呼叫 LLM API，消耗配額。本地模式只是將 LLM 處理邏輯放在本地，但仍需要呼叫 Gemini API。

---

### Q2：可以同時安裝本地模式和雲端模式嗎？

**A**：可以！兩種模式可以共存，只需要在啟動時設定不同的環境變數：
```powershell
# 本地模式
$env:PAX_MODE = "local"
.\PaxTrayApp.exe

# 雲端模式
$env:PAX_MODE = "cloud"
.\PaxTrayApp.exe
```

---

### Q3：本地模式的資料儲存在哪裡？

**A**：
- 程式檔案：`C:\Program Files\Pax\`
- 配置檔案：`C:\Program Files\Pax\.env`
- Log 檔案：`C:\Program Files\Pax\logs\`
- Cookie 快取：`C:\Users\{你的用戶名}\AppData\Local\Pax\`

---

### Q4：如何備份我的配置？

**A**：
```powershell
# 備份 .env 和 logs
Copy-Item "C:\Program Files\Pax\.env" -Destination "$env:USERPROFILE\Desktop\pax-backup.env"
Copy-Item -Recurse "C:\Program Files\Pax\logs" -Destination "$env:USERPROFILE\Desktop\pax-logs-backup"
```

---

### Q5：本地模式支援哪些作業系統？

**A**：目前只支援 Windows 10/11 (64-bit)。未來可能會支援 macOS 和 Linux。

---

## 技術支援

如果遇到無法解決的問題，請：

1. **查看 Log 檔案**：`C:\Program Files\Pax\logs\pax.log`
2. **提交 Issue**：https://github.com/stoday/PAX/issues
3. **聯繫開發團隊**：tsaiyuforwork@gmail.com

---

**文件版本**：v1.0  
**最後更新**：2026-01-16  
**作者**：Pax Team
