# -*- coding: utf-8 -*-
from .submit_work_time import submit_work_time
from .apply_travel import apply_travel
from .echo import echo
from typing import Dict, Any, Callable, Optional
from core.logger import get_pax_logger

# Action 映射表
ACTIONS: Dict[str, Callable] = {
    "submit_work_time": submit_work_time,
    "apply_travel": apply_travel,
    "echo": echo
}

def execute_action(action_name: str, params: Dict[str, Any], cookies: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    執行指定的 Action
    """
    logger = get_pax_logger()
    
    # 過濾掉不需要詳細記錄的 echo 動作，或是只記錄有意義的部分
    if action_name != "echo":
        logger.log(f"開始執行指令: {action_name}")

    func = ACTIONS.get(action_name)
    if func:
        result = func(cookies=cookies, **params)
        
        if action_name != "echo":
            status = result.get("status", "unknown")
            msg = result.get("message", "")
            logger.log(f"指令執行完成 [{action_name}] - 狀態: {status}, 訊息: {msg}")
            
        return result
        
    error_msg = f"未定義的 Action: {action_name}"
    logger.log(error_msg, level="ERROR")
    return {
        "status": "error",
        "message": error_msg,
        "details": {}
    }
