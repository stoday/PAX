"""
請求資料模型

定義前端發送到後端的請求格式
"""

from typing import Dict, Any, Optional
from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """聊天請求"""
    message: str = Field(..., description="用戶輸入的訊息")
    cookies: Optional[Dict[str, Any]] = Field(None, description="用戶的認證 Cookie")
    
    class Config:
        json_schema_extra = {
            "example": {
                "message": "幫我填今天的工時，上班 9 點，下班 6 點",
                "cookies": {
                    "ASP_NET_SESSION_ID": "...",
                    "CLIENT_TICKET": "..."
                }
            }
        }


class CallbackRequest(BaseModel):
    """回調請求（前端執行完指令後回報結果）"""
    action_id: str = Field(..., description="指令 ID")
    status: str = Field(..., description="執行狀態（success/error）")
    message: str = Field(..., description="執行結果訊息")
    details: Optional[Dict[str, Any]] = Field(None, description="詳細資訊")
    
    class Config:
        json_schema_extra = {
            "example": {
                "action_id": "abc123",
                "status": "success",
                "message": "工時提交成功",
                "details": {}
            }
        }
