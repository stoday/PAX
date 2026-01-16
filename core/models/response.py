"""
回應資料模型

定義後端返回給前端的回應格式
"""

from typing import Dict, Any, Optional
from pydantic import BaseModel, Field


class ChatResponse(BaseModel):
    """聊天回應（包含要執行的指令）"""
    action: str = Field(..., description="指令類型")
    params: Dict[str, Any] = Field(..., description="指令參數")
    description: str = Field(..., description="描述（顯示給用戶）")
    requires_confirmation: bool = Field(False, description="是否需要用戶確認")
    
    class Config:
        json_schema_extra = {
            "example": {
                "action": "submit_work_time",
                "params": {
                    "date": "2026-01-16",
                    "start_time": "09:00",
                    "end_time": "18:00",
                    "reason": "忘刷"
                },
                "description": "將為您填寫 2026-01-16 的工時（09:00-18:00）",
                "requires_confirmation": True
            }
        }


class CallbackResponse(BaseModel):
    """回調回應"""
    response: str = Field(..., description="回應訊息")
    
    class Config:
        json_schema_extra = {
            "example": {
                "response": "好的，已成功為您填寫工時"
            }
        }


class ActionResult(BaseModel):
    """指令執行結果"""
    status: str = Field(..., description="執行狀態（success/error）")
    message: str = Field(..., description="結果訊息")
    details: Optional[Dict[str, Any]] = Field(None, description="詳細資訊")
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "success",
                "message": "工時提交成功",
                "details": {}
            }
        }
