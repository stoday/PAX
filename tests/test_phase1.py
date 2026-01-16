# -*- coding: utf-8 -*-
"""
Phase 1 測試腳本 (pytest 格式)
測試本地模式（LocalRuntime）是否正常運作
"""

import sys
import os
import io
import pytest

# 確保可以導入模組（從 tests 目錄往上一層到專案根目錄）
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

@pytest.fixture
def local_runtime():
    from runtime.local import LocalRuntime
    return LocalRuntime()

def test_local_runtime_import():
    """測試 LocalRuntime 是否可以導入"""
    from runtime.local import LocalRuntime
    assert LocalRuntime is not None

def test_local_runtime_init(local_runtime):
    """測試 LocalRuntime 初始化"""
    assert local_runtime.llm_handler is not None
    assert hasattr(local_runtime, 'process_message')

def test_local_runtime_execute_action(local_runtime):
    """測試 LocalRuntime 執行指令"""
    # 測試 echo 指令
    action = {
        "action": "echo",
        "params": {"message": "測試訊息"}
    }
    
    result = local_runtime.execute_action(action)
    
    assert result['status'] == "success"
    assert result['message'] == "測試訊息"

@pytest.mark.slow
def test_local_runtime_process_message(local_runtime):
    """測試 LocalRuntime 處理訊息 (會調用 LLM)"""
    # 測試簡單訊息
    message = "請使用 fare_estimator 工具查詢台北到新竹的高鐵票價"
    result = local_runtime.process_message(message)
    
    assert result is not None
    assert "action" in result
    # 重點是是否有成功執行並返回動作，具體動作名稱取決於 LLM 解析
    assert result.get('action') in ["echo", "apply_travel"] # LLM 回應通常被解析為這兩種
