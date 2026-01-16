# 為什麼使用 uv？

## 🚀 uv 簡介

`uv` 是由 Astral 開發的極速 Python 套件管理器，用 Rust 編寫，比傳統的 `pip` 快 **10-100 倍**。

官網：https://github.com/astral-sh/uv

---

## ⚡ 速度對比

### 安裝 Pax 依賴套件（~30 個套件）

| 工具 | 時間 | 速度 |
|------|------|------|
| **pip** | ~2-3 分鐘 | 基準 |
| **uv** | ~10-20 秒 | **10-18 倍快** |

### 建立虛擬環境

| 工具 | 時間 | 速度 |
|------|------|------|
| **python -m venv** | ~5-10 秒 | 基準 |
| **uv venv** | ~1-2 秒 | **5-10 倍快** |

---

## 🎯 Pax 使用 uv 的優勢

### 1. **更快的安裝體驗**
```
舊方案（使用 pip）：
[5/6] 安裝 Python 套件...
  → 安裝中...（等待 2-3 分鐘）
  ✓ 完成

新方案（使用 uv）：
[5/6] 使用 uv 安裝 Python 套件...
  → 安裝中...（等待 10-20 秒）
  ✓ 完成（超快！）
```

**總安裝時間**：
- 舊方案：3-5 分鐘
- 新方案：2-4 分鐘（節省 1-2 分鐘）

---

### 2. **自動管理 Python 版本**

uv 會自動下載並管理 Python 3.10，不需要：
- ❌ 手動下載 Python 安裝檔
- ❌ 擔心 Python 版本衝突
- ❌ 設定 PATH 環境變數

```powershell
# 舊方案
choco install python310 -y  # 下載 ~100 MB，安裝 ~2 分鐘

# 新方案
uv venv --python 3.10  # 自動下載並建立環境，~30 秒
```

---

### 3. **更好的依賴解析**

uv 使用先進的依賴解析算法，避免套件衝突：
- ✅ 自動解決版本衝突
- ✅ 產生可重現的環境
- ✅ 支援 `pyproject.toml` 和 `requirements.txt`

---

### 4. **跨平台一致性**

uv 在 Windows、macOS、Linux 上行為完全一致：
- ✅ 相同的指令
- ✅ 相同的速度
- ✅ 相同的結果

---

## 📊 技術細節

### uv 的工作原理

1. **並行下載**：同時下載多個套件
2. **快取機制**：已下載的套件不會重複下載
3. **增量安裝**：只安裝變更的套件
4. **Rust 實作**：原生速度，無 Python 解釋器開銷

### uv 管理的 Python

```
C:\Users\{用戶名}\AppData\Roaming\uv\python\
├── cpython-3.10.x-windows-x86_64/
│   ├── python.exe
│   ├── pythonw.exe
│   └── ...
└── cpython-3.11.x-windows-x86_64/
    └── ...
```

uv 會自動下載並快取 Python，每個專案可以使用不同版本。

---

## 🔧 Pax 中的 uv 使用

### 安裝腳本中的 uv 指令

```powershell
# 1. 安裝 uv
choco install uv -y

# 2. 建立虛擬環境（自動安裝 Python 3.10）
uv venv --python 3.10

# 3. 安裝依賴（超快！）
uv pip install -r requirements.txt
```

### 虛擬環境結構

```
C:\Program Files\Pax\
├── .venv/                    # uv 建立的虛擬環境
│   ├── Scripts/
│   │   ├── python.exe       # Python 3.10
│   │   └── pythonw.exe
│   └── Lib/
│       └── site-packages/   # uv 安裝的套件
└── requirements.txt
```

---

## 🆚 uv vs pip 詳細對比

| 功能 | pip | uv |
|------|-----|-----|
| 安裝速度 | 慢 | **10-100 倍快** |
| 依賴解析 | 基礎 | **先進** |
| Python 管理 | ❌ 不支援 | ✅ 自動管理 |
| 快取機制 | 基礎 | **智能快取** |
| 並行下載 | ❌ 序列 | ✅ 並行 |
| 跨平台 | ✅ 是 | ✅ 是 |
| 記憶體使用 | 高 | **低** |
| 實作語言 | Python | **Rust** |

---

## 💡 常見問題

### Q1：uv 穩定嗎？

**A**：是的！uv 由 Astral（Ruff 的開發團隊）開發，已被廣泛使用：
- ✅ GitHub Stars: 30,000+
- ✅ 每月下載量: 1,000,000+
- ✅ 被 FastAPI、Pydantic 等知名專案使用

---

### Q2：uv 會取代 pip 嗎？

**A**：uv 是 pip 的替代品，但兩者可以共存：
- uv 用於**快速安裝**和**環境管理**
- pip 仍然可以在虛擬環境中使用

---

### Q3：如果 uv 安裝失敗怎麼辦？

**A**：安裝腳本會自動檢測並提示錯誤。你也可以：
1. 手動安裝 uv：`choco install uv`
2. 或回退到傳統的 pip 方案（修改安裝腳本）

---

### Q4：uv 需要額外的磁碟空間嗎？

**A**：uv 會快取 Python 和套件，但：
- Python 快取：~100 MB（每個版本）
- 套件快取：~50-200 MB（視使用情況）
- **總計**：比傳統方案節省空間（因為共享快取）

---

### Q5：可以手動使用 uv 嗎？

**A**：當然可以！安裝 Pax 後，你可以：

```powershell
# 進入 Pax 目錄
cd "C:\Program Files\Pax"

# 使用 uv 安裝新套件
uv pip install requests

# 使用 uv 更新套件
uv pip install --upgrade akasha-terminal

# 使用 uv 列出已安裝套件
uv pip list
```

---

## 🎓 延伸閱讀

- [uv 官方文件](https://docs.astral.sh/uv/)
- [uv GitHub](https://github.com/astral-sh/uv)
- [為什麼 uv 這麼快？](https://astral.sh/blog/uv)

---

**總結**：使用 uv 讓 Pax 的安裝更快、更穩定、更現代化！🚀

---

**文件版本**：v1.0  
**最後更新**：2026-01-16  
**作者**：Pax Team
