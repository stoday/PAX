# -*- coding: utf-8 -*-
from .submit_work_time import submit_work_time
from .apply_travel import apply_travel
from .echo import echo
from typing import Dict, Any, Callable, Optional

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
    func = ACTIONS.get(action_name)
    if func:
        return func(cookies=cookies, **params)
    return {
        "status": "error",
        "message": f"未定義的 Action: {action_name}",
        "details": {}
    }
