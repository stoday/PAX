# Akasha 與 MCP 工具測試報告

## ✅ 測試結果

### 1. Akasha 安裝狀態
- ✅ **已安裝**：akasha 模組可以正常導入
- ✅ **LLM 連接**：可以選擇 Gemini 模型（"selected gemini model"）
- ⏳ **待測試**：完整的 LLM 對話功能

### 2. MCP 工具位置確認

```
P2025_PAX/
├── tools/
│   ├── llm_uploader.py          # ✅ 工時提交工具
│   ├── mcp-google-map/          # Google Map MCP（重複）
│   └── travel_helper/           # 差旅助手（重複）
│
├── mcp-google-map/              # ✅ Google Map MCP（主要）
│   ├── package.json
│   └── ...
│
└── travel_helper/               # ✅ 差旅助手（主要）
    ├── fare_estimator.py        # 差旅費計算
    ├── apply.py                 # 出差申請
    └── ...
```

### 3. MCP 工具連接配置

已更新 `core/llm/handler.py` 使用正確的路徑：

```python
{
    "submit_work_times": {
        "command": "python",
        "args": ["-X", "utf8", "tools/llm_uploader.py"],
        "transport": "stdio",
    },
    "google-map": {
        "url": "http://localhost:3000/mcp",
        "transport": "streamable_http",
    },
    "fare_estimator": {
        "command": "python",
        "args": ["travel_helper/fare_estimator.py"],
        "transport": "stdio",
    },
    "dc_apply": {
        "command": "python",
        "args": ["travel_helper/apply.py"],
        "transport": "stdio",
    }
}
```

---

## ❌ 目前的問題

### 1. MCP 工具連接失敗

**錯誤訊息**：
```
mcp.shared.exceptions.McpError: Connection closed
```

**原因**：
- `submit_work_times` 工具（llm_uploader.py）無法啟動
- 可能是因為缺少依賴或環境問題

### 2. Google Map MCP 服務未啟動

**需要**：
- 啟動 `npm start` 在 `mcp-google-map/` 目錄
- 確保服務運行在 `http://localhost:3000/mcp`

---

## 🔧 解決方案

### 方案 1：先測試不使用 MCP 的功能

創建了 `test_akasha.py`，測試基本的 LLM 功能（不使用 MCP 工具）：

```python
agent = akasha.agents(model="gemini:gemini-2.5-flash")
response = agent.ask("請用一句話介紹你自己")
```

### 方案 2：啟動 Google Map MCP 服務

```powershell
cd mcp-google-map
npm install  # 如果還沒安裝
npm start
```

### 方案 3：檢查 llm_uploader.py 的依賴

```powershell
# 檢查 llm_uploader.py 是否可以獨立執行
python tools/llm_uploader.py
```

---

## 📋 下一步測試計畫

### 測試 1：基本 LLM 功能（不使用 MCP）
```bash
python test_akasha.py
```

**預期結果**：
- ✅ Akasha 可以正常建立 agent
- ✅ LLM 可以正常回應

### 測試 2：啟動 Google Map MCP
```bash
cd mcp-google-map
npm start
```

**預期結果**：
- ✅ 服務運行在 localhost:3000
- ✅ MCP 端點可訪問

### 測試 3：測試完整的 MCP 整合
```bash
python test_phase1.py
```

**預期結果**：
- ✅ 所有 MCP 工具可以連接
- ✅ LLM 可以調用 MCP 工具
- ✅ 完整的工作流程正常

---

## 💡 建議

1. **先執行 test_akasha.py**
   - 確認 akasha 和 Gemini 基本功能正常
   - 不依賴 MCP 工具

2. **啟動 Google Map MCP 服務**
   - 在另一個終端執行 `npm start`
   - 確保服務正常運行

3. **逐步測試 MCP 工具**
   - 先測試 Google Map（streamable_http）
   - 再測試其他工具（stdio）

4. **檢查 llm_uploader.py**
   - 確認它可以獨立執行
   - 檢查是否缺少依賴

---

**日期**：2026-01-16  
**狀態**：Akasha 已安裝，MCP 工具待測試
