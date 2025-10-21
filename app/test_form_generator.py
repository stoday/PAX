#!/usr/bin/env python3
"""
工時表單生成器測試腳本
展示如何使用 generate_form_data 函數
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from main import generate_form_data
import json

def test_form_generation():
    """測試表單生成功能"""
    print("🧪 測試動態表單生成功能")
    print("="*50)
    
    # 測試 1: 使用預設設定生成當前月份
    print("\n📅 測試 1: 生成當前月份（使用預設設定）")
    form_data_current = generate_form_data()
    print(f"生成的欄位數量: {len(form_data_current)}")
    
    # 測試 2: 生成指定月份
    print("\n📅 測試 2: 生成 2025/10 月份")
    form_data_oct = generate_form_data("2025/10")
    print(f"生成的欄位數量: {len(form_data_oct)}")
    
    # 測試 3: 自訂工作時間
    print("\n📅 測試 3: 使用自訂工作時間")
    custom_times = {
        'arrival_time': '08:30',
        'leave_time': '17:30',
        'reason': '補打卡',
        'remark': '忘記帶卡'
    }
    form_data_custom = generate_form_data("2025/11", custom_times)
    print(f"生成的欄位數量: {len(form_data_custom)}")
    
    # 顯示一些關鍵欄位的範例
    print("\n🔍 範例欄位內容:")
    for key in sorted(form_data_oct.keys()):
        if 'txtArr_20251001' in key or 'txtLev_20251001' in key or 'Dp_20251001' in key:
            print(f"  {key}: {form_data_oct[key]}")
    
    print("\n✅ 測試完成！")

if __name__ == "__main__":
    test_form_generation()