@echo off
chcp 65001 >nul
REM Pax 本地模式啟動腳本
REM 此腳本會啟動虛擬環境中的 Python 來執行 Pax

REM 取得腳本所在目錄
set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

REM 檢查虛擬環境是否存在
if not exist ".venv\Scripts\python.exe" (
    echo ❌ 找不到 Python 虛擬環境
    echo.
    echo 請確認 Pax 已正確安裝
    echo 或重新執行 setup_local.ps1
    echo.
    pause
    exit /b 1
)

REM 使用虛擬環境中的 Python 執行 Pax
start "" ".venv\Scripts\pythonw.exe" ui\tray_app.py
