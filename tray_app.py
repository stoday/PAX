import pystray
from PIL import Image, ImageDraw
import threading
import sys
import os
import time
import traceback
import socket

# === 自動載入 requirements.txt 中的套件 ===
# 這確保 PyInstaller 會將所有依賴打包進 .exe
def _load_requirements():
    """讀取 requirements.txt 並嘗試 import 所有套件"""
    req_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'requirements.txt')
    if os.path.exists(req_file):
        with open(req_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                # 跳過空行和註解
                if not line or line.startswith('#'):
                    continue
                # 移除版本號 (例如 requests==2.28.0 -> requests)
                package = line.split('==')[0].split('>=')[0].split('<=')[0].split('~=')[0].strip()
                # 處理特殊情況 (例如 package[extra])
                package = package.split('[')[0]
                try:
                    __import__(package)
                except ImportError:
                    # 開發時可能還沒安裝，打包時會報錯
                    pass

# 執行自動載入
_load_requirements()
# ==========================================

# --- 配置區 ---
LOCK_PORT = 49152  # 使用動態/私有埠號範圍 (49152-65535)，避免與系統服務衝突
# --------------

def debug_log(msg):
    """紀錄執行過程中的錯誤，方便追蹤"""
    try:
        log_dir = get_app_dir()
        with open(os.path.join(log_dir, "debug_tray.log"), "a", encoding="utf-8") as f:
            f.write(f"[{time.ctime()}] {msg}\n")
    except:
        pass

def get_app_dir():
    """取得應用程式目錄（打包後會是 .exe 的位置）"""
    if getattr(sys, 'frozen', False):
        # 打包後的環境
        return os.path.dirname(sys.executable)
    else:
        # 開發環境
        return os.path.dirname(os.path.abspath(__file__))

# ============================================
# 作業邏輯
# ============================================
def main_logic():
    """
    這是你的主要業務邏輯函數
    它會在背景執行緒中運行
    
    範例：每 10 秒寫入一次 log
    你可以替換成任何你想要的邏輯
    """
    log_path = os.path.join(get_app_dir(), 'log.txt')
    
    # 寫入啟動資訊
    with open(log_path, 'a', encoding='utf-8') as f:
        f.write(f'\n=== 腳本啟動於 {time.ctime()} ===\n')
        f.write(f'Log 檔位置: {log_path}\n')
        f.write(f'應用程式目錄: {get_app_dir()}\n')
        f.write('=' * 60 + '\n\n')
    
    # 主迴圈
    while True:
        try:
            with open(log_path, 'a', encoding='utf-8') as f:
                f.write(f'Running... {time.ctime()}\n')
            time.sleep(10)
        except Exception as e:
            debug_log(f"業務邏輯錯誤: {e}")
            time.sleep(10)  # 發生錯誤時也要等待，避免瘋狂重試

# ============================================
# 系統匣 UI 邏輯（通常不需要修改）
# ============================================
class TrayRunner:
    def __init__(self):
        self.running = False
        self.icon = None
        self.worker_thread = None

    def create_image(self, running=False):
        """建立狀態圖示：綠色代表運行中，紅色代表停止"""
        width, height = 64, 64
        image = Image.new('RGB', (width, height), (40, 40, 40))
        dc = ImageDraw.Draw(image)
        color = (0, 255, 0) if running else (255, 0, 0)
        dc.ellipse([16, 16, 48, 48], fill=color)
        return image

    def run_logic(self):
        """啟動業務邏輯"""
        if self.running:
            debug_log("邏輯已在運行中，跳過")
            return
        
        try:
            debug_log("準備啟動業務邏輯執行緒")
            self.worker_thread = threading.Thread(target=main_logic, daemon=True)
            self.worker_thread.start()
            self.running = True
            debug_log("業務邏輯執行緒已啟動")
            
            if self.icon:
                self.icon.icon = self.create_image(running=True)
                self.icon.title = "Pax運行中"
        except Exception as e:
            debug_log(f"啟動業務邏輯失敗: {e}\n{traceback.format_exc()}")

    def stop_logic(self):
        """停止業務邏輯（注意：Python 執行緒無法強制停止）"""
        if self.running:
            debug_log("注意: Python 執行緒無法強制停止，只能等待自然結束")
            self.running = False
            if self.icon:
                self.icon.icon = self.create_image(running=False)
                self.icon.title = "Pax已標記為停止"

    def on_quit(self, icon, item):
        """結束常駐程式"""
        debug_log("正在結束程式...")
        self.stop_logic()
        icon.stop()
        os._exit(0)

    def setup_tray(self):
        """建立系統匣選單與圖示"""
        try:
            debug_log("正在建立系統匣圖示...")
            self.icon = pystray.Icon(
                "PaxRunner", 
                self.create_image(running=False), 
                "Pax Runner 啟動中...",
                menu=pystray.Menu(
                    pystray.MenuItem("執行邏輯", lambda: self.run_logic()),
                    pystray.MenuItem("停止執行", lambda: self.stop_logic()),
                    pystray.MenuItem("結束常駐", self.on_quit)
                )
            )
            
            # 自動啟動業務邏輯
            threading.Thread(target=lambda: (time.sleep(1), self.run_logic()), daemon=True).start()
            
            debug_log("進入 icon.run() 主迴圈")
            self.icon.run()
        except Exception as e:
            debug_log(f"系統匣執行失敗: {e}\n{traceback.format_exc()}")

if __name__ == "__main__":
    # 記錄啟動時間（追加模式，保留歷史記錄）
    try:
        log_dir = get_app_dir()
        with open(os.path.join(log_dir, "debug_tray.log"), "a", encoding="utf-8") as f:
            f.write(f"\n=== 程式啟動於 {time.ctime()} ===\n")
    except:
        pass
    
    debug_log("步驟 1: 開始執行主程式")
    
    # --- 單一實例鎖 (Socket Lock) ---
    debug_log(f"步驟 2: 嘗試綁定埠號 {LOCK_PORT}")
    try:
        _lock_holder = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        _lock_holder.bind(('127.0.0.1', LOCK_PORT))
        debug_log(f"步驟 3: 成功綁定埠號 {LOCK_PORT}，確認為唯一實例")
    except socket.error as e:
        debug_log(f"步驟 3 失敗: 埠號 {LOCK_PORT} 已被佔用或無法綁定: {e}")
        debug_log("程式即將退出（偵測到重複實例）")
        sys.exit(0)
    
    debug_log("步驟 4: 初始化 TrayRunner")
    try:
        runner = TrayRunner()
        debug_log("步驟 5: 啟動系統匣")
        runner.setup_tray()
    except Exception as e:
        debug_log(f"步驟 5 失敗: 主程序異常: {e}\n{traceback.format_exc()}")
