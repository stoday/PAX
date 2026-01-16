# -*- coding: utf-8 -*-
import os
import platform
from typing import Dict, Any

def get_dynamic_platform_info():
    system = platform.system()
    if system == "Darwin": return '"macOS"'
    elif system == "Windows": return '"Windows"'
    elif system == "Linux": return '"Linux"'
    return '"Unknown"'

def get_dynamic_user_agent():
    system = platform.system()
    if system == "Darwin":
        try:
            mac_version = platform.mac_ver()[0].replace('.', '_')
            return f"Mozilla/5.0 (Macintosh; Intel Mac OS X {mac_version}) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"
        except:
            return "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"
    elif system == "Windows":
        try:
            version_map = {'10': '10.0', '11': '10.0'}
            win_version = version_map.get(platform.release(), '10.0')
            return f"Mozilla/5.0 (Windows NT {win_version}; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"
        except:
            return "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"
    return "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"

def get_auth_cookies() -> Dict[str, str]:
    import dotenv
    dotenv.load_dotenv(override=True) # 強制覆蓋現有環境變數
    return {
        'ASP.NET_SessionId': os.getenv("ASP_NET_SESSION_ID", ""),
        'clientTicket': os.getenv("CLIENT_TICKET", ""),
        'clientUserName': os.getenv("CLIENT_USERNAME", ""),
    }
