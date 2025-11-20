"""
ClockMate CLI 命令列介面
"""
import sys
from .main import run_llm_cli
from .get_token import get_tokens_from_browser


def main():
    """主要的 CLI 入口點"""
    if len(sys.argv) > 1 and sys.argv[1] == "get-token":
        get_tokens_from_browser()
    else:
        run_llm_cli(auto_mode=False)


def get_token():
    """取得 Token 的 CLI 入口點"""
    get_tokens_from_browser()


if __name__ == "__main__":
    main()
