# -*- coding: utf-8 -*-
"""
測試 LLMHandler 的 MCP 連接 (pytest 格式)
"""

import sys
import os
import io
import pytest

# 確保可以導入模組
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

@pytest.fixture
def handler():
    from core.llm.handler import LLMHandler
    return LLMHandler()

def test_llm_handler_init(handler):
    """測試 LLMHandler 初始化成功"""
    assert handler.model is not None
    assert handler.temperature == 0.01

def test_mcp_connection_info(handler):
    """測試 MCP 連接資訊"""
    connection_info = handler._get_mcp_connection_info()
    assert len(connection_info) >= 2
    assert "fare_estimator" in connection_info
    assert "dc_apply" in connection_info
    
    # 驗證路徑是否存在
    fare_info = connection_info["fare_estimator"]
    assert os.path.exists(fare_info["args"][0])

@pytest.mark.slow
def test_llm_handler_process_message(handler):
    """測試 LLMHandler 處理訊息（需調用實際 LLM）"""
    message = "請使用 fare_estimator 工具查詢台北到新竹的高鐵票價"
    result = handler.process_message(message)
    
    assert result is not None
    assert "action" in result
    assert "description" in result
