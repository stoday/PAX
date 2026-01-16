# -*- coding: utf-8 -*-
"""
MCP 工具獨立測試腳本

測試各個 MCP stdio 工具是否可以正常啟動
"""

import sys
import os
import io
import subprocess
import time

# 設定 UTF-8 編碼（Windows 必要）
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')


def test_mcp_tool(name, command, args, cwd=None):
    """測試單個 MCP 工具"""
    print("=" * 60)
    print(f"測試：{name}")
    print("=" * 60)
    print(f"指令：{command}")
    print(f"參數：{args}")
    if cwd:
        print(f"工作目錄：{cwd}")
    
    try:
        # 啟動 MCP 工具
        process = subprocess.Popen(
            [command] + args,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=cwd,
            text=True,
            encoding='utf-8'
        )
        
        # 等待一下看是否立即失敗
        time.sleep(1)
        
        # 檢查進程是否還在運行
        if process.poll() is None:
            print(f"✓ {name} 已成功啟動並正在運行")
            print(f"  進程 ID: {process.pid}")
            
            # 終止進程
            process.terminate()
            process.wait(timeout=2)
            print(f"  進程已終止")
            return True
        else:
            # 進程已經結束，讀取錯誤
            stdout, stderr = process.communicate()
            print(f"❌ {name} 啟動失敗")
            print(f"  返回碼: {process.returncode}")
            if stdout:
                print(f"  stdout: {stdout[:500]}")
            if stderr:
                print(f"  stderr: {stderr[:500]}")
            return False
    
    except Exception as e:
        print(f"❌ {name} 測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """執行所有測試"""
    print("\n[MCP 工具測試] 開始\n")
    
    # 取得專案根目錄（從 tests 目錄往上一層）
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    tools_dir = os.path.join(base_dir, "tools")
    travel_helper_dir = os.path.join(base_dir, "travel_helper")
    
    # 使用當前 Python 解釋器
    python_exe = sys.executable
    
    results = []
    
    # 測試 1: llm_uploader.py
    results.append((
        "submit_work_times (llm_uploader.py)",
        test_mcp_tool(
            "submit_work_times",
            python_exe,
            ["-X", "utf8", os.path.join(tools_dir, "llm_uploader.py")]
        )
    ))
    
    print("\n")
    
    # 測試 2: fare_estimator.py
    results.append((
        "fare_estimator",
        test_mcp_tool(
            "fare_estimator",
            python_exe,
            [os.path.join(travel_helper_dir, "fare_estimator.py")]
        )
    ))
    
    print("\n")
    
    # 測試 3: apply.py
    results.append((
        "dc_apply",
        test_mcp_tool(
            "dc_apply",
            python_exe,
            [os.path.join(travel_helper_dir, "apply.py")]
        )
    ))
    
    # 顯示結果
    print("\n" + "=" * 60)
    print("測試結果總結")
    print("=" * 60)
    
    for name, passed in results:
        status = "[PASS]" if passed else "[FAIL]"
        print(f"{name}: {status}")
    
    all_passed = all(result[1] for result in results)
    
    if all_passed:
        print("\n[SUCCESS] 所有 MCP 工具都可以正常啟動！")
        print("\n這表示 MCP 工具本身沒有問題。")
        print("問題可能出在 akasha 的 MCP 連接配置。")
        return 0
    else:
        print("\n[WARNING] 部分 MCP 工具無法啟動")
        print("\n請檢查：")
        print("1. Python 環境是否正確")
        print("2. 依賴套件是否都已安裝")
        print("3. 檔案路徑是否正確")
        return 1


if __name__ == "__main__":
    exit(main())
