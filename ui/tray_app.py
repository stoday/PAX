# -*- coding: utf-8 -*-
"""
Pax Tray App - 系統匣常駐程式
支援本地與雲端模式切換
"""

import pystray
from PIL import Image, ImageDraw
import threading
import sys
import os
import time
import traceback
import socket
import subprocess
import dotenv

# 確保可以導入 core 和 runtime 模組
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 載入環境變數
dotenv.load_dotenv()

class TrayRunner:
    def __init__(self):
        self.running = False
        self.icon = None
        self.worker_thread = None
        self.lock_port = 49152
        
        # 取得專案根目錄
        self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        # 載入持久化設定
        self.config_path = os.path.join(self.base_dir, "pax_config.json")
        self.mode = self._load_config().get("mode", os.getenv("PAX_MODE", "local")).lower()
        os.environ["PAX_MODE"] = self.mode
        
        print(f"[TrayApp] 初始化中，目前模式: {self.mode.upper()}")
        self.debug_log(f"程式啟動，初始模式: {self.mode}")
        
        self.runtime = self._init_runtime()

    def _load_config(self):
        import json
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r') as f:
                    return json.load(f)
            except: pass
        return {}

    def _save_config(self):
        import json
        try:
            with open(self.config_path, 'w') as f:
                json.dump({"mode": self.mode}, f)
        except: pass

    def debug_log(self, msg):
        """紀錄執行過程中的日誌"""
        try:
            log_path = os.path.join(self.base_dir, "debug_tray.log")
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(f"[{time.ctime()}] [{self.mode.upper()}] {msg}\n")
        except Exception as e:
            print(f"無法寫入日誌: {e}")

    def _init_runtime(self):
        """根據目前模式初始化 Runtime"""
        from app.main import get_runtime
        try:
            return get_runtime()
        except Exception as e:
            self.debug_log(f"初始化 Runtime 失敗 ({self.mode}): {e}")
            print(f"[TrayApp] 初始化 Runtime 失敗: {e}")
            return None

    def create_image(self, running=False):
        """建立狀態圖示"""
        width, height = 64, 64
        image = Image.new('RGB', (width, height), (40, 40, 40))
        dc = ImageDraw.Draw(image)
        if not running:
            color = (255, 0, 0) # 紅色代表停止
        elif self.mode == "cloud":
            color = (0, 255, 255) # 青色代表雲端
        else:
            color = (0, 255, 0) # 綠色代表本地
            
        dc.ellipse([16, 16, 48, 48], fill=color)
        return image

    def switch_mode(self, new_mode):
        """切換運行模式"""
        if self.mode == new_mode:
            return
            
        old_mode = self.mode
        self.mode = new_mode
        os.environ["PAX_MODE"] = new_mode
        self.runtime = self._init_runtime()
        self._save_config()
        
        if self.icon:
            self.icon.icon = self.create_image(running=self.running)
            self.icon.title = f"Pax ({self.mode.upper()}) - {'運行中' if self.running else '已停止'}"
            try:
                self.icon.notify(
                    f"已從 {old_mode.upper()} 切換至 {new_mode.upper()} 模式",
                    title="Pax 模式切換"
                )
            except: pass
            
        self.debug_log(f"已切換至 {new_mode} 模式")
        print(f"[TrayApp] 已切換連至 {new_mode.upper()} 模式")

    def open_pax_console(self):
        """開啟 Pax 互動式 Console"""
        try:
            print("[TrayApp] 正在啟動 Pax Console...")
            subprocess.Popen(
                [sys.executable, '-m', 'app.main'],
                creationflags=subprocess.CREATE_NEW_CONSOLE,
                cwd=self.base_dir,
                env=os.environ.copy()
            )
        except Exception as e:
            self.debug_log(f"啟動 Pax Console 失敗: {e}")

    def on_quit(self, icon, item):
        self.running = False
        icon.stop()
        os._exit(0)

    def setup_tray(self):
        """建立系統匣選單與圖示"""
        try:
            print("[TrayApp] 正在建立系統匣功能面板...")
            menu = pystray.Menu(
                pystray.MenuItem("打開 Pax Console", self.open_pax_console),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem("運行模式", pystray.Menu(
                    pystray.MenuItem("本地模式 (Local)", 
                                     lambda: self.switch_mode("local"),
                                     checked=lambda item: self.mode == "local"),
                    pystray.MenuItem("雲端模式 (Cloud)", 
                                     lambda: self.switch_mode("cloud"),
                                     checked=lambda item: self.mode == "cloud")
                )),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem("結束常駐", self.on_quit)
            )
            
            self.icon = pystray.Icon(
                "PaxRunner", 
                self.create_image(running=True), 
                f"Pax ({self.mode.upper()})",
                menu=menu
            )
            
            self.running = True
            print(f"[TrayApp] 成功進入主迴圈，請檢查系統匣圖示。")
            self.icon.run()
        except Exception as e:
            print(f"[TrayApp] 系統匣執行失敗: {e}")
            self.debug_log(f"系統匣執行失敗: {e}\n{traceback.format_exc()}")

if __name__ == "__main__":
    # 單一實例鎖 (Socket Lock)
    try:
        _lock_holder = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        _lock_holder.bind(('127.0.0.1', 49152))
    except socket.error:
        print("[TrayApp] 警告：偵測到重複執行，Pax 可能已經在運行中（請檢查系統匣）。")
        sys.exit(0)
    
    runner = TrayRunner()
    runner.setup_tray()
