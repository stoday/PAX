# -*- coding: utf-8 -*-
"""
測試多個 MCP 工具同時連接
"""

import sys
import os
import io

# 設定 UTF-8 編碼（Windows 必要）
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# 確保可以導入模組
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_multiple_mcp_tools():
    """測試連接多個 MCP 工具"""
    print("=" * 60)
    print("測試：連接多個 MCP 工具")
    print("=" * 60)
    
    try:
        import akasha
        
        base_dir = os.path.dirname(os.path.abspath(__file__))
        travel_helper_dir = os.path.join(base_dir, "travel_helper")
        python_exe = r"c:\Users\today\Projects\Envs\P2025_CLOCKMATE\.venv\Scripts\python.exe"
        
        # 連接兩個 MCP 工具
        connection_info = {
            "fare_estimator": {
                "command": python_exe,
                "args": [os.path.join(travel_helper_dir, "fare_estimator.py")],
                "transport": "stdio",
            },
            "dc_apply": {
                "command": python_exe,
                "args": [os.path.join(travel_helper_dir, "apply.py")],
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
        print("\n調用 MCP agent（連接 2 個工具）...")
        
        # 使用簡單的 prompt
        prompt = "請使用 fare_estimator 工具查詢台北到新竹的高鐵票價"
        
        response = agent.mcp_agent(connection_info, prompt)
        
        print("\n✓ 成功連接多個 MCP 工具！")
        print(f"回應: {response[:200]}...")
        
        return True
        
    except Exception as e:
        print(f"\n❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """執行測試"""
    print("\n[測試多個 MCP 工具] 開始\n")
    
    result = test_multiple_mcp_tools()
    
    print("\n" + "=" * 60)
    print("測試結果")
    print("=" * 60)
    
    if result:
        print("連接多個 MCP 工具: [PASS]")
        print("\n[SUCCESS] 測試通過！")
        return 0
    else:
        print("連接多個 MCP 工具: [FAIL]")
        print("\n[WARNING] 測試失敗")
        return 1


if __name__ == "__main__":
    exit(main())
