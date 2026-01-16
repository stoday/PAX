# -*- coding: utf-8 -*-
"""
Pax Backend Server - 雲端模式後端伺服器

提供 API 讓 Client 端調用 LLM 處理邏輯。
"""

import sys
import os
from typing import Dict, Any, Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

# 確保可以導入 core 模組
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from core.llm.handler import LLMHandler

app = FastAPI(title="Pax Backend API", version="1.0.0")
llm_handler = LLMHandler()

class ChatRequest(BaseModel):
    message: str
    cookies: Optional[Dict[str, Any]] = None

@app.get("/")
async def root():
    return {"status": "ok", "message": "Pax Backend API is running"}

@app.post("/api/chat")
async def chat(request: ChatRequest):
    """
    處理客戶端的對話請求
    """
    try:
        print(f"[Server] 收到請求: {request.message[:50]}...")
        
        # 調用 LLM Handler 處理訊息
        action = llm_handler.process_message(request.message, request.cookies)
        
        return action
        
    except Exception as e:
        print(f"[Server] 錯誤: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
