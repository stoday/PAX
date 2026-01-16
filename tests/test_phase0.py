# -*- coding: utf-8 -*-
"""
Phase 0 測試腳本 (pytest 格式)
測試重構後的核心邏輯是否正常運作
"""

import sys
import os
import io
import pytest

# 確保可以導入 core 模組
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_imports():
    """測試所有模組是否可以正常導入"""
    # 測試 RuntimeAdapter
    from core import RuntimeAdapter
    assert RuntimeAdapter is not None
    
    # 測試 LLMHandler
    from core import LLMHandler
    assert LLMHandler is not None
    
    # 測試資料模型
    from core import (
        ChatRequest,
        ChatResponse,
        CallbackRequest,
        CallbackResponse,
        ActionResult,
    )
    assert ChatRequest is not None
    assert ChatResponse is not None
    assert ActionResult is not None

def test_data_models():
    """測試資料模型是否正常運作"""
    from core.models import ChatRequest, ChatResponse
    
    # 測試 ChatRequest
    request = ChatRequest(
        message="幫我填今天的工時",
        cookies={"test": "cookie"}
    )
    assert request.message == "幫我填今天的工時"
    
    # 測試 ChatResponse
    response = ChatResponse(
        action="submit_work_time",
        params={"date": "2026-01-16"},
        description="測試回應",
        requires_confirmation=True
    )
    assert response.action == "submit_work_time"
    assert response.requires_confirmation is True

def test_llm_handler_init():
    """測試 LLMHandler 是否可以初始化"""
    from core.llm import LLMHandler
    
    # 測試初始化
    handler = LLMHandler()
    assert handler.model is not None
    assert handler.temperature == 0.01
    
    # 測試 MCP 連接資訊取得成功
    connection_info = handler._get_mcp_connection_info()
    assert isinstance(connection_info, dict)
    assert len(connection_info) > 0
