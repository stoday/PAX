# -*- coding: utf-8 -*-
"""
Phase 2 測試腳本 (pytest 格式)
測試雲端模式（CloudRuntime）與後端伺服器的整合
"""

import sys
import os
import time
import threading
import pytest
import requests
import uvicorn

# 確保可以導入模組
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from runtime.cloud.client.executor import CloudRuntime
from runtime.cloud.server.main import app

# 測試用的伺服器配置
HOST = "127.0.0.1"
PORT = 8081  # 使用不同的埠號避免衝突

def run_server():
    """啟動測試伺服器"""
    uvicorn.run(app, host=HOST, port=PORT, log_level="error")

@pytest.fixture(scope="module", autouse=True)
def server():
    """啟動與停止測試伺服器的 fixture"""
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()
    
    # 等待伺服器啟動
    time.sleep(2)
    yield
    # 執行緒會隨進程結束而終止 (daemon=True)

@pytest.fixture
def cloud_runtime():
    """建立 CloudRuntime 實例"""
    return CloudRuntime(server_url=f"http://{HOST}:{PORT}")

def test_server_health():
    """測試伺服器健康檢查"""
    response = requests.get(f"http://{HOST}:{PORT}/")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

@pytest.mark.slow
def test_cloud_runtime_process_message(cloud_runtime):
    """測試雲端模式處理訊息 (會調用後端 -> 後端調用 LLM)"""
    message = "請使用 fare_estimator 工具查詢台北到新竹的高鐵票價"
    
    print(f"\n[Test] 發送訊息到雲端適配器...")
    result = cloud_runtime.process_message(message)
    
    assert result is not None
    assert "action" in result
    # 驗證返回了合理的動作
    assert result.get('action') in ["echo", "apply_travel", "thsr_fare_estimator"]

def test_cloud_runtime_execute_action_locally(cloud_runtime):
    """測試雲端模式下的本地執行指令"""
    action = {
        "action": "submit_work_time",
        "params": {"date": "2026-01-16"}
    }
    
    result = cloud_runtime.execute_action(action)
    
    assert result['status'] == "success"
    assert "雲端模式 - 本地執行" in result['message']
    assert result['details']['date'] == "2026-01-16"
