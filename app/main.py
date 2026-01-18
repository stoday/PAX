import os
import sys

# --- 專案路徑初始化 ---
# 取得目前腳本所在的目錄 (app/)
current_dir = os.path.dirname(os.path.abspath(__file__))
# 取得專案根目錄 (app/ 的上一層)
base_dir = os.path.dirname(current_dir)
# 將根目錄加入 sys.path，確保可以找到 core, runtime 等套件
if base_dir not in sys.path:
    sys.path.insert(0, base_dir)
# ---------------------

import dotenv
from pyfiglet import Figlet
from rich.console import Console
from rich.panel import Panel
from core.logger import get_pax_logger

# 載入 TOML 設定
def get_app_version():
    try:
        import tomllib as toml # Python 3.11+
    except ImportError:
        import pip._vendor.tomli as toml # Fallback for 3.10
    
    config_path = os.path.join(base_dir, "config.toml")
    if os.path.exists(config_path):
        with open(config_path, "rb") as f:
            config = toml.load(f)
            return config.get("general", {}).get("version", "unk")
    return "0.0"

APP_VERSION = get_app_version()

# 載入環境變數
dotenv.load_dotenv()

# 常量定義
MODEL = "gemini:gemini-2.5-flash"
console = Console()
figlet = Figlet(font="slant")


def get_runtime():
    """
    根據環境變數 PAX_MODE 獲取對應的 Runtime 適配器
    """
    mode = os.getenv("PAX_MODE", "local").lower()
    
    if mode == "cloud":
        from runtime.cloud.client.executor import CloudRuntime
        server_url = os.getenv("PAX_SERVER_URL", "http://localhost:8000")
        return CloudRuntime(server_url=server_url)
    else:
        from runtime.local.executor import LocalRuntime
        return LocalRuntime()


def display_welcome_banner():
    """顯示歡迎橫幅"""
    console.print("\r\n")
    ascii_banner = figlet.renderText("Pax")
    panel = Panel.fit(
        ascii_banner.rstrip(),
        border_style="cyan",
        title=f"Pax 便利工作助手 v{APP_VERSION}",
        subtitle=f"目前的運行模式: [bold yellow]{os.getenv('PAX_MODE', 'local').upper()}[/bold yellow]",
        style="bold magenta",
    )
    console.print(panel)


def prompt_with_default(prompt_text, default_value=None):
    """具備預設值的輸入提示"""
    if default_value:
        prompt = f"[bold white]{prompt_text}[/bold white] [[cyan]{default_value}[/cyan]]: "
    else:
        prompt = f"[bold white]{prompt_text}[/bold white]: "
    user_input = console.input(prompt).strip()
    return user_input or (default_value if default_value is not None else "")


def run_llm_cli():
    display_welcome_banner()
    
    # 說明面板
    from rich.panel import Panel
    from rich.rule import Rule
    
    logger = get_pax_logger(base_dir)
    logger.log(f"--- Pax Console v{APP_VERSION} 啟動 (模式: {os.getenv('PAX_MODE', 'local').upper()}) ---")
    
    instructions = (
        "* 範圍: [bold white]本月 1 日至今日[/bold white]\n"
        "* 預設: [bold white]09:00 - 18:00[/bold white]\n"
        "* 原因: [bold white]忘刷[/bold white]\n"
        "* 指令: [cyan]exit[/cyan] 退出系統 | [cyan]Enter[/cyan] 使用預設"
    )
    console.print(Panel(instructions, title="[grey70]操作說明[/grey70]", border_style="grey37", padding=(1, 2)))
    
    # 初始化 Runtime
    try:
        runtime = get_runtime()
    except Exception as e:
        console.print(f"[bold red][X] 錯誤: 無法初始化執行環境: {e}[/bold red]")
        return

    console.print("\n[bold bright_white]請問我可以為您做什麼呢？[/bold bright_white]")

    accumulated_message = ""
    while True:
        user_message = prompt_with_default("[bold cyan]>[/bold cyan]")
        
        if user_message.lower() in ['exit', 'quit', '退出', 'stop']:
            console.print("\n[bold yellow]感謝使用 Pax，再見！[/bold yellow]")
            logger.log("--- Pax Console 結束 (使用者結束) ---")
            break
            
        if not user_message:
            continue
        
        # 視覺分隔 (僅保留 Rule 及其後一個空行)
        console.print(Rule(style="grey37"))
        console.print("\n")

        # 將使用者輸入累積成單一訊息
        if accumulated_message:
            accumulated_message = f"{user_message}\n{accumulated_message}".strip()
        else:
            accumulated_message = user_message.strip()

        console.print("[bold italic yellow]Pax 正在思考中...[/bold italic yellow]")
        
        try:
            # 獲取最新 Cookie
            from core.actions.utils import get_auth_cookies
            current_cookies = get_auth_cookies()
            
            # 1. 處理訊息（獲取 Action）
            action_result = runtime.process_message(accumulated_message, cookies=current_cookies)
            
            # 顯示 LLM 解析的描述
            console.print(f"\n[bold cyan]Pax 反映:[/bold cyan] {action_result.get('description', '已收到您的請求')}")
            console.print("\n")
            
            # 2. 執行 Action
            execute_result = runtime.execute_action(action_result, cookies=current_cookies)
            
            if execute_result['status'] == 'success':
                console.print(f"[bold green][OK] {execute_result['message']}[/bold green]")
                accumulated_message = "" 
            elif execute_result['status'] == 'auth_failed':
                console.print(f"\n[bold bright_red][!] 需要認證:[/bold bright_red] {execute_result['message']}")
                console.print("[dim]正在為您開啟登入瀏覽器...[/dim]\n")
                
                from app.get_token import get_tokens_from_browser
                get_tokens_from_browser()
                console.print("\n[bold green][OK] 認證已更新！請再說一遍您的要求。[/bold green]")
                continue
            else:
                console.print(f"[bold red][X] 執行失敗: {execute_result['message']}[/bold red]")

            console.print("\n")

        except Exception as e:
            console.print(f"[bold red][X] 發生程式異常: {e}[/bold red]")
            import traceback
            console.print(f"[grey37]{traceback.format_exc()}[/grey37]")
            console.print("\n")


if __name__ == "__main__":
    import dotenv
    # 強制從 .env 讀取，即使環境變數已存在也覆蓋
    dotenv.load_dotenv(override=True)
    run_llm_cli()
