# -*- coding: utf-8 -*-
import os
import datetime
import glob

class PaxLogger:
    def __init__(self, base_dir: str):
        self.log_dir = os.path.join(base_dir, "logs")
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)
        self._cleanup_old_logs()

    def _get_log_file(self) -> str:
        """取得今天的 log 檔案路徑 (YYYY-MM-DD.log)"""
        today = datetime.datetime.now().strftime("%Y-%m-%d")
        return os.path.join(self.log_dir, f"{today}.log")

    def log(self, message: str, level: str = "INFO"):
        """記錄一條訊息"""
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        log_file = self._get_log_file()
        
        entry = f"[{timestamp}] [{level}] {message}\n"
        
        try:
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(entry)
            print(f"[PaxLog] {entry.strip()}")
        except Exception as e:
            print(f"Failed to write log: {e}")

    def _cleanup_old_logs(self):
        """刪除超過 30 天的 log 檔案"""
        try:
            now = time.time()
            log_files = glob.glob(os.path.join(self.log_dir, "*.log"))
            for f in log_files:
                # 取得檔案修改時間
                if os.stat(f).st_mtime < now - 30 * 86400:
                    os.remove(f)
        except:
            pass

    def get_history_text(self, days: int = 7) -> str:
        """取得最近 N 天的 log 內容"""
        history = []
        now = datetime.datetime.now()
        
        for i in range(days - 1, -1, -1):
            target_date = now - datetime.timedelta(days=i)
            date_str = target_date.strftime("%Y-%m-%d")
            log_file = os.path.join(self.log_dir, f"{date_str}.log")
            
            history.append(f"=== {date_str} ===")
            if os.path.exists(log_file):
                try:
                    with open(log_file, "r", encoding="utf-8") as f:
                        content = f.read().strip()
                        if content:
                            history.append(content)
                        else:
                            history.append("(無紀錄)")
                except:
                    history.append("(讀取失敗)")
            else:
                history.append("(無紀錄)")
            history.append("") # 換行
            
        return "\n".join(history)

# 全域 logger 實例
import time
_logger_instance = None

def get_pax_logger(base_dir: str = None):
    global _logger_instance
    if _logger_instance is None:
        if base_dir is None:
            # 嘗試找尋專案根目錄
            base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        _logger_instance = PaxLogger(base_dir)
    return _logger_instance
