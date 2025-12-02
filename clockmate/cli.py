"""
ClockMate CLI 命令列介面
"""
from get_token import get_tokens_from_browser
from agent_tools import agent
from datetime import datetime
import argparse
import termlit
import sys
import io


class _FilteringStream(io.TextIOBase):
    """Filter out specific noisy lines from stdout/stderr."""

    def __init__(self, target, drop_keywords=None):
        self._target = target
        self._drop_keywords = drop_keywords or []

    def write(self, data):
        if not data:
            return 0
        filtered_parts = []
        for line in data.splitlines(keepends=True):
            text = line.strip()
            if any(keyword in text for keyword in self._drop_keywords):
                continue
            filtered_parts.append(line)
        out = "".join(filtered_parts)
        if not out:
            return len(data)
        try:
            return self._target.write(out)
        except OSError:
            # 如果底層串流已經關閉，忽略這次寫入
            return len(data)

    def flush(self):
        try:
            return self._target.flush()
        except OSError:
            return None


def install_output_filter():
    """Install a lightweight stdout/stderr filter to drop noisy lines."""
    drop_keywords = ["Spend Time:", "-------------------------------------"]
    original_stdout, original_stderr = sys.stdout, sys.stderr
    sys.stdout = _FilteringStream(original_stdout, drop_keywords)
    sys.stderr = _FilteringStream(original_stderr, drop_keywords)

    def restore():
        sys.stdout = original_stdout
        sys.stderr = original_stderr

    return restore

def _start_ssh_server(host: str, port: int, fastapi_url: str):
    """啟動 SSH 伺服器"""
    restore_filter = install_output_filter()

    def app():
        termlit.welcome(
            title='Hello',
            subtitle='Version 0.1.0',
            description='您填工時的好幫手',
        )
        
        history_session = ''
        while True:
            prompt = termlit.input("你: ")
            if prompt.lower() in ['exit', 'quit']:
                termlit.write("再見！")
                break
            
            with termlit.spinner("dots", "正在處理您的請求..."):
                # 問問題並使用工具回答
                prompt_for_today_date = datetime.now().strftime("今天是 %Y 年 %m 月 %d 日。")
                response = agent("""
                # 資訊:
                {today_date_info}
                
                # 任務
                - 協助使用者填寫工作時間(工時)紀錄表單。根據使用者所描述的需求，蒐集判斷使用者需要填寫哪些日期的工時，並使用預設或依據使用者指定的上下班時間、原因與備註來完成表單資訊。最後使用適合的工具將表單資訊填寫完成後送出給系統。
                - 如果使用者的問題是想要離開這個系統，或是表達離開 / 掰掰 / 881 之類的，提醒她可以鍵入 'exit' 或 'quit'，或是按 Ctrl+C 來結束對話。
                
                # 歷史對話
                {history}
                
                # 使用者需求                   
                {user_prompt}
            """.format(
                today_date_info=prompt_for_today_date, 
                history=history_session,
                user_prompt=prompt))  # "幫我填11月5日的工時，然後上班時間要接近9點，因為我那天有點晚到。"

            # spinner 結束後換行，再輸出回應，避免兩者同一行
            termlit.write("")
            termlit.write('AI: ' + response)
            
            history_session += f"User: {prompt}\nAI: {response}\n"
    
    try:
        termlit.run(app)
    finally:
        restore_filter()
            
VALID_MODES = ["manual", "llm"]
DEFAULT_MODE = "llm"

def main():
    """主要的 CLI 入口點"""
    parser = argparse.ArgumentParser(
        prog="clockmate",
        description="ClockMate CLI 或取得 token。"
    )

    # 共同參數
    parser.add_argument(
        "-m", "--mode",
        choices=VALID_MODES,
        default=DEFAULT_MODE,
        help=f"要使用的運行模式，預設為 '{DEFAULT_MODE}'。可用值: {', '.join(VALID_MODES)}."
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

    # 固定啟動 SSH 伺服器
    _start_ssh_server(args.ssh_host, args.ssh_port, args.fastapi_url)
    return

def get_token():
    """取得 Token 的 CLI 入口點"""
    get_tokens_from_browser()


if __name__ == "__main__":
    main()
