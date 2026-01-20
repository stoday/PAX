# -*- coding: utf-8 -*-
"""
Cloud Runtime Executor - 雲端執行環境 (Client 端)

這個模組實作了雲端執行模式，訊息處理由遠端伺服器完成，
而具體的指令執行（Actions）則在本地完成，以便使用本地 Cookie 和環境。
"""

import requests
import os
from typing import Dict, Any, Optional
from core.runtime_adapter import RuntimeAdapter


class CloudRuntime(RuntimeAdapter):
    """
    雲端執行環境
    
    將 LLM 處理委託給後端伺服器，本地負責執行指令。
    適合輕量級安裝，且不需要在本地運行複雜的 LLM 和 MCP 工具。
    """
    
    def __init__(self, server_url: str = None):
        """
        初始化雲端執行環境
        
        Args:
            server_url: 後端伺服器 URL。如果為 None，則依序從 環境變數 PAX_SERVER_URL 與 config.toml 讀取。
        """
        # 1. 優先使用傳入參數
        self.server_url = server_url
        
        # 2. 其次使用環境變數
        if not self.server_url:
            self.server_url = os.getenv("PAX_SERVER_URL")
            
        # 3. 再其次從 config.toml 讀取
        if not self.server_url:
            try:
                import tomli
                # 假設 config.toml 在 root (與 app/core 同層)
                # CloudRuntime 通常在 runtime/cloud/client/executor.py
                # dist 結構下，root 是 dist/cloud/client/
                # 所以 config.toml 在 ../../../config.toml ? 
                # 不，在 build_cloud_service.py 中，config.toml 是被複製到 CLIENT_DIR 的 root。
                # 而 executor.py 会被导入。我们需要找到正确的 root。
                # 在 client 中，PYTHONPATH 會包含 CLIENT_DIR。
                base_dir = os.getcwd() # 啟動時的目錄，通常是 root
                config_path = os.path.join(base_dir, "config.toml")
                if os.path.exists(config_path):
                    with open(config_path, "rb") as cf:
                        config = tomli.load(cf)
                        self.server_url = config.get("server", {}).get("server_url")
            except:
                pass
                
        # 4. 最後使用預設值
        if not self.server_url:
            self.server_url = "http://localhost:8000"
            
        print(f"[CloudRuntime] 雲端執行環境已初始化，伺服器: {self.server_url}")
    
    def process_message(
        self, 
        message: str, 
        cookies: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        將訊息發送到後端伺服器處理 (含 API Key 與極簡格式解析)
        """
        import time
        import re
        max_retries = 3
        retry_delay = 2
        
        api_key = os.getenv("PAX_CLOUD_API_KEY", "")
        headers = {"X-API-KEY": api_key} if api_key else {}
        
        for attempt in range(max_retries):
            try:
                print(f"[CloudRuntime] 發送訊息到雲端 (嘗試 {attempt+1}/{max_retries}): {message[:50]}...")
                response = requests.post(
                    f"{self.server_url}/api/chat",
                    json={"message": message, "cookies": cookies},
                    headers=headers,
                    timeout=600
                )
                response.raise_for_status()
                data = response.json()
                
                # 直接使用結構化數據
                action_type = data.get("action", "echo")
                response_text = data.get("response", "")
                params = data.get("params", {})
                
                return {
                    "action": action_type,
                    "params": params,
                    "description": response_text,
                    "requires_confirmation": False
                }
                
            except requests.exceptions.RequestException as e:
                print(f"[CloudRuntime] 嘗試 {attempt+1} 失敗: {e}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                else:
                    return {
                        "action": "echo",
                        "params": {"message": f"❌ 經過 {max_retries} 次嘗試後仍無法連接到伺服器。"},
                        "description": "連線失敗",
                        "requires_confirmation": False
                    }
    
    def execute_action(
        self, 
        action: Dict[str, Any], 
        cookies: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        在本地執行指令
        """
        from core.actions import execute_action
        
        action_type = action.get("action")
        params = action.get("params", {})
        
        print(f"[CloudRuntime] 在本地執行雲端指令: {action_type}")
        return execute_action(action_type, params, cookies)
