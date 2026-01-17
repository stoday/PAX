# Pax 便利工作助手

> **您的智慧行政助理 — 讓工時填寫與差旅申請變得前所未有的簡單。**

Pax 是一款整合了 LLM (Gemini) 與 MCP (Model Context Protocol) 技術的智慧助手，專為簡化繁瑣的行政流程而設計。

## 🚀 快速開始 (推薦：可攜式版本)

無需配置 Python 或 Node.js 環境，直接下載解壓縮即可使用：

1. **下載與啟動**：
   - 下載 `Pax-Portable.zip` 並解壓縮。
   - 執行 **`Pax.bat`**。
2. **配置金鑰**：
   - 編輯 `.env` 檔案，填入您的 `GEMINI_API_KEY`。
3. **開始使用**：
   - 在右下角系統匣選單點擊 **「打開 Pax Console」**。
   - 直接輸入：「幫我報今天 9 點到 6 點的工時」或「查詢去台中的油錢」。

---

## 🏗️ 專案特色

*   **雙模式路徑**：支援「本地模式」(Local) 保障隱私，與「雲端模式」(Cloud) 快速回應。
*   **免安裝環境**：內建嵌入式 Python 與 Node.js，不汙染系統環境。
*   **系統匣整合**：常駐背景執行，隨點隨用，支援自動獲取 Token。
*   **智慧 MCP 工具**：整合 Google Map 距離計算、工時自動提交、差旅費率查詢。

---

## 🛠️ 開發與建置

如果您是開發者，想要自行建置可攜式發佈包：

### 1. 環境需求
*   [Python 3.10+](https://www.python.org/)
*   建議使用 [uv](https://github.com/astral-sh/uv) 進行套件管理。

### 2. 安裝依賴
```powershell
pip install -r requirements.txt
```

### 3. 建置發佈包
執行內建的建置指令，這會自動下載 Python/Node Runtimes 並打包：
```powershell
python scripts/build_portable.py
```
生成的成品將位於 `portable_dist/` 目錄。

---

## 📂 常見文件
*   [使用者指南](docs/USER_GUIDE.md)：詳細的介面操作與配置說明。
*   [架構設計](docs/ARCHITECTURE.md)：深入了解 Pax 的混合適配器設計。
*   [編碼設定指南](docs/POWERSHELL_UTF8_SETUP.md)：解決 Windows 終端機亂碼問題。

---

## ⚠️ 注意事項
- 請確保 `.env` 中的 API Key 與 Session Cookies 妥善保管，切勿上傳至公開版本控管系統。
- 本工具僅供輔助使用，提交工時或申請前請務必再次核對 Console 輸出的資訊。

---
**License**: MIT  
**Author**: Pax Project Team
