"""
ClockMate CLI 命令列介面
"""
import sys
from main import run_llm_cli
from get_token import get_tokens_from_browser
import argparse
import sys

# Replace or import these in your real project
VALID_MODES = ["local", "ssh", "llm"]
DEFAULT_MODE = "local"



def main():
    """主要的 CLI 入口點"""
    parser = argparse.ArgumentParser(
        prog="clockmate",
        description="ClockMate CLI - 使用 --mode 選擇運行模式，或 --get-token 取得 token。"
    )

    # --mode / -m 參數，用來選擇模式
    parser.add_argument(
        "-m", "--mode",
        choices=VALID_MODES,
        default=DEFAULT_MODE,
        help=f"要使用的模式，預設為 '{DEFAULT_MODE}'。可用值: {', '.join(VALID_MODES)}."
    )
    
    # --get-token 開關，跟舊的 "get-token" subcommand 等價但更 argparse-friendly
    parser.add_argument(
        "--get-token",
        action="store_true",
        help="從瀏覽器取得 token，取得完後立即結束 (獨立於 --mode)。"
    )

    args = parser.parse_args()

    # 如果使用者要求取得 token，優先處理並結束
    if args.get_token:
        get_tokens_from_browser()
        return

    # 根據 mode 使用 if/else 選擇啟動函式
    mode = args.mode.lower()
    if mode == "llm":
        # 已知存在於 main.py 的實作
        run_llm_cli()
    elif mode == "local":
        run_local_cli()
    elif mode == "ssh":
        # 嘗試匯入 ssh 啟動函式，若不存在給予明確錯誤訊息
        try:
            from main import run_ssh_cli
        except Exception:
            print(
                "run_ssh_cli() not found in main.py. "
                "請在 main.py 中實作 run_ssh_cli()，或改用 --mode llm。",
                file=sys.stderr
            )
            sys.exit(2)
        else:
            run_ssh_cli()


def get_token():
    """取得 Token 的 CLI 入口點"""
    get_tokens_from_browser()


if __name__ == "__main__":
    main()
