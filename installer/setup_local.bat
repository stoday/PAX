@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo.
echo ╔════════════════════════════════════════╗
echo ║   Pax 本地模式安裝程式                ║
echo ╚════════════════════════════════════════╝
echo.
echo 正在啟動 PowerShell 安裝腳本...
echo.
echo 如果出現安全提示，請選擇「執行」
echo.

REM 檢查 PowerShell 是否存在
where powershell >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo ❌ 找不到 PowerShell
    echo.
    echo 請確認您的 Windows 版本支援 PowerShell
    echo.
    pause
    exit /b 1
)

REM 執行 PowerShell 腳本
powershell -ExecutionPolicy Bypass -File "%~dp0setup_local.ps1"

REM 檢查執行結果
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ❌ 安裝失敗
    echo.
    echo 請嘗試以下方法：
    echo 1. 右鍵點擊 setup_local.ps1
    echo 2. 選擇「以系統管理員身分執行」
    echo.
    pause
    exit /b 1
)

echo.
echo 安裝腳本執行完成
echo.
pause
