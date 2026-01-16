# -*- coding: utf-8 -*-
"""
調試 LLMHandler 的路徑配置
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


def debug_paths():
    """調試路徑配置"""
    print("=" * 60)
    print("調試：LLMHandler 路徑配置")
    print("=" * 60)
    
    from core.llm.handler import LLMHandler
    
    handler = LLMHandler()
    connection_info = handler._get_mcp_connection_info()
    
    print(f"\nPython 解釋器: {sys.executable}")
    print(f"\n當前工作目錄: {os.getcwd()}")
    print(f"\nMCP 工具配置:")
    
    for name, info in connection_info.items():
        print(f"\n  [{name}]")
        print(f"    Transport: {info.get('transport')}")
        if 'command' in info:
            print(f"    Command: {info['command']}")
            print(f"    Args: {info.get('args', [])}")
            
            # 檢查檔案是否存在
            if 'args' in info and len(info['args']) > 0:
                script_path = info['args'][0]
                exists = os.path.exists(script_path)
                print(f"    檔案存在: {exists}")
                if not exists:
                    print(f"    [錯誤] 找不到檔案: {script_path}")


if __name__ == "__main__":
    debug_paths()
