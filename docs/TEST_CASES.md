# 測試案例補充文件

本文件補充 `ARCHITECTURE.md` 中各個 Phase 的詳細測試案例。

---

## Phase 2：LLM 整合測試案例

### ✅ 測試目標
確保 LLM 能正確處理用戶輸入並生成合適的指令

### 測試案例

| 測試案例 | 測試步驟 | 預期結果 | 驗證方式 |
|---------|---------|---------|---------|
| TC2.1: LLM 基礎回應 | 發送「你好」 | LLM 返回友善回應 | 回應內容合理且為中文 |
| TC2.2: 工時意圖識別 | 發送「幫我填今天的工時」 | 識別為工時提交意圖 | `action` 為 `submit_work_time` |
| TC2.3: 參數提取 | 發送「上班 9 點，下班 6 點」 | 正確提取時間參數 | `params` 包含 `start_time: "09:00"`, `end_time: "18:00"` |
| TC2.4: 日期解析 | 發送「填昨天的工時」 | 正確計算日期 | `params.date` 為昨天的日期 |
| TC2.5: 錯誤輸入處理 | 發送亂碼或無意義文字 | 返回提示訊息 | 回應包含「無法理解」或類似提示 |
| TC2.6: LLM 超時處理 | 模擬 LLM API 超時 | 返回超時錯誤 | 捕捉到 `TimeoutError` |

### 測試腳本

```python
# tests/test_phase2.py
import pytest
from datetime import datetime, timedelta
from server.llm.handler import LLMHandler

@pytest.fixture
def llm_handler():
    return LLMHandler()

def test_basic_response(llm_handler):
    """測試基礎回應"""
    result = llm_handler.process_message("你好", {})
    assert result["action"] in ["echo", "greeting"]
    assert len(result["params"]["message"]) > 0

def test_work_time_intent(llm_handler):
    """測試工時意圖識別"""
    result = llm_handler.process_message("幫我填今天的工時", {})
    assert result["action"] == "submit_work_time"

def test_time_extraction(llm_handler):
    """測試時間參數提取"""
    result = llm_handler.process_message(
        "幫我填今天的工時，上班 9 點，下班 6 點", {}
    )
    assert result["params"]["start_time"] == "09:00"
    assert result["params"]["end_time"] == "18:00"

def test_date_parsing(llm_handler):
    """測試日期解析"""
    result = llm_handler.process_message("填昨天的工時", {})
    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    assert result["params"]["date"] == yesterday

def test_invalid_input(llm_handler):
    """測試無效輸入"""
    result = llm_handler.process_message("asdfghjkl", {})
    assert "無法理解" in result["description"] or result["action"] == "clarify"
```

### 通過標準
- ✅ LLM 能正確識別至少 3 種常見意圖（工時、出差、查詢）
- ✅ 參數提取準確率 > 90%
- ✅ 日期時間解析正確
- ✅ 錯誤處理機制完善

---

## Phase 3：指令執行測試案例

### ✅ 測試目標
確保前端能正確執行後端返回的指令

### 測試案例

| 測試案例 | 測試步驟 | 預期結果 | 驗證方式 |
|---------|---------|---------|---------|
| TC3.1: Echo 指令 | 執行 `{"action": "echo", "params": {"message": "測試"}}` | 返回成功訊息 | `status` 為 `success` |
| TC3.2: 工時提交（Mock） | 執行工時提交指令（使用 Mock Cookie） | 模擬提交成功 | 返回成功訊息 |
| TC3.3: 未知指令 | 執行 `{"action": "unknown", ...}` | 返回錯誤訊息 | `status` 為 `error`，訊息包含「未知指令」 |
| TC3.4: 參數缺失 | 執行缺少必要參數的指令 | 返回參數錯誤 | 錯誤訊息指出缺少哪個參數 |
| TC3.5: Cookie 無效 | 使用無效 Cookie 執行指令 | 返回認證錯誤 | 錯誤訊息提示重新登入 |

### 測試腳本

```python
# tests/test_phase3.py
import pytest
from client.action_executor import ActionExecutor

@pytest.fixture
def mock_cookies():
    return {"session_id": "test_session"}

def test_echo_action(mock_cookies):
    """測試 Echo 指令"""
    executor = ActionExecutor(mock_cookies)
    result = executor.execute({
        "action": "echo",
        "params": {"message": "測試訊息"}
    })
    assert result["status"] == "success"
    assert result["message"] == "測試訊息"

def test_unknown_action(mock_cookies):
    """測試未知指令"""
    executor = ActionExecutor(mock_cookies)
    result = executor.execute({
        "action": "unknown_action",
        "params": {}
    })
    assert result["status"] == "error"
    assert "未知指令" in result["message"]

def test_missing_params(mock_cookies):
    """測試參數缺失"""
    executor = ActionExecutor(mock_cookies)
    result = executor.execute({
        "action": "submit_work_time",
        "params": {}  # 缺少必要參數
    })
    assert result["status"] == "error"
```

### 通過標準
- ✅ 所有已定義的指令都能正確執行
- ✅ 錯誤處理完善，能清楚提示錯誤原因
- ✅ 參數驗證機制正常運作

---

## Phase 4：MCP 工具整合測試案例

### ✅ 測試目標
確保 MCP 工具能正確整合到 LLM 流程中

### 測試案例

| 測試案例 | 測試步驟 | 預期結果 | 驗證方式 |
|---------|---------|---------|---------|
| TC4.1: Google Map 查詢 | 請求「查詢台北到新竹的距離」 | 返回正確距離 | 距離在合理範圍內（70-90 km） |
| TC4.2: 差旅費計算 | 請求「計算台北到高雄的差旅費」 | 返回計算結果 | 包含交通費、住宿費等項目 |
| TC4.3: 工具鏈調用 | 請求「幫我申請明天去高雄的出差」 | 依序調用多個工具 | 先查地址，再算費用，最後生成申請指令 |
| TC4.4: 工具錯誤處理 | Google Map API 失敗 | 返回降級方案 | 提示用戶手動輸入距離 |
| TC4.5: 並行工具調用 | 同時查詢多個地點 | 並行處理 | 總耗時 < 單次耗時 × 數量 |

### 測試腳本

```python
# tests/test_phase4.py
import pytest
from server.mcp_tools.google_map.handler import GoogleMapHandler
from server.mcp_tools.fare_calculator.calculator import FareCalculator

def test_google_map_distance():
    """測試 Google Map 距離查詢"""
    handler = GoogleMapHandler()
    result = handler.get_distance("台北市", "新竹市")
    assert 70 <= result["distance_km"] <= 90

def test_fare_calculation():
    """測試差旅費計算"""
    calculator = FareCalculator()
    result = calculator.calculate("台北", "高雄", days=1)
    assert "transport_fee" in result
    assert "accommodation_fee" in result
    assert result["total"] > 0

def test_tool_chain():
    """測試工具鏈調用"""
    from server.llm.handler import LLMHandler
    handler = LLMHandler()
    result = handler.process_message("幫我申請明天去高雄的出差", {})
    
    # 應該生成出差申請指令
    assert result["action"] == "apply_travel"
    assert "高雄" in str(result["params"])
```

### 通過標準
- ✅ 所有 MCP 工具都能正常運作
- ✅ 工具鏈調用邏輯正確
- ✅ 錯誤處理和降級方案完善
- ✅ 效能符合預期（單次查詢 < 3 秒）

---

## Phase 5：Cookie 管理測試案例

### ✅ 測試目標
確保 Cookie 管理機制穩定可靠

### 測試案例

| 測試案例 | 測試步驟 | 預期結果 | 驗證方式 |
|---------|---------|---------|---------|
| TC5.1: 首次取得 Cookie | 呼叫 `get_cookies()` | 開啟瀏覽器讓用戶登入 | 返回有效的 Cookie 字典 |
| TC5.2: Cookie 快取 | 連續兩次呼叫 `get_cookies()` | 第二次不開啟瀏覽器 | 第二次呼叫時間 < 1 秒 |
| TC5.3: Cookie 過期檢測 | 模擬 Cookie 過期（修改 `last_update`） | 自動刷新 Cookie | 重新開啟瀏覽器 |
| TC5.4: 強制刷新 | 呼叫 `get_cookies(force_refresh=True)` | 強制重新取得 | 開啟瀏覽器 |
| TC5.5: Cookie 持久化 | 重啟程式 | Cookie 仍然有效 | 不需要重新登入（可選功能） |

### 測試腳本

```python
# tests/test_phase5.py
import pytest
import time
from client.cookie_manager import CookieManager

def test_cookie_caching():
    """測試 Cookie 快取"""
    manager = CookieManager()
    
    # 第一次取得（需要登入）
    start = time.time()
    cookies1 = manager.get_cookies()
    first_time = time.time() - start
    
    # 第二次取得（使用快取）
    start = time.time()
    cookies2 = manager.get_cookies()
    second_time = time.time() - start
    
    assert cookies1 == cookies2
    assert second_time < 1  # 快取應該很快

def test_cookie_expiration():
    """測試 Cookie 過期"""
    manager = CookieManager()
    manager.get_cookies()
    
    # 模擬過期
    manager.last_update = time.time() - 7200  # 2 小時前
    
    # 應該重新取得
    assert manager._is_expired() == True
```

### 通過標準
- ✅ Cookie 快取機制正常運作
- ✅ 過期檢測準確
- ✅ 用戶體驗流暢（不會頻繁要求登入）

---

## Phase 6：整合測試案例

### ✅ 測試目標
端到端測試完整流程

### 測試案例

| 測試案例 | 測試步驟 | 預期結果 | 驗證方式 |
|---------|---------|---------|---------|
| TC6.1: 完整工時流程 | 用戶輸入「幫我填今天的工時」→ 確認 → 提交 | 工時成功提交 | 在 hrwt 系統中看到記錄 |
| TC6.2: 出差申請流程 | 用戶輸入「申請明天去高雄出差」→ 確認 → 提交 | 出差單成功提交 | 系統中看到申請記錄 |
| TC6.3: 多輪對話 | 用戶：「填工時」→ 系統：「幾點？」→ 用戶：「9 點到 6 點」 | 正確理解上下文 | 最終提交正確的時間 |
| TC6.4: 錯誤恢復 | 網路中斷 → 恢復 → 重試 | 自動重試成功 | 最終完成操作 |
| TC6.5: 並發請求 | 同時發送多個請求 | 都能正確處理 | 所有請求都有回應 |

### 測試腳本

```python
# tests/test_phase6_integration.py
import pytest
from client.cli_interface import PaxCLI

@pytest.fixture
def cli():
    return PaxCLI()

def test_full_work_time_flow(cli):
    """測試完整工時流程"""
    # 模擬用戶輸入
    user_input = "幫我填今天的工時，上班 9 點，下班 6 點"
    
    # 執行
    result = cli.process_input(user_input)
    
    # 驗證
    assert result["status"] == "success"
    assert "工時" in result["message"]

def test_multi_turn_conversation(cli):
    """測試多輪對話"""
    # 第一輪
    result1 = cli.process_input("填工時")
    assert "幾點" in result1["message"] or "時間" in result1["message"]
    
    # 第二輪（帶上下文）
    result2 = cli.process_input("9 點到 6 點")
    assert result2["status"] == "success"
```

### 通過標準
- ✅ 所有端到端流程都能順利完成
- ✅ 多輪對話上下文管理正確
- ✅ 錯誤恢復機制有效
- ✅ 並發處理穩定

---

## Phase 7：打包與部署測試案例

### ✅ 測試目標
確保打包後的程式能正常運作

### 測試案例

| 測試案例 | 測試步驟 | 預期結果 | 驗證方式 |
|---------|---------|---------|---------|
| TC7.1: 打包成功 | 執行 `pyinstaller` 指令 | 生成 `.exe` 檔案 | `dist/` 資料夾中有 `.exe` |
| TC7.2: 檔案大小 | 檢查 `.exe` 大小 | < 50 MB | `ls -lh dist/PaxTrayApp.exe` |
| TC7.3: 獨立運行 | 在乾淨的 Windows 環境執行 `.exe` | 程式正常啟動 | 系統匣出現圖示 |
| TC7.4: 功能完整性 | 執行所有核心功能 | 都能正常運作 | 工時提交、出差申請都成功 |
| TC7.5: 後端連線 | `.exe` 連接到生產環境後端 | 連線成功 | 能正常通訊 |

### 測試腳本

```powershell
# tests/test_phase7_deployment.ps1

# 測試打包
Write-Host "測試打包..."
cd client
pyinstaller --noconsole --onefile --name "PaxTrayApp" tray_app.py

# 檢查檔案
if (Test-Path "dist\PaxTrayApp.exe") {
    Write-Host "✅ 打包成功"
    
    # 檢查大小
    $size = (Get-Item "dist\PaxTrayApp.exe").Length / 1MB
    Write-Host "檔案大小: $size MB"
    
    if ($size -lt 50) {
        Write-Host "✅ 檔案大小符合預期"
    } else {
        Write-Host "❌ 檔案過大"
    }
} else {
    Write-Host "❌ 打包失敗"
}
```

### 通過標準
- ✅ 打包成功，無錯誤
- ✅ 檔案大小 < 50 MB
- ✅ 在乾淨環境中能獨立運行
- ✅ 所有功能正常

---

## 測試執行流程

### 每個 Phase 完成後

1. **執行單元測試**
   ```bash
   pytest tests/test_phase{N}.py -v
   ```

2. **執行整合測試**（Phase 3 之後）
   ```bash
   pytest tests/test_integration.py -v
   ```

3. **手動測試**
   - 按照測試案例表格逐項測試
   - 記錄測試結果

4. **Code Review**
   - 檢查代碼品質
   - 確認符合規範

5. **文件更新**
   - 更新 README
   - 記錄已知問題

### 全部 Phase 完成後

1. **完整回歸測試**
   ```bash
   pytest tests/ -v --cov
   ```

2. **效能測試**
   - 測試回應時間
   - 測試並發處理能力

3. **安全測試**
   - 檢查 Cookie 處理
   - 檢查 API 安全性

4. **用戶驗收測試（UAT）**
   - 邀請真實用戶測試
   - 收集反饋

---

## 測試工具

### 推薦工具
- **pytest**: 單元測試框架
- **pytest-cov**: 測試覆蓋率
- **requests-mock**: Mock HTTP 請求
- **selenium**: 瀏覽器自動化測試
- **locust**: 負載測試

### 安裝
```bash
pip install pytest pytest-cov requests-mock selenium locust
```

---

**文件版本**：v1.0  
**最後更新**：2026-01-16  
**作者**：Pax Team
