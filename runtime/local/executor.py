# -*- coding: utf-8 -*-
"""
Local Runtime Executor - 本地執行環境

這個模組實作了本地執行模式，所有業務邏輯都在本地執行規定。
"""

import sys
import os
import subprocess
from typing import Dict, Any, Optional

# 確保可以導入 core 模組
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from core.runtime_adapter import RuntimeAdapter
from core.llm.handler import LLMHandler


class LocalRuntime(RuntimeAdapter):
    """
    本地執行環境
    
    所有邏輯（LLM 處理、MCP 工具、指令執行）都在本地執行。
    適合需要離線使用或對隱私要求極高的用戶。
    """
    
    def __init__(self):
        """初始化本地執行環境"""
        self.llm_handler = LLMHandler()
        self.mcp_process = None
        
        # 啟動 Google Map MCP 服務
        self._start_mcp_google_map()
        
        print("[LocalRuntime] 本地執行環境已初始化")
    
    def _start_mcp_google_map(self):
        """啟動 Google Map MCP 服務"""
        try:
            # 檢查服務是否已經在運行
            if self.mcp_process and self.mcp_process.poll() is None:
                print("[LocalRuntime] Google Map MCP 服務已在運行")
                return
            
            # 取得專案根目錄
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            mcp_dir = os.path.join(base_dir, "tools", "mcp-google-map")
            
            # 檢查目錄是否存在
            if not os.path.exists(mcp_dir):
                print(f"[LocalRuntime] 警告：找不到 mcp-google-map 目錄: {mcp_dir}")
                return
            
            # 啟動服務（在背景執行）
            CREATE_NEW_CONSOLE = subprocess.CREATE_NEW_CONSOLE if hasattr(subprocess, "CREATE_NEW_CONSOLE") else 0x00000010
            
            # 決定 node 指令：優先使用可攜式環境內的 node.exe
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            portable_node = os.path.join(base_dir, "runtime", "node", "node.exe")
            
            try:
                if os.path.exists(portable_node):
                    log_msg = f"[LocalRuntime] 使用可攜式 Node: {portable_node}"
                    index_js = os.path.join(mcp_dir, "dist", "index.js")
                    # 如果 dist/index.js 不存在，嘗試直接 npm start
                    if os.path.exists(index_js):
                        cmd = [portable_node, index_js]
                        shell_mode = False
                    else:
                        cmd = ["npm.cmd", "start"] # 假設在 PATH 中
                        shell_mode = True
                else:
                    # 一般開發環境
                    cmd = ["npm", "start"]
                    shell_mode = True

                self.mcp_process = subprocess.Popen(
                    cmd,
                    cwd=mcp_dir,
                    env=os.environ.copy(),
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    shell=shell_mode,
                    creationflags=CREATE_NEW_CONSOLE if sys.platform == 'win32' else 0
                )
                print("[LocalRuntime] Google Map MCP 服務已啟動")
                
            except Exception as e:
                print(f"[LocalRuntime] 警告：無法啟動 Google Map MCP 服務: {e}")
            
        except Exception as e:
            print(f"[LocalRuntime] 警告：無法啟動 Google Map MCP 服務: {e}")
    
    def process_message(
        self, 
        message: str, 
        cookies: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        處理用戶訊息（本地執行）
        
        Args:
            message: 用戶輸入的訊息
            cookies: 用戶的認證 Cookie（可選）
        
        Returns:
            包含 action 和 params 的字典
        """
        print(f"[LocalRuntime] 處理訊息: {message[:50]}...")
        
        # 直接在本地調用 LLM Handler（同步方法）
        action = self.llm_handler.process_message(message, cookies)
        
        return action
    
    def execute_action(
        self, 
        action: Dict[str, Any], 
        cookies: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        在本地執行指令
        
        可以直接使用 core/actions 下的實作。
        """
        from core.actions import execute_action
        
        action_type = action.get("action")
        params = action.get("params", {})
        
        print(f"[LocalRuntime] 在本地執行指令: {action_type}")
        
        # 使用統一的 Action 執行入口
        return execute_action(action_type, params, cookies)
