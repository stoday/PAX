# -*- coding: utf-8 -*-
"""
Phase 3 整合測試
驗證 Actions 統一入口、本地與雲端模式的 Actions 調用
"""

import sys
import os
import pytest

# 確保可以導入模組
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.actions import execute_action
from runtime.local.executor import LocalRuntime
from runtime.cloud.client.executor import CloudRuntime

def test_actions_unified_entry():
    """測試 Actions 統一入口"""
    # 測試 echo
    result = execute_action("echo", {"message": "Hello Test"})
    assert result["status"] == "success"
    assert result["message"] == "Hello Test"
    
    # 測試未知 Action
    result = execute_action("unknown_action", {})
    assert result["status"] == "error"
    assert "未定義的 Action" in result["message"]

def test_local_runtime_action_integration():
    """測試 LocalRuntime 是否正確調用 Actions"""
    runtime = LocalRuntime()
    action = {"action": "echo", "params": {"message": "Local Echo"}}
    
    result = runtime.execute_action(action)
    assert result["status"] == "success"
    assert "Local Echo" in result["message"]

def test_cloud_runtime_action_locally():
    """測試 CloudRuntime 是否在本地執行指令 (使用 Mock 模擬網路)"""
    from unittest.mock import patch, MagicMock
    
    # 模擬 requests.Session.get 成功返回包含隱藏欄位的頁面
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = '<html><input name="__VIEWSTATE" value="vs"><input name="__VIEWSTATEGENERATOR" value="gen"><input name="__EVENTVALIDATION" value="val"></html>'
    mock_response.raise_for_status = MagicMock()
    
    with patch("requests.Session.get", return_value=mock_response):
        runtime = CloudRuntime(server_url="http://localhost:9999") 
        action = {"action": "submit_work_time", "params": {}}
        
        result = runtime.execute_action(action)
        assert result["status"] == "success", f"Action failed: {result.get('message')}"
        assert "工時已提交" in result["message"]
