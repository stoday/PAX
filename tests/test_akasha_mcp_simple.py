# -*- coding: utf-8 -*-
"""
簡化的 Akasha MCP 測試

只測試一個 MCP 工具，看看是否可以正常連接
"""

import sys
import os
import io

# 設定 UTF-8 編碼（Windows 必要）
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# 確保可以導入模組（從 tests 目錄往上一層到專案根目錄）
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_akasha_single_mcp():
    """測試 Akasha 連接單個 MCP 工具"""
    print("=" * 60)
    print("測試：Akasha 連接單個 MCP 工具 (fare_estimator)")
    print("=" * 60)
    
    try:
        import akasha
        
        # 取得專案根目錄（從 tests 目錄往上一層）
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        travel_helper_dir = os.path.join(base_dir, "tools", "travel_helper")
        python_exe = sys.executable
        
        # 只測試一個簡單的 MCP 工具
        connection_info = {
            "fare_estimator": {
                "command": python_exe,
                "args": [os.path.join(travel_helper_dir, "fare_estimator.py")],
                "transport": "stdio",
            }
        }
        
        print(f"Python 解釋器: {python_exe}")
        print(f"MCP 工具路徑: {os.path.join(travel_helper_dir, 'fare_estimator.py')}")
        print("\n建立 Akasha agent...")
        
        # 建立 agent
        agent = akasha.agents(
            model="gemini:gemini-2.5-flash",
            temperature=0.01,
            verbose=True
        )
        
        print("✓ Agent 建立成功")
        print("\n測試 MCP 連接...")
        
        # 簡單的測試 prompt
        prompt = "請使用 fare_estimator 工具查詢台北到新竹的高鐵票價"
        
        print(f"Prompt: {prompt}")
        print("\n調用 MCP agent...")
        
        # 調用 MCP agent
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
    """執行測試"""
    print("\n[Akasha MCP 簡化測試] 開始\n")
    
    result = test_akasha_single_mcp()
    
    print("\n" + "=" * 60)
    print("測試結果")
    print("=" * 60)
    
    if result:
        print("Akasha MCP 連接: [PASS]")
        print("\n[SUCCESS] Akasha 可以正常連接 MCP 工具！")
        return 0
    else:
        print("Akasha MCP 連接: [FAIL]")
        print("\n[WARNING] Akasha 無法連接 MCP 工具")
        print("\n可能的原因：")
        print("1. MCP 協議版本不匹配")
        print("2. akasha 的 MCP 配置有問題")
        print("3. 需要額外的環境設定")
        return 1


if __name__ == "__main__":
    exit(main())
