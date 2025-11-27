"""
ClockMate CLI 命令列介面
"""
from main import run_llm_cli
from get_token import get_tokens_from_browser
import argparse

# 延遲載入，僅在需要時導入 SSH 伺服器
def _start_ssh_server(host: str, port: int, fastapi_url: str):
    from ssh_server_plain import SSHServer
    server = SSHServer(host=host, port=port, fastapi_url=fastapi_url)
    server.start()

# Replace or import these in your real project
VALID_MODES = ["manual", "llm"]
VALID_SERVERS = ["local", "ssh"]
DEFAULT_MODE = "llm"
DEFAULT_SERVER = "ssh"

def main():
    """主要的 CLI 入口點"""
    parser = argparse.ArgumentParser(
        prog="clockmate",
        description="ClockMate CLI - 選擇在本機或透過 SSH 啟動工時助手；或取得 token。"
    )

    # 共同參數
    parser.add_argument(
        "-m", "--mode",
        choices=VALID_MODES,
        default=DEFAULT_MODE,
        help=f"要使用的運行模式，預設為 '{DEFAULT_MODE}'。可用值: {', '.join(VALID_MODES)}."
    )
    parser.add_argument(
        "-t", "--target",
        choices=VALID_SERVERS,
        default=DEFAULT_SERVER,
        help=f"選擇執行環境（'local' 或 'ssh'），預設為 '{DEFAULT_SERVER}'。"
    )
    parser.add_argument(
        "--get-token",
        action="store_true",
        help="從瀏覽器取得 token 後結束。"
    )

    parser.add_argument(
        "--ssh-host",
        default="127.0.0.1",
        help="SSH 伺服器監聽地址 (預設: 127.0.0.1)"
    )
    parser.add_argument(
        "--ssh-port",
        type=int,
        default=2222,
        help="SSH 伺服器監聽埠號 (預設: 2222)"
    )
    parser.add_argument(
        "--fastapi-url",
        default="http://localhost:8000",
        help="供 SSH shell 使用的 FastAPI 服務 URL (預設: http://localhost:8000)"
    )

    args = parser.parse_args()

    # 取得 token 後結束
    if args.get_token:
        get_tokens_from_browser()
        return

    # 按照 --target：未指定則 local；指定為 server 則啟動 SSH 伺服器
    if args.target == "ssh":
        _start_ssh_server(args.ssh_host, args.ssh_port, args.fastapi_url)
        return

    # 在本機直接執行
    run_llm_cli(mode=args.mode.lower())

def get_token():
    """取得 Token 的 CLI 入口點"""
    get_tokens_from_browser()


if __name__ == "__main__":
    main()
