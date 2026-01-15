# 系統常駐程式開發與部署指南 (System Tray App)

本文件描述如何使用 `pystray`、`Pillow` 以及 `PyInstaller` 製作一個可以在 Windows 右下角系統匣常駐運行的 Python 程式。

## 1. 環境準備與概念

這個常駐程式（Tray App）本質上是一個 **Python 執行環境的封裝**。當你使用 PyInstaller 將其打包後，它會包含一個完整的 Python 解釋器。

我們的做法是讓「常駐程式」去呼叫（Spawn）另外一個「邏輯腳本」（`.py` 檔案）。這樣做的好處是：
- **解耦**：常駐邏輯（UI/系統匣）與業務邏輯內容分離。
- **動態執行**：只要環境（Library）匹配，你可以隨時更換目標腳本。

請確保已安裝必要套件：

```powershell
# 確保使用 UTF-8 編碼
chcp 65001

# 安裝依賴項
pip install pystray pillow pyinstaller
```

## 2. 程式架構 (`tray_app.py`)

現在的 `tray_app.py` 被設計為一個 **Runner**：
1. **自動偵測 Python 環境**：打包後會自動尋找系統的 Python 解釋器（支援 `python` 指令或 `uv` 管理的 Python）。
2. **`subprocess.Popen`**：使用找到的 Python 環境來執行指定的 `.py` 檔案。
3. **`CREATE_NO_WINDOW`**：在 Windows 上執行子程序時不彈出黑色的 cmd 視窗。
4. **狀態監控**：可以在系統匣選單中手動「執行」或「停止」該腳本。
5. **單一實例鎖**：使用 Socket 埠號（49152）確保同時只有一個程式實例在運行。

關鍵配置項：
```python
TARGET_SCRIPT = os.path.join(APP_DIR, "main_logic.py")  # 自動指向 .exe 所在目錄
LOCK_PORT = 49152  # 防止重複啟動的埠號
```

## 3. 打包為執行檔 (.exe)

為了讓程式在沒有 Python 環境的電腦運行，且不顯示黑色的命令提示字元視窗，我們使用 `PyInstaller`。

在 PowerShell 中執行：

```powershell
# 確保使用 UTF-8 編碼
chcp 65001

# 清理舊的編譯產物
Remove-Item -Recurse -Force .\dist, .\build -ErrorAction SilentlyContinue
Remove-Item -Force .\*.spec -ErrorAction SilentlyContinue

# 打包為無視窗版本
# --noconsole: 不顯示黑色視窗
# --onefile: 打包成單一執行檔
# --name: 指定產生的 exe 名稱
pyinstaller --noconsole --onefile --name "PaxTrayApp" tray_app.py
```

執行完畢後，你可以在 `./dist/` 資料夾中找到 `PaxTrayApp.exe`。

## 4. 使用方式

### 啟動程式
雙擊 `PaxTrayApp.exe`，你會在右下角系統匣看到一個圓點圖示：
- **綠色圓點**：`main_logic.py` 正在運行中
- **紅色圓點**：已停止

### 系統匣選單
在圓點上按右鍵，會出現選單：
- **執行腳本**：手動啟動 `main_logic.py`
- **停止執行**：停止正在運行的腳本
- **結束常駐**：完全關閉常駐程式

### 查看日誌
程式會在 `dist` 資料夾下產生兩個日誌檔：
- **`log.txt`**：`main_logic.py` 的業務日誌（每 10 秒寫入一次）
- **`debug_tray.log`**：常駐程式本身的除錯日誌

即時監控日誌：
```powershell
Get-Content .\dist\log.txt -Wait -Encoding UTF8
```

## 5. 自訂你的邏輯腳本

預設的 `main_logic.py` 只是一個測試範例。你可以：

1. **替換為你自己的腳本**：
   - 將你的 Python 腳本命名為 `main_logic.py`
   - 放在 `dist` 資料夾（與 `.exe` 同目錄）
   - 重新啟動 `PaxTrayApp.exe`

2. **修改目標腳本名稱**：
   - 編輯 `tray_app.py` 的第 19 行
   - 將 `TARGET_SCRIPT = os.path.join(APP_DIR, "main_logic.py")` 改為你的腳本名稱
   - 重新打包

## 6. 進階：打包其他依賴 (Datas)

如果你的 `main_logic.py` 需要讀取額外的檔案，或者你希望將 `main_logic.py` 直接包進 `.exe` 裡，可以使用 `--add-data`：

```powershell
# 將 main_logic.py 打包進去 (Windows 語法用分號 ;)
pyinstaller --noconsole --onefile --add-data "main_logic.py;." --name "PaxRunner" tray_app.py
```

## 7. 開機自動啟動

如果你希望程式在 Windows 開機時自動啟動：

1. 按 `Win + R`，輸入 `shell:startup`，按 Enter
2. 將 `PaxTrayApp.exe` 的**捷徑**複製到開啟的資料夾中
3. 重新啟動電腦測試

## 8. 常見問題與備註

### 環境一致性
子程序會繼承父程序的環境。如果你在 `main_logic.py` 中用了其他套件（如 `requests`），請確保系統的 Python 環境已經安裝了這些套件。

打包時 PyInstaller 只會掃描 `tray_app.py` 的 import。如果 `tray_app.py` 沒用到但子程序有用到，建議在 `tray_app.py` 中也補上 `import` 以確保 package 被包進去。

### 編碼問題
在 PowerShell 操作時，若內容包含中文，請務必先執行 `chcp 65001`。

### 路徑處理
所有路徑都使用絕對路徑，確保 `log.txt` 和 `main_logic.py` 一定會出現在 `.exe` 的同一個資料夾。

### 防止重複啟動
程式使用 Socket 埠號 `49152` 作為鎖。如果你需要同時運行多個不同的常駐程式，請修改 `LOCK_PORT` 為不同的值。

### 強制關閉程式
如果程式無法從系統匣正常關閉，可以使用 PowerShell 強制結束：
```powershell
taskkill /F /IM "PaxTrayApp.exe" /T
```

### Python 解釋器偵測
打包後的程式會依序嘗試以下方式尋找 Python：
1. 系統 PATH 中的 `python` 或 `python3`
2. `uv` 管理的 Python（位於 `%USERPROFILE%\AppData\Roaming\uv\python`）

如果找不到 Python，程式會在 `debug_tray.log` 中記錄錯誤。

## 9. 故障排除

### 程式啟動後立刻消失
檢查 `debug_tray.log`，可能原因：
- 埠號 49152 被其他程式佔用
- 找不到 Python 解釋器

### 看不到系統匣圖示
- 檢查是否有多個實例在運行（只有第一個會顯示圖示）
- 查看工作管理員是否有 `PaxTrayApp.exe` 在運行

### log.txt 沒有產生
- 確認 Python 子程序是否在運行：
  ```powershell
  Get-WmiObject Win32_Process -Filter "name='python.exe'" | Where-Object { $_.CommandLine -like "*main_logic*" }
  ```
- 檢查 `debug_tray.log` 中的子程序啟動記錄

### 編譯時出現 CopyIcons 錯誤
這通常是因為舊的 `.exe` 還在運行中。解決方法：
1. 先關閉所有 `PaxTrayApp.exe`
2. 刪除 `dist` 和 `build` 資料夾
3. 重新編譯

---

## 附錄：完整的開發流程

```powershell
# 1. 安裝依賴
chcp 65001
pip install pystray pillow pyinstaller

# 2. 開發測試（使用 Python 直接執行）
python tray_app.py

# 3. 打包為執行檔
Remove-Item -Recurse -Force .\dist, .\build -ErrorAction SilentlyContinue
Remove-Item -Force .\*.spec -ErrorAction SilentlyContinue
pyinstaller --noconsole --onefile --name "PaxTrayApp" tray_app.py

# 4. 測試執行檔
.\dist\PaxTrayApp.exe

# 5. 監控日誌
Get-Content .\dist\log.txt -Wait -Encoding UTF8

# 6. 關閉程式（在系統匣右鍵選擇「結束常駐」）
# 或使用指令強制關閉：
taskkill /F /IM "PaxTrayApp.exe" /T
```

---

**恭喜！你已經成功建立了一個 Windows 系統常駐程式！** 🎉
