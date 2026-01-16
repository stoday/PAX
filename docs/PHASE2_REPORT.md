# Phase 2 實作報告：雲端模式 (Cloud Mode)

## 📋 概述
Phase 2 的目標是實作 Pax 的**雲端模式**。在此模式下，重量級的 LLM 處理與 MCP 工具鏈運行在遠端伺服器上，而輕量級的客戶端僅負責訊息傳遞與本地指令執行。這不僅大幅縮減了分發包的大小，也簡化了客戶端的環境依賴。

## 🚀 關鍵實作內容

### 1. 雲端執行器 (CloudRuntime Client)
- **檔案路徑**: `runtime/cloud/client/executor.py`
- **功能**:
    - 實作 `RuntimeAdapter` 介面。
    - **訊息委託**: 透過 HTTP POST 將用戶訊息發送到後端 `/api/chat`。
    - **混合執行**: LLM 在雲端「思考」，但 Action（如 Selenium 自動化）在本地執行，確保能存取用戶的本地 Cookie 與資源。

### 2. 後端伺服器 (Pax Backend Server)
- **檔案路徑**: `runtime/cloud/server/main.py`
- **技術棧**: FastAPI, Uvicorn
- **功能**:
    - 提供 RESTful API 介面。
    - 封裝了 `core/llm/handler.py` 的產出，讓伺服器端具備完整的 MCP 調用能力。
    - 集中管理 API Keys 與 LLM 配置，降低前端暴露風險。

### 3. 客戶端整合與 UI 升級
- **檔案路徑**: `app/main.py`, `ui/tray_app.py`
- **功能**:
    - **模式切換**: 透過 `.env` 中的 `PAX_MODE` (local/cloud) 進行靜態切換。
    - **動態選單**: 系統匣 (Tray App) 新增「運行模式」子選單，支援在本地與雲端模式間即時切換。
    - **視覺化狀態指標**:
        - 🟢 **綠色**: 本地模式 (Local Mode)
        - 🔵 **青色**: 雲端模式 (Cloud Mode)
        - 🔴 **紅色**: 停止狀態

### 4. 測試與驗證 (test_phase2.py)
- **測試重點**:
    - 伺服器健康檢查。
    - 客戶端與伺服器的端到端通訊。
    - 雲端指令回傳後，客戶端的本地執行能力。
- **結果**: 通過 `pytest` 驗證，所有功能運作正常。

## 📊 測試結果總結
執行 `python -m pytest tests/test_phase2.py -v`：
- `test_server_health`: **PASSED**
- `test_cloud_runtime_process_message`: **PASSED** (LLM 集成測試成功)
- `test_cloud_runtime_execute_action_locally`: **PASSED**

## 💡 效益分析
- **體積最佳化**: 未來打包雲端版 `.exe` 時，可排除相關重量級依賴，預計體積可降至 30MB 以下。
- **部署靈活性**: 企業內部可統一佈署後端服務，用戶端只需輕量級安裝。
- **維護便利性**: 更新 LLM 提示詞 (Prompts) 或 MCP 工具只需在伺服器端修改，用戶端無需更新。

## ⏭️ 下一步計畫
1. **Phase 3**: 完善 UI 的連接重試機制與錯誤處理。
2. **Phase 4**: 執行 PyInstaller 打包流程，驗證「輕量版」的分發效果。
3. **功能擴充**: 整合真正的 `core/actions` 實作，取代目前的模擬回應。

---
**日期**: 2026-01-16  
**負責人**: Pax Team
