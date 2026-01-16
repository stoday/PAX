# -*- coding: utf-8 -*-
from typing import Dict, Any, Optional

def echo(cookies: Optional[Dict[str, Any]] = None, **params) -> Dict[str, Any]:
    """
    簡單的回應動作
    """
    return {
        "status": "success",
        "message": params.get("message", "已收到您的訊息"),
        "details": {}
    }
