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
        
        # 建立 agent
        agent = akasha.agents(
            model=self.model,
            temperature=self.temperature,
            verbose=False,
            max_input_tokens=self.max_input_tokens,
            max_output_tokens=self.max_output_tokens
        )
        
        # 建立 prompt
        user_prompt = prompt_create(user_message=message)
        print(f"\n[Debug] --- LLM Prompt Start ---\n{user_prompt}\n[Debug] --- LLM Prompt End ---\n")
        
        # 取得 MCP 工具連接資訊
        connection_info = self._get_mcp_connection_info()
        print(f"[Debug] MCP Tools to akasha: {list(connection_info.keys())}")
        
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
        
        # 根據運行模式決定 MCP 工具
        # 雲端模式下，移除實體「打卡」連線，改由 LLM 回傳指令給 Client 執行
        pax_mode = os.getenv("PAX_MODE", "local").lower()
        
        mcp_tools = {
            "fare_estimator": {
                "command": python_exe,
                "args": [os.path.join(travel_helper_dir, "fare_estimator.py")],
                "transport": "stdio",
            },
            "dc_apply": {
                "command": python_exe,
                "args": [os.path.join(travel_helper_dir, "apply.py")],
                "transport": "stdio",
            },
             "google-map": {
                "url": f"http://localhost:{os.getenv('MCP_SERVER_PORT', '3000')}/mcp",
                "transport": "streamable_http",
            }
        }
        
        # 只有在本地模式才加入實體打卡工具
        if pax_mode == "local":
            mcp_tools["submit_work_times"] = {
                "command": python_exe,
                "args": ["-X", "utf8", llm_uploader_path],
                "transport": "stdio",
            }
            
        return mcp_tools

    def _parse_response(self, llm_response: str, original_message: str) -> Dict[str, Any]:
        """
        將 LLM 的回應解析為結構化指令
        """
        import json
        import re

        # 嘗試從回應中提取並解析 JSON (支援純 JSON 或帶有 Markdown 的 JSON)
        try:
            # 尋找 JSON 區塊
            json_match = re.search(r"({.*})", llm_response, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group(1))
                # 如果符合我們要求的新結構，直接回傳
                if "action" in data and ("response" in data or "description" in data):
                    return {
                        "action": data["action"],
                        "params": data.get("params", {}),
                        "description": data.get("response") or data.get("description", ""),
                        "requires_confirmation": data.get("requires_confirmation", False)
                    }
        except Exception:
            pass # 如果解析失敗，進入傳統關鍵字判定邏輯

        # 傳統關鍵字判定與 fallback (兼容舊版或解析失敗)
        if "submit_work_times" in llm_response.lower() or "work_times" in llm_response.lower() or "工時" in original_message:
            return {
                "action": "submit_work_time",
                "params": {"response": llm_response},
                "description": "已為您準備好工時處理指令",
                "requires_confirmation": False
            }
        
        if "apply_travel" in llm_response or "InWorkRoute" in llm_response or "出差" in original_message:
            return {
                "action": "apply_travel",
                "params": {"response": llm_response},
                "description": "已為您準備好出差申請指令",
                "requires_confirmation": False
            }
        
        return {
            "action": "echo",
            "params": {"message": llm_response},
            "description": llm_response,
            "requires_confirmation": False
        }
