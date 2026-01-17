# Pax 核心測試案例與驗證規範

本文件詳述 Pax 各個發展階段的測試案例、驗證方式及對應的實體測試腳本。

---

## 🟢 Phase 1 & 2：LLM 處理與意圖識別

### ✅ 測試目標
確保 LLM 能正確理解中文自然語言，並轉換為 `Action` JSON 格式。

| 測試案例 | 測試步驟 | 預期結果 | 驗證方式 |
|---------|---------|---------|---------|
| TC2.1: 基礎對話 | 輸入「你好」 | 返回客氣的回應 | `action` 為 `echo` 或 `greeting` |
| TC2.2: 工時意圖 | 輸入「幫我填今天的工時」 | 識別為工時提交 | `action` 為 `submit_work_time` |
| TC2.3: 參數提取 | 輸入「0900 到 1800」 | 提取正確時間 | `params` 包含 `start_time: "09:00"` |
| TC2.4: 差旅意圖 | 輸入「我要申請出差到台北」 | 識別為差旅申請 | `action` 為 `apply_travel` |

**驗證腳本**: `tests/test_phase1.py` & `tests/test_phase2.py`

---

## 🔵 Phase 3：統一指令執行與模式切換 (現狀)

### ✅ 測試目標
驗證「本地模式」與「雲端模式」下的指令執行穩定性，以及 UI 切換邏輯。

#### 1. 指令執行 (Action Execution)
| 測試案例 | 測試步驟 | 預期結果 | 驗證方式 |
|---------|---------|---------|---------|
| TC3.1: 統一入口測試 | 呼叫 `core.actions.execute_action` | 能正確路由到不同 Action 模組 | `tests/test_phase3.py` |
| TC3.2: 雲端本地執行 | 在 CloudRuntime 觸發 `execute_action` | 指令應在用戶本機執行而非伺服器 | `test_cloud_runtime_action_locally` |
| TC3.3: 網路重試 | 模擬伺服器斷線 (HTTP 500) | 自動觸發重試機制 (最多 3 次) | 檢查 `CloudRuntime` logs |

#### 2. 常駐 UI (Tray App)
| 測試案例 | 測試步驟 | 預期結果 | 驗證方式 |
|---------|---------|---------|---------|
| TC3.4: 模式持久化 | 切換模式後重啟 Pax | 自動載入 `pax_config.json` 的設定 | `tests/test_tray_logic.py` |
| TC3.5: 控制台啟動 | 點選「打開 Pax Console」 | 彈出新的 CMD 視窗執行 `app.main` | 手動觀察 |
| TC3.6: 系統通知 | 切換模式 (Local -> Cloud) | 右下角跳出 Windows 原生通知訊息 | 手動觀察 |

---

## 🔒 認證與安全性測試 (Authentication)

### ✅ 測試目標
驗證 Cookie 擷取流程與失效後的自我修復能力。

| 測試案例 | 測試步驟 | 預期結果 | 驗證方式 |
|---------|---------|---------|---------|
| TC5.1: 認證自動校驗 | 執行 `tests/debug_auth_token.py` | 成功存取 HRWT 並抓到 VIEWSTATE | 檢查控制台輸出綠色勾勾 |
| TC5.2: 指令失效引導 | 手動清空 SessionId 後填工時 | Pax 偵測 `auth_failed` 並彈出瀏覽器 | 觸發 `app.get_token.py` 流程 |
| TC5.3: 自動登入 | 設定 `EIP_USER` 環境變數後啟動 | Selenium 自動填入帳密並跳轉成功 | 觀察 Chrome 自動化過程 |

---

## 📦 Phase 4：打包與部署 (即將進行)

### ✅ 測試目標
確保打包後的獨立執行檔在乾淨環境中能正常執行。

| 測試案例 | 測試步驟 | 預期結果 | 驗證方式 |
|---------|---------|---------|---------|
| TC4.1: 雲端版體積 | 檢查 `dist/Pax-Cloud.exe` | 檔案大小 < 30MB | `ls -lh` |
| TC4.2: 依賴完整性 | 在未安裝 Python 的電腦執行 | 正常開啟 Tray 並連接雲端 | UI 正常顯示 & 指令回應 |
| TC4.3: 模式防呆 | 離線時切換到雲端模式 | 提示「無法連接伺服器」但不崩潰 | 觀察 Error Message |

---

## 🛠️ 測試執行指令表

### 單元/整合測試 (推薦)
```powershell
# 執行所有 Phase 測試
python -m pytest tests/ -v

# 執行特定 UI 邏輯測試
python -m pytest tests/test_tray_logic.py -v
```

### 診斷工具 (手動)
```powershell
# 測試目前的 .env 認證是否有效
python tests/debug_auth_token.py

# 啟動模擬 Server (用於測試雲端模式)
python runtime/cloud/server/main.py
```

---
**文件版本**：v2.0 (對應混合模式架構)  
**最後更新**：2026-01-16  
**作者**：Pax Team
