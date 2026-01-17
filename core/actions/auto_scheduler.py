# -*- coding: utf-8 -*-
import os
import datetime
import time
import threading
import json
import requests
from bs4 import BeautifulSoup
from typing import Dict, Any, List, Optional
from .utils import get_auth_cookies, get_dynamic_user_agent, get_dynamic_platform_info
from .submit_work_time import BASE_TIMESHEET_URL
from core.logger import get_pax_logger

class AutoWorkTimeScheduler:
    def __init__(self, base_dir: str):
        self.base_dir = base_dir
        self.config_path = os.path.join(self.base_dir, "pax_config.json")
        self.last_run_file = os.path.join(self.base_dir, "last_auto_run.txt")
        self.target_time = (17, 55)  # 每天 17:55 執行
        self.logger = get_pax_logger(self.base_dir)
        
    def _get_last_run_date(self) -> str:
        if os.path.exists(self.last_run_file):
            try:
                with open(self.last_run_file, "r") as f:
                    return f.read().strip()
            except: pass
        return ""

    def _set_last_run_date(self, date_str: str):
        try:
            with open(self.last_run_file, "w") as f:
                f.write(date_str)
        except: pass

    def should_run_now(self) -> bool:
        """檢查現在是否應該執行"""
        now = datetime.datetime.now()
        today_str = now.strftime("%Y-%m-%d")
        
        # 1. 檢查時間是否到了 17:55
        if now.hour == self.target_time[0] and now.minute == self.target_time[1]:
            # 2. 檢查今天是否已經跑過
            if self._get_last_run_date() != today_str:
                return True
        return False

    def find_missing_workdays(self) -> List[str]:
        """找尋當月到昨天為止所有漏填的工作日 (YYYYMMDD)"""
        now = datetime.datetime.now()
        year = now.year
        month = now.month
        yesterday = now - datetime.timedelta(days=1)
        
        # 如果昨天不屬於這個月 (例如今天是 1 號)，則不執行或處理上個月 (目前簡化為僅處理當月)
        if yesterday.month != month:
            return []

        # 1. 讀取網頁內容
        session = requests.Session()
        auth_cookies = get_auth_cookies()
        for name, value in auth_cookies.items():
            if value: session.cookies.set(name, value, domain='hrwt.iii.org.tw')
            
        headers = {
            "User-Agent": get_dynamic_user_agent(),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
        }
        
        try:
            resp = session.get(BASE_TIMESHEET_URL, headers=headers, timeout=20)
            if resp.status_code != 200: return []
            
            soup = BeautifulSoup(resp.text, 'html.parser')
            
            # 2. 找出 1 號到昨天之間的所有工作日
            missing_days = []
            for day in range(1, yesterday.day + 1):
                date_obj = datetime.date(year, month, day)
                # 0-4 是週一到週五
                if date_obj.weekday() < 5:
                    date_str = date_obj.strftime("%Y%m%d")
                    # 檢查網頁中對應的輸入框是否為空
                    # ctl00$ContentPlaceHolder1$txtArr_20260117
                    input_id = f"ctl00$ContentPlaceHolder1$txtArr_{date_str}"
                    input_node = soup.find('input', {'name': input_id})
                    
                    # 如果找不到節點或值為空串，標記為 missing
                    if not input_node or not input_node.get('value', '').strip():
                        missing_days.append(date_str)
            
            return missing_days
        except Exception as e:
            self.logger.log(f"檢查漏填天數時發生錯誤: {e}", level="ERROR")
            return []

    def run_auto_upload(self, notify_callback=None) -> bool:
        """執行自動上傳流程"""
        now = datetime.datetime.now()
        today_str = now.strftime("%Y-%m-%d")
        
        self.logger.log("開始執行每日自動工時檢查...")
        missing_days = self.find_missing_workdays()
        
        if not missing_days:
            self.logger.log("檢查完畢：昨日之前無漏填工作日。")
            self._set_last_run_date(today_str)
            return True
            
        self.logger.log(f"偵測到漏填天數: {missing_days}")
        
        # 調用 submit_work_time 進行補打
        from .submit_work_time import submit_work_time
        
        # 構造補打參數
        work_times_payload = {}
        for day in missing_days:
            work_times_payload[day] = {
                "arrival_time": "09:00",
                "leave_time": "18:00",
                "reason": "忘刷",
                "remark": "Pax Auto Filler"
            }
            
        result = submit_work_time(work_times=work_times_payload)
        
        if result.get("status") == "success":
            msg = f"已為您自動補填 {len(missing_days)} 天漏登工時。"
            self.logger.log(f"自動補報成功: {msg}")
            if notify_callback: notify_callback("自動工時補打完成", msg)
            self._set_last_run_date(today_str)
            return True
        elif result.get("status") == "auth_failed":
            msg = "自動補打失敗：憑證已過期，請手動更新 Token。"
            self.logger.log(msg, level="WARNING")
            if notify_callback: notify_callback("自動填報提醒", msg)
            return False
        else:
            self.logger.log(f"自動補打發生錯誤: {result.get('message')}", level="ERROR")
            return False

def start_scheduler_thread(base_dir: str, notify_fn):
    """啟動定時調度線程"""
    scheduler = AutoWorkTimeScheduler(base_dir)
    
    def loop():
        print("[Scheduler] 定時監控線程已啟動 (目標: 17:55)")
        while True:
            try:
                if scheduler.should_run_now():
                    scheduler.run_auto_upload(notify_fn)
            except Exception as e:
                scheduler.logger.log(f"排程線程發生噴發錯誤: {e}", level="ERROR")
                
            # 每 60 秒檢查一次
            time.sleep(60)
            
    thread = threading.Thread(target=loop, daemon=True)
    thread.start()
    return thread
