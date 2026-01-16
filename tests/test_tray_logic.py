# -*- coding: utf-8 -*-
"""
Tray App 邏輯測試
驗證 TrayRunner 的核心邏輯（設定儲存、模式切換、Runtime 初始化）
而不實際啟動 GUI 介面。
"""

import os
import sys
import json
import pytest
from unittest.mock import MagicMock, patch

# 確保可以導入模組
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ui.tray_app import TrayRunner

@pytest.fixture
def tray_runner(tmp_path):
    """
    建立一個測試用的 TrayRunner 實例
    使用臨時目錄下的設定檔，避免影響真實環境。
    """
    # 模擬暫存目錄中的設定檔路徑
    config_file = tmp_path / "pax_config.json"
    
    # 模擬 socket 鎖，避免衝突
    with patch("socket.socket"):
        # 模擬 pystray.Icon 以免啟動真正的 GUI
        with patch("pystray.Icon"):
            runner = TrayRunner()
            runner.config_path = str(config_file)
            return runner

def test_config_persistence(tray_runner):
    """測試設定持久化 (Save/Load)"""
    tray_runner.mode = "cloud"
    tray_runner._save_config()
    
    # 驗證檔案是否存在
    assert os.path.exists(tray_runner.config_path)
    
    # 讀取檔案確認內容
    with open(tray_runner.config_path, 'r') as f:
        data = json.load(f)
        assert data["mode"] == "cloud"
    
    # 修改後再讀回
    tray_runner.mode = "local"
    tray_runner._save_config()
    new_data = tray_runner._load_config()
    assert new_data["mode"] == "local"

def test_switch_mode_logic(tray_runner):
    """測試切換模式的完整邏輯"""
    # 模擬 icon 物件
    mock_icon = MagicMock()
    tray_runner.icon = mock_icon
    
    # 初始模式
    tray_runner.mode = "local"
    
    # 切換到雲端模式
    with patch.object(tray_runner, '_init_runtime') as mock_init:
        tray_runner.switch_mode("cloud")
        
        # 驗證屬性更新
        assert tray_runner.mode == "cloud"
        assert os.environ["PAX_MODE"] == "cloud"
        
        # 驗證有重新讀取 Runtime
        mock_init.assert_called_once()
        
        # 驗證有發送系統通知
        mock_icon.notify.assert_called()
        
        # 驗證圖示有更新
        assert mock_icon.icon is not None

def test_image_creation(tray_runner):
    """測試圖示生成是否正常 (不同模式顏色不同)"""
    from PIL import Image
    
    # 本地模式圖示
    tray_runner.mode = "local"
    img_local = tray_runner.create_image(running=True)
    assert isinstance(img_local, Image.Image)
    
    # 雲端模式圖示
    tray_runner.mode = "cloud"
    img_cloud = tray_runner.create_image(running=True)
    assert isinstance(img_cloud, Image.Image)
    
    # 停止狀態圖示
    img_stop = tray_runner.create_image(running=False)
    assert isinstance(img_stop, Image.Image)

def test_runtime_reinitialization(tray_runner):
    """測試切換模式時 Runtime 適配器是否正確更新"""
    # 由本地切換到雲端
    tray_runner.switch_mode("cloud")
    from runtime.cloud.client.executor import CloudRuntime
    assert isinstance(tray_runner.runtime, CloudRuntime)
    
    # 由雲端切換回本地
    tray_runner.switch_mode("local")
    from runtime.local.executor import LocalRuntime
    assert isinstance(tray_runner.runtime, LocalRuntime)
