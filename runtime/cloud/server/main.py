# -*- coding: utf-8 -*-
"""
Pax Backend Server - 雲端模式後端伺服器

提供 API 讓 Client 端調用 LLM 處理邏輯。
"""

import sys
import os
from typing import Dict, Any, Optional
from fastapi import FastAPI, HTTPException, Request, Depends, Header
from fastapi.security import APIKeyHeader
from pydantic import BaseModel

# 確保可以導入 core 模組
# 結構: root/runtime/cloud/server/main.py -> 需要往上四層到達 root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from core.llm.handler import LLMHandler

app = FastAPI(title="Pax Backend API", version="1.0.0")
llm_handler = LLMHandler()

# 安全認證設定
API_KEY_NAME = "X-API-KEY"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

async def verify_api_key(api_key: str = Depends(api_key_header)):
    """驗證 API Key"""
    expected_key = os.getenv("PAX_CLOUD_API_KEY")
    if not expected_key:
        # 如果伺服器沒設定 Key，預設允許連線 (僅供開發測試)
        return
    if api_key != expected_key:
        raise HTTPException(
            status_code=403,
            detail="Could not validate credentials"
        )

class ChatRequest(BaseModel):
    message: str
    cookies: Optional[Dict[str, Any]] = None

@app.get("/")
async def root():
    return {"status": "ok", "message": "Pax Backend API is running"}

@app.post("/api/chat")
async def chat(request: ChatRequest, _ = Depends(verify_api_key)):
    """
    處理客戶端的對話請求 (Minimalist JSON)
    """
    try:
        print(f"[Server] 收到請求: {request.message[:50]}...")
        
        # 調用 LLM Handler 處理訊息
        # 由於 prompt 已修改為要求 JSON，LLMHandler._parse_response 將嘗試解析它
        action_dict = llm_handler.process_message(request.message, request.cookies)
        
        # 直接回傳結構化 JSON 給 Client
        return {
            "response": action_dict.get("description") or action_dict.get("params", {}).get("message", "已處理您的請求"),
            "action": action_dict.get("action", "echo"),
            "params": action_dict.get("params", {})
        }
        
    except Exception as e:
        print(f"[Server] 錯誤: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
