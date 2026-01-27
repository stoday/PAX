# -*- coding: utf-8 -*-
"""
Pax Tray App - 系統匣常駐程式
支援本地與雲端模式切換
"""

import sys
import os

# 確保可以導入 core 和 runtime 模組
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pystray
from PIL import Image, ImageDraw
import threading
import time
import traceback
import socket
import subprocess
import dotenv
try:
    import tkinter as tk
    from tkinter import scrolledtext
    HAS_TKINTER = True
except ImportError:
    HAS_TKINTER = False

from core.logger import get_pax_logger

# 載入 TOML 設定
def get_app_version(base_dir):
    try:
        import tomllib as toml 
    except ImportError:
        import pip._vendor.tomli as toml
    
    config_path = os.path.join(base_dir, "config.toml")
    if os.path.exists(config_path):
        with open(config_path, "rb") as f:
            config = toml.load(f)
            return config.get("general", {}).get("version", "unk")
    return "0.0"

# 載入環境變數
dotenv.load_dotenv()

class TrayRunner:
    def __init__(self):
        self.running = False
        self.icon = None
        self.worker_thread = None
        self.lock_port = 49152
        
        if getattr(sys, 'frozen', False):
            # 打包後的環境：base_dir 是執行檔所在目錄
            self.base_dir = os.path.dirname(sys.executable)
        else:
            # 開發環境：base_dir 是專案根目錄
            self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        # 載入持久化設定
        self.config_path = os.path.join(self.base_dir, "pax_config.json")
        self.mode = self._load_config().get("mode", os.getenv("PAX_MODE", "local")).lower()
        os.environ["PAX_MODE"] = self.mode
        
        self.version = get_app_version(self.base_dir)
        
        print(f"[TrayApp] 初始化中，版本: {self.version}, 目前模式: {self.mode.upper()}")
        self.logger = get_pax_logger(self.base_dir)
        self.logger.log(f"--- Pax Tray App v{self.version} 啟動 ---")
        self.debug_log(f"程式啟動，版本: {self.version}, 初始模式: {self.mode}")
        
        self.runtime = self._init_runtime()
        
        # 啟動自動工時補打排程 (讀取 .env)
        try:
            from core.actions.auto_scheduler import start_scheduler_thread
            self.scheduler_thread = start_scheduler_thread(self.base_dir, self._notify)
            target_time = os.getenv("AUTO_FILL_TIME", "17:55")
            self.debug_log(f"自動工時排程線程已啟動 (目標: {target_time})")
            self.logger.log(f"自動工時排程監測已啟動 (每日 {target_time})")
        except Exception as e:
            self.debug_log(f"啟動排程線程失敗: {e}")
            self.logger.log(f"啟動排程線程失敗: {e}", level="ERROR")

        # 啟動開機自動認證檢查
        threading.Thread(target=self._validate_auth_on_startup, daemon=True).start()

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

    def _notify(self, title, message):
        """顯示系統通知"""
        try:
            if self.icon:
                self.icon.notify(message, title=title)
            else:
                print(f"[{title}] {message}")
        except Exception as e:
            self.debug_log(f"無法顯示通知: {e}")

    def _open_console(self):
        """開啟 Pax AI 控制台視窗"""
        try:
            if getattr(sys, 'frozen', False):
                # 打包模式：呼叫自己並帶上 --console 參數
                # 使用 CREATE_NEW_CONSOLE 旗標來彈出新的 CMD 視窗
                subprocess.Popen(
                    [sys.executable, "--console"],
                    creationflags=subprocess.CREATE_NEW_CONSOLE,
                    cwd=self.base_dir
                )
            else:
                # 開發模式
                main_py = os.path.join(self.base_dir, "app", "main.py")
                subprocess.Popen(
                    ["cmd.exe", "/c", "start", "python", main_py],
                    cwd=self.base_dir
                )
                
            self._notify("Pax Console", "控制台已啟動")
        except Exception as e:
            self.debug_log(f"無法啟動控制台: {e}")
            self._notify("錯誤", f"無法啟動控制台: {e}")

            return None

    def _init_runtime(self):
        """根據目前模式初始化 Runtime"""
        from app.main import get_runtime
        try:
            return get_runtime()
        except Exception as e:
            self.debug_log(f"初始化 Runtime 失敗 ({self.mode}): {e}")
            print(f"[TrayApp] 初始化 Runtime 失敗: {e}")
            return None

    def _validate_auth_on_startup(self):
        """開機時檢查認證狀態，若無效則自動開啟登入頁面"""
        self.debug_log("正在執行開機認證檢查...")
        from core.actions.utils import get_auth_cookies
        from core.actions.submit_work_time import BASE_TIMESHEET_URL
        import requests
        from bs4 import BeautifulSoup

        cookies = get_auth_cookies()
        
        # 1. 檢查是否有基本資料
        has_info = all([cookies.get('ASP.NET_SessionId'), cookies.get('clientTicket'), cookies.get('clientUserName')])
        
        should_reauth = False
        if not has_info:
            self.debug_log("偵測到尚未完成首次認證")
            should_reauth = True
        else:
            # 2. 實測一次連線
            try:
                headers = {"User-Agent": "Mozilla/5.0"}
                resp = requests.get(BASE_TIMESHEET_URL, cookies=cookies, headers=headers, timeout=10)
                if resp.status_code != 200 or "__VIEWSTATE" not in resp.text:
                    self.debug_log("偵測到現有認證已過期")
                    should_reauth = True
            except:
                self.debug_log("認證檢查連線異常，跳過自動登入")
                return

        if should_reauth:
            self.logger.log("偵測到需要認證，自動開啟登入視窗...")
            self._notify("Pax 認證提醒", "偵測到您尚未登入或認證已過期，正在為您開啟登入網頁...")
            try:
                from app.get_token import get_tokens_from_browser
                get_tokens_from_browser()
                self._notify("認證完成", "已成功獲取認證資料，Pax 現在已準備就緒！")
                self.logger.log("自動認證完成")
                # 認證成功後，啟動 Keep-Alive
                self._start_token_keeper()
            except Exception as e:
                self.debug_log(f"自動認證失敗: {e}")
        else:
            # 已有認證，直接啟動 Keep-Alive
            self._start_token_keeper()

    def _start_token_keeper(self):
        """啟動 Token 自動保鮮服務"""
        try:
            from core.token_keeper import keeper
            keeper.on_expired = self._on_token_expired
            keeper.start()
            self.debug_log("TokenKeeper 服務已啟動")
        except Exception as e:
            self.debug_log(f"啟動 TokenKeeper 失敗: {e}")

    def _on_token_expired(self):
        """當 TokenKeeper 回報 Token 失效時的回調"""
        self.logger.log("Token 已失效 (Keep-Alive 檢測)，發出通知")
        self._notify("Pax 認證已過期", "您的登入憑證已失效，請重新開啟 Pax Console 進行認證。")

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
        """開啟 Pax 互動式 Console修"""
        try:
            self.logger.log("使用者手動開啟 Pax Console")
            self.debug_log("嘗試啟動 Pax Console...")
            # 確保使用 python.exe 而不是 pythonw.exe，以便彈出主視窗
            python_exe = sys.executable
            self.debug_log(f"原始 sys.executable: {python_exe}")
            
            if python_exe.lower().endswith("pythonw.exe"):
                python_exe = python_exe.lower().replace("pythonw.exe", "python.exe")
            
            self.debug_log(f"目標 python_exe: {python_exe}")
            self.debug_log(f"工作目錄 base_dir: {self.base_dir}")

            # 檢查檔案是否存在
            main_py = os.path.join(self.base_dir, "app", "main.py")
            if not os.path.exists(main_py):
                self.debug_log(f"錯誤: 找不到 {main_py}")
                return

            # 檢查檔案是否存在
            main_py = os.path.join(self.base_dir, "app", "main.py")
            if not os.path.exists(main_py):
                self.debug_log(f"錯誤: 找不到 {main_py}")
                return

            # 強制將專案根目錄加入 PYTHONPATH (作為備援)
            env = os.environ.copy()
            env["PYTHONPATH"] = self.base_dir + os.pathsep + env.get("PYTHONPATH", "")
            # 確保輸出編碼正確
            env["PYTHONIOENCODING"] = "utf-8"

            self.debug_log(f"準備啟動: {python_exe} {main_py}")

            # 正式版啟動：直接啟動控制台
            proc = subprocess.Popen(
                [python_exe, main_py],
                creationflags=subprocess.CREATE_NEW_CONSOLE,
                cwd=self.base_dir,
                env=env
            )
            self.debug_log(f"Popen 已執行，PID: {proc.pid}")
            
        except Exception as e:
            self.debug_log(f"啟動 Pax Console 失敗: {str(e)}\n{traceback.format_exc()}")

    def on_quit(self, icon, item):
        self.logger.log("--- Pax Tray App 結束 ---")
        self.running = False
        try:
            from core.token_keeper import keeper
            keeper.stop()
        except: pass
        icon.stop()
        os._exit(0)

    def show_history_window(self):
        """顯示最近 7 天的歷史紀錄視窗"""
        if not HAS_TKINTER:
            # 如果不支援 GUI，嘗試用系統預設記事本開啟最新的一份 Log
            import glob
            log_dir = os.path.join(self.base_dir, "logs")
            log_files = glob.glob(os.path.join(log_dir, "*.log"))
            
            if log_files:
                # 找到最新的檔案
                latest_log = max(log_files, key=os.path.getmtime)
                try:
                    import subprocess
                    # 在 Windows 下用 notepad 開啟
                    subprocess.Popen(['notepad.exe', latest_log])
                    self._notify("日誌檢視", f"已開啟最新紀錄: {os.path.basename(latest_log)}")
                except:
                    self._notify("系統限制", f"無法開啟檔案: {os.path.basename(latest_log)}")
            else:
                self._notify("系統限制", "目前尚無任何歷史紀錄檔案。")
            return

        def create_window():
            try:
                window = tk.Tk()
                window.title("Pax 任務歷史紀錄 (最近 7 天)")
                window.geometry("600x500")
                window.configure(bg="#1e1e1e")
                
                # 建立捲動文字區域
                log_area = scrolledtext.ScrolledText(
                    window, 
                    wrap=tk.WORD, 
                    width=70, 
                    height=25,
                    bg="#252526",
                    fg="#d4d4d4",
                    insertbackground="white",
                    font=("Consolas", 10)
                )
                log_area.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
                
                # 填充紀錄內容
                history_text = self.logger.get_history_text(7)
                log_area.insert(tk.INSERT, history_text)
                log_area.configure(state='disabled') # 唯讀
                
                # 置頂視窗
                window.attributes('-topmost', True)
                window.mainloop()
            except Exception as e:
                self.debug_log(f"建立紀錄視窗失敗: {e}")

        threading.Thread(target=create_window, daemon=True).start()

    def open_auth_window(self):
        """開啟獨立的認證更新視窗"""
        try:
            self.debug_log("手動啟動認證視窗...")
            python_exe = sys.executable
            if python_exe.lower().endswith("pythonw.exe"):
                python_exe = python_exe.lower().replace("pythonw.exe", "python.exe")
            
            # 使用 --auth-only 參數
            if getattr(sys, 'frozen', False):
                # 打包模式
                # TODO: 這裡可能需要修改 pyinstaller 的 spec 支援參數
                main_script = [sys.executable, "--auth-only"]
            else:
                # 開發模式
                main_py = os.path.join(self.base_dir, "app", "main.py")
                main_script = [python_exe, main_py, "--auth-only"]
            
            env = os.environ.copy()
            env["PYTHONPATH"] = self.base_dir + os.pathsep + env.get("PYTHONPATH", "")
            
            subprocess.Popen(
                main_script,
                creationflags=subprocess.CREATE_NEW_CONSOLE,
                cwd=self.base_dir,
                env=env
            )
        except Exception as e:
            self.debug_log(f"啟動認證視窗失敗: {e}")

    def setup_tray(self):
        """建立系統匣選單與圖示"""
        try:
            print("[TrayApp] 正在建立系統匣功能面板...")
            menu_items = [
                pystray.MenuItem("打開 Pax Console", self.open_pax_console),
                pystray.MenuItem("手動更新憑證", self.open_auth_window)
            ]
            
            # 無論有沒有 TK 都顯示歷史紀錄 (沒有就用 Notepad)
            menu_items.append(pystray.MenuItem("歷史紀錄", self.show_history_window))
                
            menu_items.extend([
                pystray.Menu.SEPARATOR,
                pystray.MenuItem(lambda item: f"Pax v{self.version}", None, enabled=False),
                pystray.MenuItem("結束常駐", self.on_quit)
            ])
            
            menu = pystray.Menu(*menu_items)
            
            self.icon = pystray.Icon(
                "PaxRunner", 
                self.create_image(running=True), 
                f"Pax v{self.version} ({self.mode.upper()})",
                menu=menu
            )
            
            self.running = True
            print(f"[TrayApp] 成功進入主迴圈，請檢查系統匣圖示。")
            self.icon.run()
        except Exception as e:
            print(f"[TrayApp] 系統匣執行失敗: {e}")
            self.debug_log(f"系統匣執行失敗: {e}\n{traceback.format_exc()}")

if __name__ == "__main__":
    import argparse
    import sys
    import socket
    
    # 解決 Akasha 等大型庫的遞迴限制問題
    sys.setrecursionlimit(5000)
    
    parser = argparse.ArgumentParser()
    parser.add_argument("--console", action="store_true", help="啟動 Console 模式")
    args, unknown = parser.parse_known_args()
    
    if args.console:
        # 直接執行控制台，不檢查 Socket 鎖
        try:
            from app.main import run_llm_cli
            run_llm_cli()
        except Exception as e:
            print(f"\n❌ 啟動控制台失敗: {e}")
            import traceback
            print(traceback.format_exc())
            input("\n按任意鍵結束...")
    else:
        # 啟動系統匣，需要 Socket 鎖防止重複開啟
        try:
            _lock_holder = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            _lock_holder.bind(('127.0.0.1', 49152))
        except socket.error:
            # 這是目前你看到的報錯來源，現在我們透過 --console 參數繞過它
            print("[TrayApp] 警告：Pax 已經在運行中（請檢查系統匣圖示）。")
            sys.exit(0)
            
        runner = TrayRunner()
        runner.setup_tray()
