"""
Runtime Adapter 介面定義

這個模組定義了 Pax 的執行環境適配器介面。
不同的運行模式（本地模式、雲端模式）都需要實作這個介面。
"""

from abc import ABC, abstractmethod
from typing import Dict, Any


class RuntimeAdapter(ABC):
    """
    執行環境適配器基礎類別
    
    這個抽象類別定義了 Pax 運行時需要的核心介面。
    所有的運行模式（本地、雲端）都必須實作這些方法。
    """
    
    @abstractmethod
    def process_message(self, message: str, cookies: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        處理用戶訊息
        
        Args:
            message: 用戶輸入的自然語言訊息
            cookies: 用戶的認證 Cookie（可選）
        
        Returns:
            包含 action 和 params 的字典：
            {
                "action": "submit_work_time",  # 指令類型
                "params": {...},               # 指令參數
                "description": "...",          # 描述（顯示給用戶）
                "requires_confirmation": bool  # 是否需要確認
            }
        """
        pass
    
    @abstractmethod
    def execute_action(self, action: Dict[str, Any], cookies: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        執行指令
        
        Args:
            action: 要執行的指令（包含 action 和 params）
            cookies: 用戶的認證 Cookie（可選）
        
        Returns:
            執行結果：
            {
                "status": "success" | "error",  # 執行狀態
                "message": "...",               # 結果訊息
                "details": {...}                # 詳細資訊（可選）
            }
        """
        pass
