# setup_local.ps1 - Pax 本地模式一鍵安裝腳本
# 版本：v1.0
# 使用方式：右鍵 → 以系統管理員身分執行

# 檢查管理員權限
if (-NOT ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")) {
    Write-Host ""
    Write-Host "❌ 需要管理員權限！" -ForegroundColor Red
    Write-Host ""
    Write-Host "請按照以下步驟操作：" -ForegroundColor Yellow
    Write-Host "1. 右鍵點擊此檔案 (setup_local.ps1)" -ForegroundColor White
    Write-Host "2. 選擇『以系統管理員身分執行』" -ForegroundColor White
    Write-Host ""
    pause
    exit 1
}

# 顯示歡迎訊息
Clear-Host
Write-Host ""
Write-Host "╔════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║   Pax 本地模式安裝程式 v1.0          ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""
Write-Host "即將安裝：" -ForegroundColor White
Write-Host "  • Chocolatey（套件管理器）" -ForegroundColor Gray
Write-Host "  • Node.js LTS (~50 MB)" -ForegroundColor Gray
Write-Host "  • uv（Python 套件管理器，會自動安裝 Python 3.10）" -ForegroundColor Gray
Write-Host "  • Pax 程式與依賴" -ForegroundColor Gray
Write-Host ""
Write-Host "預計時間：2-4 分鐘（uv 讓安裝更快！）" -ForegroundColor Yellow
Write-Host "需要網路連線" -ForegroundColor Yellow
Write-Host ""
$confirm = Read-Host "是否繼續？(Y/N)"
if ($confirm -ne "Y" -and $confirm -ne "y") {
    Write-Host ""
    Write-Host "安裝已取消" -ForegroundColor Yellow
    Write-Host ""
    pause
    exit 0
}

# 開始安裝
Write-Host ""
Write-Host "開始安裝..." -ForegroundColor Green
Write-Host ""

# 1. 安裝 Chocolatey
Write-Host "[1/5] 檢查 Chocolatey..." -ForegroundColor Yellow
if (!(Get-Command choco -ErrorAction SilentlyContinue)) {
    Write-Host "  → 安裝 Chocolatey..." -ForegroundColor Gray
    try {
        Set-ExecutionPolicy Bypass -Scope Process -Force
        [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072
        iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))
        Write-Host "  ✓ Chocolatey 安裝完成" -ForegroundColor Green
    } catch {
        Write-Host "  ❌ Chocolatey 安裝失敗: $_" -ForegroundColor Red
        pause
        exit 1
    }
} else {
    Write-Host "  ✓ Chocolatey 已安裝" -ForegroundColor Green
}

# 2. 安裝 Node.js
Write-Host ""
Write-Host "[2/5] 檢查 Node.js..." -ForegroundColor Yellow
if (!(Get-Command node -ErrorAction SilentlyContinue)) {
    Write-Host "  → 安裝 Node.js LTS（這可能需要幾分鐘）..." -ForegroundColor Gray
    try {
        choco install nodejs-lts -y
        refreshenv
        Write-Host "  ✓ Node.js 安裝完成" -ForegroundColor Green
    } catch {
        Write-Host "  ❌ Node.js 安裝失敗: $_" -ForegroundColor Red
        pause
        exit 1
    }
} else {
    $nodeVersion = node --version
    Write-Host "  ✓ Node.js 已安裝 ($nodeVersion)" -ForegroundColor Green
}

# 3. 安裝 uv（Python 套件管理器）
Write-Host ""
Write-Host "[3/5] 檢查 uv..." -ForegroundColor Yellow
if (!(Get-Command uv -ErrorAction SilentlyContinue)) {
    Write-Host "  → 安裝 uv（這可能需要幾分鐘）..." -ForegroundColor Gray
    try {
        choco install uv -y
        refreshenv
        Write-Host "  ✓ uv 安裝完成" -ForegroundColor Green
    } catch {
        Write-Host "  ❌ uv 安裝失敗: $_" -ForegroundColor Red
        pause
        exit 1
    }
} else {
    $uvVersion = uv --version
    Write-Host "  ✓ uv 已安裝 ($uvVersion)" -ForegroundColor Green
}

# 4. 下載並安裝 Pax
Write-Host ""
Write-Host "[4/5] 下載 Pax 程式..." -ForegroundColor Yellow
$InstallDir = "C:\Program Files\Pax"
New-Item -ItemType Directory -Path $InstallDir -Force | Out-Null

$DownloadUrl = "https://github.com/stoday/PAX/releases/latest/download/pax-local.zip"
$ZipPath = "$env:TEMP\pax-local.zip"

try {
    Write-Host "  → 下載中..." -ForegroundColor Gray
    Invoke-WebRequest -Uri $DownloadUrl -OutFile $ZipPath -UseBasicParsing
    
    Write-Host "  → 解壓縮中..." -ForegroundColor Gray
    Expand-Archive -Path $ZipPath -DestinationPath $InstallDir -Force
    Remove-Item $ZipPath
    
    Write-Host "  ✓ Pax 下載完成" -ForegroundColor Green
} catch {
    Write-Host "  ❌ 下載失敗: $_" -ForegroundColor Red
    Write-Host "  請檢查網路連線或稍後再試" -ForegroundColor Yellow
    Write-Host "  下載網址: $DownloadUrl" -ForegroundColor Gray
    pause
    exit 1
}

# 5. 使用 uv 建立虛擬環境並安裝依賴
Write-Host ""
Write-Host "[5/6] 使用 uv 建立 Python 環境..." -ForegroundColor Yellow

try {
    Set-Location $InstallDir
    
    # 使用 uv 建立虛擬環境（自動安裝 Python 3.10）
    Write-Host "  → 建立虛擬環境（uv 會自動安裝 Python 3.10）..." -ForegroundColor Gray
    uv venv --python 3.10
    Write-Host "  ✓ 虛擬環境建立完成" -ForegroundColor Green
    
    # 使用 uv 安裝套件（比 pip 快 10-100 倍）
    Write-Host "  → 安裝 Python 套件（使用 uv，速度超快）..." -ForegroundColor Gray
    uv pip install -r requirements.txt
    Write-Host "  ✓ Python 套件安裝完成" -ForegroundColor Green
} catch {
    Write-Host "  ❌ Python 環境設定失敗: $_" -ForegroundColor Red
    pause
    exit 1
}

# 6. 安裝 npm 依賴
Write-Host ""
Write-Host "[6/6] 安裝 npm 套件..." -ForegroundColor Yellow

try {
    Write-Host "  → 安裝 npm 套件..." -ForegroundColor Gray
    Set-Location "$InstallDir\tools\mcp-google-map"
    npm install --silent
    Write-Host "  ✓ npm 套件安裝完成" -ForegroundColor Green
} catch {
    Write-Host "  ❌ 依賴安裝失敗: $_" -ForegroundColor Red
    pause
    exit 1
}

# 7. 建立桌面捷徑
Write-Host ""
Write-Host "建立桌面捷徑..." -ForegroundColor Yellow
try {
    $WshShell = New-Object -comObject WScript.Shell
    $Shortcut = $WshShell.CreateShortcut("$env:USERPROFILE\Desktop\Pax.lnk")
    $Shortcut.TargetPath = "$InstallDir\PaxTrayApp.bat"  # 使用啟動腳本
    $Shortcut.WorkingDirectory = $InstallDir
    $Shortcut.Description = "Pax 便利工作助手（本地模式）"
    $Shortcut.WindowStyle = 7  # 最小化視窗（隱藏 cmd 視窗）
    $Shortcut.Save()
    Write-Host "  ✓ 桌面捷徑已建立" -ForegroundColor Green
} catch {
    Write-Host "  ⚠ 桌面捷徑建立失敗（不影響使用）" -ForegroundColor Yellow
}

# 7. 建立 .env 範例檔案
Write-Host ""
Write-Host "建立配置檔案..." -ForegroundColor Yellow
try {
    Set-Location $InstallDir
    if (!(Test-Path ".env")) {
        if (Test-Path "config\local.env.example") {
            Copy-Item "config\local.env.example" -Destination ".env"
            Write-Host "  ✓ 配置檔案已建立" -ForegroundColor Green
            Write-Host "  ⚠ 請記得編輯 .env 檔案，填入你的 GEMINI_API_KEY" -ForegroundColor Yellow
        }
    } else {
        Write-Host "  ✓ 配置檔案已存在" -ForegroundColor Green
    }
} catch {
    Write-Host "  ⚠ 配置檔案建立失敗（可手動建立）" -ForegroundColor Yellow
}

# 完成
Write-Host ""
Write-Host "╔════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "║   ✓ 安裝完成！                       ║" -ForegroundColor Green
Write-Host "╚════════════════════════════════════════╝" -ForegroundColor Green
Write-Host ""
Write-Host "安裝位置：$InstallDir" -ForegroundColor Cyan
Write-Host "桌面捷徑：已建立" -ForegroundColor Cyan
Write-Host ""
Write-Host "下一步：" -ForegroundColor Yellow
Write-Host "1. 編輯配置檔案：$InstallDir\.env" -ForegroundColor White
Write-Host "2. 填入你的 GEMINI_API_KEY" -ForegroundColor White
Write-Host "3. 雙擊桌面上的「Pax」圖示開始使用" -ForegroundColor White
Write-Host ""
Write-Host "如何取得 Gemini API Key：" -ForegroundColor Gray
Write-Host "https://makersuite.google.com/app/apikey" -ForegroundColor Gray
Write-Host ""
Write-Host "按任意鍵關閉..." -ForegroundColor Gray
pause
