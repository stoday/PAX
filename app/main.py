from pyfiglet import Figlet
from rich.console import Console
from rich.panel import Panel
import dotenv
import os
import akasha
import subprocess

# 載入環境變數
dotenv.load_dotenv()

MODEL = "gemini:gemini-2.5-flash"
console = Console()
figlet = Figlet(font="slant")
stream_process = None


def run_mcp_google_map():
    global stream_process

    if stream_process and stream_process.poll() is None:
        print("streamable_http already running")
        return
    cwd = os.path.join(os.path.abspath(os.getcwd()), "tools", "mcp-google-map")
    stream_process = subprocess.Popen(
        ["npm", "start"],
        cwd=cwd,
        stdout=None,   # 或 None
        # stdout=subprocess.PIPE,   # 或 None
        stderr=None,
        # stderr=subprocess.PIPE,
        shell=True,               # Windows 一定要
        env=os.environ.copy()
    )

def display_welcome_banner(plain: bool = False):
    console.print("\r\n")

    ascii_banner = figlet.renderText("Pax")
    panel = Panel.fit(
        ascii_banner.rstrip(),
        border_style="cyan",
        title="Pax 便利工作助手",
        style="bold magenta",
    )
    console.print(panel)


def prompt_with_default(prompt_text, default_value=None):
    # 始終使用 Rich 標記以確保渲染樣式
    if default_value:
        prompt = f"[bold white]{prompt_text}[/bold white] [[cyan]{default_value}[/cyan]]: "
    else:
        prompt = f"[bold white]{prompt_text}[/bold white]: "
    user_input = console.input(prompt).strip()
    return user_input or (default_value if default_value is not None else "")

def run_llm_cli(mode="llm"):
    from app import prompt_create
    # 顯示 banner 並啟動必要服務
    run_mcp_google_map()
    display_welcome_banner(plain=False)
    accumulated_message = ""
    if mode == "llm":
        console.print("處理範圍：本月 1 日至今日")
        console.print("預設時間 09:00-18:00")
        console.print("預設原因：忘刷")
        console.print(" - 直接按 [Enter]：將使用預設值")
        console.print(" - 輸入 'exit'： 退出系統")
        console.print("[bold]請問我可以為您做什麼呢[/bold]")

        # 迴圈：若 LLM 回覆
        accumulated_message = ""
        while True:
            # 首次或累積後的訊息提示
            user_message = prompt_with_default(">")
            
            # 將使用者輸入累積成單一訊息（保留上下文）
            if accumulated_message:
                accumulated_message = f"{user_message}\n{accumulated_message}".strip()
            else:
                accumulated_message = user_message.strip()

            console.print("[bold]思考中...[/bold]")
            user_prompt = prompt_create(user_message=accumulated_message)
            
            # 定義 MCP 伺服器連接資訊
            tools_dir = os.path.abspath(os.path.join(os.getcwd(), "tools"))
            travel_helper_cwd = os.path.join(tools_dir, "travel_helper")
            llm_uploader_path = os.path.join(tools_dir, "llm_uploader.py")
            
            connection_info = {
                "submit_work_times": {
                    "command": "python",
                    "args": ["-X", "utf8", llm_uploader_path],  # 注意要用 utf8 編碼執行
                    "transport": "stdio",
                },
                "google-map": {
                    "url": "http://localhost:3000/mcp",
                    "transport": "streamable_http",
                },
                "fare_estimator": {
                    "command": "python",
                    "args": [f"{travel_helper_cwd}\\fare_estimator.py"],
                    "transport": "stdio",
                },
                "dc_apply": {
                    "command": "python",
                    "args": [f"{travel_helper_cwd}\\apply.py"],
                    "transport": "stdio",
                }
            }
            
            agent = akasha.agents(
                model=MODEL,
                temperature=0.01,
                verbose=True,
                max_input_tokens=50000,
                max_output_tokens=50000
            )
            
            response = agent.mcp_agent(connection_info, user_prompt)
            console.print(response)


if __name__ == "__main__":
    run_llm_cli()
