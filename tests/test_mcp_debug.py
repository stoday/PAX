# -*- coding: utf-8 -*-
"""
MCP 連接詳細測試

測試 MCP 工具是否可以正常啟動和連接
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

# 確保可以導入模組
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_mcp_tool_standalone():
    """測試 MCP 工具是否可以獨立啟動"""
    print("=" * 60)
    print("測試：MCP 工具獨立啟動")
    print("=" * 60)
    
    base_dir = os.path.dirname(os.path.abspath(__file__))
    travel_helper_dir = os.path.join(base_dir, "travel_helper")
    fare_estimator_path = os.path.join(travel_helper_dir, "fare_estimator.py")
    
    # 使用虛擬環境的 Python
    python_exe = r"c:\Users\today\Projects\Envs\P2025_CLOCKMATE\.venv\Scripts\python.exe"
    
    print(f"Python: {python_exe}")
    print(f"MCP 工具: {fare_estimator_path}")
    print(f"工具存在: {os.path.exists(fare_estimator_path)}")
    
    try:
        # 嘗試啟動 MCP 工具
        print("\n啟動 MCP 工具...")
        proc = subprocess.Popen(
            [python_exe, fare_estimator_path],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding='utf-8'
        )
        
        # 等待一下讓工具啟動
        time.sleep(2)
        
        # 檢查進程是否還在運行
        poll_result = proc.poll()
        if poll_result is not None:
            # 進程已經結束
            stdout, stderr = proc.communicate()
            print(f"\n❌ MCP 工具啟動後立即退出 (exit code: {poll_result})")
            print(f"\nSTDOUT:\n{stdout}")
            print(f"\nSTDERR:\n{stderr}")
            return False
        else:
            print("✓ MCP 工具正在運行")
            
            # 嘗試發送一個簡單的 MCP 初始化請求
            print("\n發送 MCP 初始化請求...")
            init_request = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {
                        "name": "test-client",
                        "version": "1.0.0"
                    }
                }
            }
            
            import json
            request_str = json.dumps(init_request) + "\n"
            print(f"請求: {request_str}")
            
            try:
                proc.stdin.write(request_str)
                proc.stdin.flush()
                
                # 等待回應
                time.sleep(1)
                
                # 讀取回應（非阻塞）
                import select
                if sys.platform == 'win32':
                    # Windows 不支援 select，直接嘗試讀取
                    print("(Windows 環境，嘗試讀取回應...)")
                    # 設定超時
                    proc.stdout.flush()
                    response = proc.stdout.readline()
                    if response:
                        print(f"✓ 收到回應: {response}")
                        proc.terminate()
                        return True
                    else:
                        print("❌ 沒有收到回應")
                        proc.terminate()
                        return False
                
            except Exception as e:
                print(f"❌ 發送請求時發生錯誤: {e}")
                proc.terminate()
                return False
            
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_akasha_mcp_connection():
    """測試 Akasha 連接 MCP"""
    print("\n" + "=" * 60)
    print("測試：Akasha 連接 MCP")
    print("=" * 60)
    
    try:
        import akasha
        
        base_dir = os.path.dirname(os.path.abspath(__file__))
        travel_helper_dir = os.path.join(base_dir, "travel_helper")
        python_exe = r"c:\Users\today\Projects\Envs\P2025_CLOCKMATE\.venv\Scripts\python.exe"
        
        connection_info = {
            "fare_estimator": {
                "command": python_exe,
                "args": [os.path.join(travel_helper_dir, "fare_estimator.py")],
                "transport": "stdio",
            }
        }
        
        print(f"建立 Akasha agent...")
        agent = akasha.agents(
            model="gemini:gemini-2.5-flash",
            temperature=0.01,
            verbose=True
        )
        
        print("✓ Agent 建立成功")
        print("\n調用 MCP agent...")
        
        # 使用簡單的 prompt
        prompt = "請使用 fare_estimator 工具查詢台北到新竹的高鐵票價"
        
        response = agent.mcp_agent(connection_info, prompt)
        
        print("\n✓ MCP 連接成功！")
        print(f"回應: {response[:200]}...")
        
        return True
        
    except Exception as e:
        print(f"\n❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """執行所有測試"""
    print("\n[MCP 詳細測試] 開始\n")
    
    results = []
    
    # 測試 1: MCP 工具獨立啟動
    results.append(("MCP 工具獨立啟動", test_mcp_tool_standalone()))
    
    # 測試 2: Akasha 連接 MCP
    results.append(("Akasha 連接 MCP", test_akasha_mcp_connection()))
    
    # 顯示結果
    print("\n" + "=" * 60)
    print("測試結果總結")
    print("=" * 60)
    
    for name, passed in results:
        status = "[PASS]" if passed else "[FAIL]"
        print(f"{name}: {status}")
    
    all_passed = all(result[1] for result in results)
    
    if all_passed:
        print("\n[SUCCESS] 所有測試通過！")
        return 0
    else:
        print("\n[WARNING] 部分測試失敗")
        return 1


if __name__ == "__main__":
    exit(main())
