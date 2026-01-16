# PAX 專案測試系統說明文件

PAX 專案目前採用 **pytest** 作為自動化測試框架，所有的測試腳本均存放在專案根目錄的 `tests/` 資料夾中。

## 1. 環境準備

在執行測試前，請確保你已進入正確的虛擬環境並安裝了必要的依賴：

```powershell
# 使用專案指定的虛擬環境
c:\Users\today\Projects\Envs\P2025_CLOCKMATE\.venv\Scripts\activate

# 確保已安裝 pytest
pip install pytest
```

## 2. 執行測試

### 執行所有測試
在專案根目錄下執行：
```powershell
python -m pytest
```

### 執行特定階段測試 (推薦)
如果你想驗證特定的開發進度，可以單獨執行特定檔案：
```powershell
# 驗證核心模組與資料模型 (Phase 0)
python -m pytest tests/test_phase0.py -v

# 驗證本地執行環境與指令執行 (Phase 1)
python -m pytest tests/test_phase1.py -v

# 驗證 LLM 與 MCP 工具的連接實況
python -m pytest tests/test_llm_handler.py -v
```

## 3. 測試檔案說明

| 檔案名稱 | 說明 | 關鍵驗證點 |
| :--- | :--- | :--- |
| `test_phase0.py` | 核心架構驗證 | 驗證 `core` 模組導入、Pydantic 資料模型建立。 |
| `test_phase1.py` | 本地運行環境 | 驗證 `LocalRuntime` 初始化、`echo` 指令執行邏輯。 |
| `test_llm_handler.py` | LLM 與 MCP 集成 | **核心測試**。驗證 MCP 工具路徑是否正確，以及 Akasha 是否能成功調優 `fare_estimator` 等工具。 |
| `test_akasha_mcp_simple.py` | 簡化版 MCP 測試 | 用於診斷 MCP 協議連接的基本健康狀況。 |

## 4. 進階技巧

*   **查看詳細輸出**：加上 `-v` 參數。
*   **查看 Print 內容**：pytest 預設會捕捉 stdout，如果要即時看到程式中的 `print` 輸出，請加上 `-s` 參數。
    ```powershell
    python -m pytest tests/test_phase1.py -vs
    ```
*   **跳過耗時測試**：部分測試會調用實際的 LLM API（標記為 `@pytest.mark.slow`），如果你只想快速檢查邏輯：
    ```powershell
    python -m pytest -m "not slow"
    ```

## 5. 常見問題與解決方案

### Q: 出現 `McpError: Connection closed`？
**A:** 這通常是因為 MCP 工具的 Python 腳本路徑不正確。請檢查 `core/llm/handler.py` 中的 `base_dir` 計算是否正確指向了專案根目錄。目前已修正為往上跳三層目錄。

### Q: Windows 下的編碼問題？
**A:** 我們在測試腳本中都加入了 UTF-8 強制轉碼邏輯，但建議在執行 PowerShell 時先執行：
```powershell
chcp 65001
```
