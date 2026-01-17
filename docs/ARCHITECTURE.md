# Pax 架構升級計畫：混合模式（雲端 + 本地）

## 📋 目錄
1. [升級目標](#升級目標)
2. [架構設計](#架構設計)
3. [運行模式](#運行模式)
4. [專案結構](#專案結構)
5. [技術棧](#技術棧)
6. [實作步驟](#實作步驟)
7. [API 設計](#api-設計)
8. [部署方案](#部署方案)
9. [測試策略](#測試策略)

---

## 升級目標

### 現況問題
- ❌ 打包後的 `.exe` 檔案過大（500+ MB）
- ❌ 需要在使用者電腦安裝 Node.js、Python 等環境
- ❌ LLM API Keys 分散在每個使用者電腦（安全風險）
- ❌ 更新 LLM 邏輯需要重新打包並分發 `.exe`
- ❌ 無法集中管理、監控使用情況

### 升級後優勢
- ✅ **可攜式套件 (Portable Dist)**：免安裝環境，解壓縮即可在任何 Windows 電腦運行。
- ✅ **內建 Runtime**：自帶 Embedded Python 與 Portable Node.js，不影響使用者電腦。
- ✅ **雙模式支援**：雲端模式（運算在伺服器）+ 本地模式（完全隱私）。
- ✅ **系統匣管理**：整合 Tray App，支援模式切換與 Token 自動獲取。

---

## 架構設計

### 核心理念：Runtime Adapter 模式

```
┌─────────────────────────────────────────────────┐
│              UI 層（共用）                       │
│  ┌──────────────┐  ┌──────────────┐            │
│  │ 系統匣 UI    │  │ CLI 介面     │            │
│  └──────────────┘  └──────────────┘            │
└─────────────────┬───────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────┐
│         Runtime Adapter（執行環境適配器）        │
│  ┌──────────────┐         ┌──────────────┐     │
│  │ LocalRuntime │   OR    │ CloudRuntime │     │
│  │ (本地執行)   │         │ (雲端執行)   │     │
│  └──────┬───────┘         └──────┬───────┘     │
└─────────┼────────────────────────┼─────────────┘
          │                        │
          ▼                        ▼
┌─────────────────────┐  ┌─────────────────────┐
│   本地執行環境       │  │   雲端執行環境       │
│  ┌────────────────┐ │  │  ┌────────────────┐ │
│  │ LLM Handler    │ │  │  │ API Client     │ │
│  │ MCP Tools      │ │  │  │ (HTTP)         │ │
│  │ Actions        │ │  │  └────────┬───────┘ │
│  └────────────────┘ │  │           │         │
└─────────────────────┘  └───────────┼─────────┘
                                     │
                                     ▼
                         ┌─────────────────────┐
                         │   後端伺服器         │
                         │  ┌────────────────┐ │
                         │  │ LLM Handler    │ │
                         │  │ MCP Tools      │ │
                         │  │ Actions        │ │
                         │  └────────────────┘ │
                         └─────────────────────┘
```

### 執行環境架構
```
Pax-Portable/
├── Pax.bat              # 🚀 啟動入口
├── .env                 # 🔑 本地配置與 API Keys
├── app/                 # 主程式進入點 (Console)
├── core/                # 🔥 共用核心邏輯
├── ui/                  # 🟢 系統匣 UI 與圖示
├── runtime/             # 🛠️ 執行環境
│   ├── python/          # Embedded Python 3.10
│   ├── node/            # Portable Node.js v20
│   ├── local/           # 本地執行器
│   └── cloud/           # 雲端客戶端執行器
└── tools/               # 外部 MCP 工具 (Google Map 等)
```

### 關鍵設計：共用核心邏輯

所有業務邏輯（LLM 處理、MCP 工具、指令定義）都在 `core/` 資料夾中，兩種模式共用：

```python
# core/runtime_adapter.py
from abc import ABC, abstractmethod

class RuntimeAdapter(ABC):
    """執行環境適配器"""
    
    @abstractmethod
    def process_message(self, message: str, cookies: dict):
        """處理用戶訊息，返回指令"""
        pass
    
    @abstractmethod
    def execute_action(self, action: dict, cookies: dict):
        """執行指令，返回結果"""
        pass
```

---

## 運行模式

### 模式 1：雲端模式（Cloud Mode）

**適用情境**：
- ✅ 大部分用戶（推薦）
- ✅ 需要快速安裝
- ✅ 不介意使用網路
- ✅ 信任後端管理 API Keys

**特點**：
- 📦 輕量級 `.exe`（20-30 MB）
- ⚡ 安裝快速（< 1 分鐘）
- ☁️ LLM 和 MCP 工具在後端執行
- 🔐 API Keys 集中管理
- 🔄 自動更新（只需更新後端）

**架構**：
```
使用者電腦                     後端伺服器
┌──────────────┐              ┌──────────────┐
│ PaxTrayApp   │─────HTTP────>│ FastAPI      │
│ (20 MB)      │<─────────────│ + LLM        │
│              │              │ + MCP Tools  │
└──────────────┘              └──────────────┘
```

---

### 模式 2：本地模式（Local Mode）

**適用情境**：
- ✅ 需要離線使用
- ✅ 對隱私要求極高
- ✅ 願意安裝環境
- ✅ 自行管理 API Keys

**特點**：
- 💻 需要安裝 Node.js + Python
- 📦 安裝包較大（~150 MB 依賴）
- 🔒 完全本地執行
- 🔑 API Keys 在本地管理
- 📴 可離線使用（除了呼叫 LLM API）

**架構**：
```
使用者電腦
┌─────────────────────────┐
│ PaxTrayApp              │
│ + Node.js (50 MB)       │
│ + Python (100 MB)       │
│ + LLM Handler           │
│ + MCP Tools             │
│ + 所有業務邏輯           │
└─────────────────────────┘
```

---

## 專案結構 (原始碼)

```
P2025_PAX/
├── app/                          # 互動式 Console UI
├── core/                         # 核心邏輯 (LLM, MCP, Actions)
├── docs/                         # 專案文檔
├── runtime/                      # 多模式執行適配器
├── scripts/                      # 建置工具 (build_portable.py)
├── tools/                        # 各式 MCP 工具原始碼
├── ui/                           # 系統匣常駐程式
├── portable_dist/                # 最終生成的發佈包
└── requirements.txt              # 相依套件定義
```

---

## 技術棧

### 共用核心（core/）
```python
# 業務邏輯相關
akasha-terminal==0.9.14      # LLM 處理
langchain-mcp-adapters==0.1.14  # MCP 工具
pydantic>=2.0.0              # 資料驗證
python-dotenv>=1.0.0         # 環境變數
```

### UI 層（ui/）
```python
pystray==0.19.5              # 系統匣圖示
pillow==10.0.0               # 圖示生成
rich==13.7.0                 # CLI 美化
selenium==4.15.0             # 瀏覽器自動化
```

### 雲端模式（runtime/cloud/）
```python
# 前端
requests==2.31.0             # HTTP 通訊

# 後端
fastapi==0.104.0             # API 框架
uvicorn[standard]==0.24.0    # ASGI 伺服器
```

### 本地模式（runtime/local/）
```
Node.js LTS                  # 執行 MCP Google Map
Python 3.10+                 # 執行主程式
```

---

## 實作步驟

### Phase 0：重構現有代碼（3-4 天）

#### 目標
將現有的單體架構重構為模組化架構，為混合模式做準備。

#### 步驟
1. **建立 `core/` 資料夾結構**
   ```bash
   mkdir -p core/{llm,mcp_tools,models,actions}
   ```

2. **遷移現有邏輯到 `core/`**
   - 將 `app/main.py` 的 LLM 邏輯移到 `core/llm/handler.py`
   - 將 `tools/` 的 MCP 工具移到 `core/mcp_tools/`
   - 將指令執行邏輯移到 `core/actions/`

3. **定義 Runtime Adapter 介面**
   ```python
   # core/runtime_adapter.py
   from abc import ABC, abstractmethod
   
   class RuntimeAdapter(ABC):
       @abstractmethod
       def process_message(self, message: str, cookies: dict):
           pass
       
       @abstractmethod
       def execute_action(self, action: dict, cookies: dict):
           pass
   ```

4. **測試重構後的代碼**
   - 確保所有功能正常
   - 執行現有的測試案例

#### ✅ Phase 0 測試案例

| 測試案例 | 測試步驟 | 預期結果 |
|---------|---------|---------|
| TC0.1: 核心邏輯獨立性 | Import `core` 模組 | 無依賴錯誤 |
| TC0.2: LLM 處理 | 調用 `LLMHandler` | 正常回應 |
| TC0.3: MCP 工具 | 調用各個 MCP 工具 | 正常運作 |
| TC0.4: 向後兼容 | 執行舊版測試 | 全部通過 |

---

### Phase 1：實作本地模式（4-5 天）

#### 1.1 實作 LocalRuntime

```python
# runtime/local/executor.py
from core.runtime_adapter import RuntimeAdapter
from core.llm.handler import LLMHandler
from core.actions.submit_work_time import submit_work_time

class LocalRuntime(RuntimeAdapter):
    """本地執行環境：所有邏輯都在本地執行"""
    
    def __init__(self):
        self.llm_handler = LLMHandler()
    
    def process_message(self, message: str, cookies: dict):
        # 直接在本地調用 LLM
        return self.llm_handler.process_message(message, cookies)
    
    def execute_action(self, action: dict, cookies: dict):
        # 直接在本地執行
        action_type = action["action"]
        params = action["params"]
        
        if action_type == "submit_work_time":
            return submit_work_time(cookies, **params)
        # ... 其他 action
```

#### 1.2 建立安裝腳本

詳見 `docs/LOCAL_MODE.md`

#### 1.3 修改 UI 支援本地模式

```python
# ui/tray_app.py
import os
from runtime.local.executor import LocalRuntime

# 讀取配置
MODE = os.getenv("PAX_MODE", "local")

if MODE == "local":
    runtime = LocalRuntime()

# 之後的代碼使用統一的 runtime 介面
```

#### ✅ Phase 1 測試案例

| 測試案例 | 測試步驟 | 預期結果 |
|---------|---------|---------|
| TC1.1: 環境安裝 | 執行 `setup_local.ps1` | Node.js + Python 安裝成功 |
| TC1.2: 本地執行 | 啟動 PaxTrayApp（本地模式） | 程式正常運行 |
| TC1.3: LLM 調用 | 發送訊息 | LLM 正常回應 |
| TC1.4: MCP 工具 | 調用 Google Map | 正常查詢 |
| TC1.5: 離線運行 | 斷網後執行 | 除了 LLM API，其他正常 |

---

### Phase 2：實作雲端模式（6-7 天）

#### 2.1 實作 CloudRuntime（Client）

```python
# runtime/cloud/client/executor.py
from core.runtime_adapter import RuntimeAdapter
import requests

class CloudRuntime(RuntimeAdapter):
    """雲端執行環境：通過 API 調用後端"""
    
    def __init__(self, server_url):
        self.server_url = server_url
    
    def process_message(self, message: str, cookies: dict):
        # 發送到後端
        response = requests.post(
            f"{self.server_url}/api/chat",
            json={"message": message, "cookies": cookies}
        )
        return response.json()
    
    def execute_action(self, action: dict, cookies: dict):
        # 在本地執行（需要使用者 Cookie 的操作）
        from core.actions.submit_work_time import submit_work_time
        
        if action["action"] == "submit_work_time":
            return submit_work_time(cookies, **action["params"])
        # ... 其他 action
```

#### 2.2 實作後端 Server

```python
# runtime/cloud/server/main.py
from fastapi import FastAPI
from core.llm.handler import LLMHandler

app = FastAPI(title="Pax Backend API")
llm_handler = LLMHandler()

@app.post("/api/chat")
async def chat(request: dict):
    action = await llm_handler.process_message(
        request["message"],
        request["cookies"]
    )
    return action
```

#### 2.3 修改 UI 支援雲端模式

```python
# ui/tray_app.py
import os
from runtime.local.executor import LocalRuntime
from runtime.cloud.client.executor import CloudRuntime

MODE = os.getenv("PAX_MODE", "cloud")

if MODE == "local":
    runtime = LocalRuntime()
elif MODE == "cloud":
    runtime = CloudRuntime(server_url=os.getenv("SERVER_URL"))
```

#### ✅ Phase 2 測試案例

詳見 `docs/TEST_CASES.md`

---

### Phase 3：模式切換與整合（2-3 天）

#### 3.1 實作模式切換功能

```python
# ui/tray_app.py
def switch_mode(self, new_mode):
    """切換運行模式"""
    os.environ["PAX_MODE"] = new_mode
    # 重新初始化 runtime
    self.runtime = self._init_runtime()
    # 提示用戶
    self.show_notification(f"已切換到{new_mode}模式")
```

#### 3.2 加入系統匣選單

```python
menu = pystray.Menu(
    pystray.MenuItem("打開 Pax", lambda: self.open_pax_console()),
    pystray.MenuItem("執行邏輯", lambda: self.run_logic()),
    pystray.MenuItem("停止執行", lambda: self.stop_logic()),
    pystray.MenuItem("切換模式", pystray.Menu(
        pystray.MenuItem("本地模式", lambda: self.switch_mode("local")),
        pystray.MenuItem("雲端模式", lambda: self.switch_mode("cloud"))
    )),
    pystray.MenuItem("結束常駐", self.on_quit)
)
```

---

### Phase 4：打包與部署（3-4 天）

#### 4.1 打包雲端版

```powershell
# 輕量級版本（只包含 UI 和 CloudRuntime）
pyinstaller --noconsole --onefile --name "PaxTrayApp-Cloud" `
    --add-data "config/cloud.env.example;config" `
    ui/tray_app.py
```

#### 4.2 打包本地版

```powershell
# 包含所有代碼
pyinstaller --noconsole --onefile --name "PaxTrayApp-Local" `
    --add-data "core;core" `
    --add-data "runtime/local;runtime/local" `
    --add-data "config/local.env.example;config" `
    ui/tray_app.py
```

#### 4.3 建立安裝包

```
releases/
├── pax-cloud-installer.exe      # 雲端版安裝包（20 MB）
├── pax-local-installer.exe      # 本地版安裝包（包含環境安裝腳本）
└── pax-hybrid.exe               # 混合版（支援兩種模式切換）
```

---

## API 設計

### POST /api/chat（雲端模式）

**請求**：
```json
{
  "message": "幫我填今天的工時，上班 9 點，下班 6 點",
  "cookies": {
    "ASP_NET_SESSION_ID": "...",
    "CLIENT_TICKET": "..."
  }
}
```

**回應**：
```json
{
  "action": "submit_work_time",
  "params": {
    "date": "2026-01-16",
    "start_time": "09:00",
    "end_time": "18:00",
    "reason": "忘刷"
  },
  "description": "將為您填寫 2026-01-16 的工時（09:00-18:00）",
  "requires_confirmation": true
}
```

---

## 部署方案

### 本地模式部署

1. 用戶下載 `pax-local-installer.exe`
2. 執行安裝程式（自動安裝 Node.js + Python）
3. 安裝完成後，執行 `PaxTrayApp.exe`
4. 配置 `.env`（API Keys）

### 雲端模式部署

#### 前端
1. 用戶下載 `PaxTrayApp-Cloud.exe`（20 MB）
2. 雙擊執行，立刻可用

#### 後端
```bash
# 部署到公司內網或雲端
cd runtime/cloud/server
docker build -t pax-backend .
docker run -p 8000:8000 pax-backend
```

---

## 測試策略

### 單元測試
- 測試 `core/` 中的所有模組
- 測試兩種 Runtime 的實作

### 整合測試
- 測試本地模式的完整流程
- 測試雲端模式的完整流程
- 測試模式切換功能

### 端到端測試
- 模擬真實用戶使用情境
- 測試所有核心功能

詳見 `docs/TEST_CASES.md`

---

## 時程估算

| 階段 | 工作內容 | 預估時間 |
|------|---------|---------|
| Phase 0 | 重構現有代碼 | 3-4 天 |
| Phase 1 | 實作本地模式 | 4-5 天 |
| Phase 2 | 實作雲端模式 | 6-7 天 |
| Phase 3 | 模式切換與整合 | 2-3 天 |
| Phase 4 | 打包與部署 | 3-4 天 |
| **總計** | | **18-23 天** |

---

## 下一步

1. ✅ **Review 本文件**：確認架構設計
2. ✅ **閱讀詳細文件**：
   - `docs/LOCAL_MODE.md` - 本地模式詳細說明
   - `docs/CLOUD_MODE.md` - 雲端模式詳細說明
   - `docs/TEST_CASES.md` - 測試案例
3. ✅ **開始 Phase 0**：重構現有代碼
4. ✅ **定期 Review**：每完成一個 Phase 就 Review 一次

---

**文件版本**：v2.0（混合模式）  
**最後更新**：2026-01-16  
**作者**：Pax Team
