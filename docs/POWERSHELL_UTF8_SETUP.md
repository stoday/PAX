# PowerShell UTF-8 編碼設定指南

## 問題說明
PowerShell 預設使用 Big5 編碼，導致中文顯示亂碼。

## 解決方案

### 方法 1：設定 PowerShell Profile（推薦）

1. 開啟 PowerShell（以系統管理員身分執行）

2. 執行以下指令來編輯 Profile：
```powershell
notepad $PROFILE
```

3. 如果出現「找不到檔案」的訊息，先建立檔案：
```powershell
New-Item -Path $PROFILE -ItemType File -Force
notepad $PROFILE
```

4. 在記事本中加入以下內容：
```powershell
# 設定 UTF-8 編碼
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8
chcp 65001 | Out-Null
```

5. 儲存並關閉記事本

6. 重新開啟 PowerShell，設定就會自動生效

---

### 方法 2：每次手動執行（臨時方案）

在每次開啟 PowerShell 後執行：
```powershell
chcp 65001
```

---

### 方法 3：修改 Windows Terminal 設定（如果使用 Windows Terminal）

1. 開啟 Windows Terminal
2. 按 `Ctrl + ,` 開啟設定
3. 在左側選擇「PowerShell」
4. 在「命令列」欄位中，將：
   ```
   powershell.exe
   ```
   改為：
   ```
   powershell.exe -NoExit -Command "chcp 65001"
   ```

---

## 驗證設定

執行以下指令來驗證編碼設定：
```powershell
[Console]::OutputEncoding
chcp
```

應該會顯示：
```
BodyName          : utf-8
EncodingName      : Unicode (UTF-8)
...

Active code page: 65001
```

---

## 給 AI 助手的提示

如果你使用 AI 助手（如 Antigravity）執行 PowerShell 指令，可以在 User Rules 中加入：

```
在使用 powershell 指令時，要注意編碼的問題。請在執行 powershell 指令之前，先下指令 `chcp 65001` 來確保是使用 UTF-8 來顯示。
```

這樣 AI 助手就會自動在每次執行 PowerShell 指令時先設定 UTF-8 編碼。

---

## 常見問題

### Q: 為什麼每次都要設定？
A: 因為 PowerShell 預設使用系統編碼（Windows 中文版是 Big5）。設定 Profile 後就只需要設定一次。

### Q: 設定後還是亂碼怎麼辦？
A: 
1. 確認 Profile 檔案已儲存
2. 重新開啟 PowerShell
3. 執行 `chcp` 確認是否為 65001

### Q: 會影響其他程式嗎？
A: 不會，這只影響 PowerShell 的顯示編碼。

---

**建議**：使用方法 1（設定 Profile），一勞永逸！
