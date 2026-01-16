"""
LLM Handler - 處理所有與 LLM 相關的邏輯

這個模組負責：
1. 與 LLM（Gemini）進行通訊
2. 管理 MCP 工具連接
3. 解析 LLM 回應並生成指令
"""

import os
from typing import Dict, Any, Optional
from core.models.response import ChatResponse


class LLMHandler:
    """LLM 處理器"""
    
    def __init__(self, model: str = "gemini:gemini-2.5-flash"):
        """
        初始化 LLM Handler
        
        Args:
            model: LLM 模型名稱
        """
        self.model = model
        self.temperature = 0.01
        self.max_input_tokens = 50000
        self.max_output_tokens = 50000
    
    def process_message(
        self, 
        message: str, 
        cookies: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        處理用戶訊息
        
        Args:
            message: 用戶輸入的訊息
            cookies: 用戶的認證 Cookie（可選）
        
        Returns:
            包含 action 和 params 的字典
        """
        # 延遲導入 akasha（避免測試時失敗）
        import akasha
        
        # 導入 prompt 建立函數
        from app.llm_prompt import prompt_create
        
        # 建立 prompt
        user_prompt = prompt_create(user_message=message)
        
        # 取得 MCP 工具連接資訊
        connection_info = self._get_mcp_connection_info()
        
        # 建立 agent
        agent = akasha.agents(
            model=self.model,
            temperature=self.temperature,
            verbose=False,
            max_input_tokens=self.max_input_tokens,
            max_output_tokens=self.max_output_tokens
        )
        
        # 調用 LLM（同步方法）
        response = agent.mcp_agent(connection_info, user_prompt)
        
        # 解析回應並生成指令
        action = self._parse_response(response, message)
        
        return action
    
    def _get_mcp_connection_info(self) -> Dict[str, Any]:
        """
        取得 MCP 工具連接資訊
        
        Returns:
            MCP 工具連接資訊字典
        """
        import sys
        
        # 使用絕對路徑
        # __file__ = .../P2025_PAX/core/llm/handler.py
        # 需要往上三層到達專案根目錄
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        tools_dir = os.path.join(base_dir, "tools")
        travel_helper_dir = os.path.join(tools_dir, "travel_helper")
        llm_uploader_path = os.path.join(tools_dir, "llm_uploader.py")
        
        # 使用當前 Python 解釋器（虛擬環境中的 Python）
        python_exe = sys.executable
        
        return {
            # 暫時註解掉 submit_work_times，因為它可能需要特殊的環境設定
            # "submit_work_times": {
            #     "command": python_exe,
            #     "args": ["-X", "utf8", llm_uploader_path],
            #     "transport": "stdio",
            # },
            # 暫時註解掉 google-map，因為服務還沒啟動
            # "google-map": {
            #     "url": "http://localhost:3000/mcp",
            #     "transport": "streamable_http",
            # },
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
    
    def _parse_response(self, llm_response: str, original_message: str) -> Dict[str, Any]:
        """
        解析 LLM 回應並生成指令
        
        Args:
            llm_response: LLM 的回應
            original_message: 原始用戶訊息
        
        Returns:
            包含 action 和 params 的字典
        """
        # TODO: 實作更智能的回應解析
        # 目前先返回簡單的 echo 指令
        
        # 如果回應包含工時相關資訊，生成 submit_work_time 指令
        if "work_times" in llm_response.lower() or "工時" in original_message:
            return {
                "action": "submit_work_time",
                "params": {
                    "response": llm_response
                },
                "description": "LLM 已處理您的工時請求",
                "requires_confirmation": False
            }
        
        # 如果回應包含出差相關資訊，生成 apply_travel 指令
        if "InWorkRoute" in llm_response or "出差" in original_message:
            return {
                "action": "apply_travel",
                "params": {
                    "response": llm_response
                },
                "description": "LLM 已處理您的出差申請",
                "requires_confirmation": False
            }
        
        # 預設返回 echo 指令
        return {
            "action": "echo",
            "params": {
                "message": llm_response
            },
            "description": "LLM 回應",
            "requires_confirmation": False
        }
