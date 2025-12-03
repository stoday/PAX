from .main import (
    run_llm_cli,
    set_output_stream,
    set_io_hooks,
    suppress_lib_output,
    redirect_lib_output_to_logger,
    get_agent_logger,
    LoggerWriter,
    generate_form_llm_data,
    get_fresh_form_llm_data,
    generate_form_data,
    build_timesheet_url,
)

try:
    from .llm_clockmate import (
        prompt_create,
        parse_llm_output,
    )
except ImportError:
    # Fallback for direct script use
    from llm_clockmate import (
        prompt_create,
        parse_llm_output,
    )

__all__ = [
    "run_llm_cli",
    "set_output_stream",
    "set_io_hooks",
    "suppress_lib_output",
    "redirect_lib_output_to_logger",
    "get_agent_logger",
    "LoggerWriter",
    "generate_form_llm_data",
    "get_fresh_form_llm_data",
    "generate_form_data",
    "build_timesheet_url",
    "prompt_create",
    "parse_llm_output",
]
"""
ClockMate - 工時填報助手
一個自動化工時表單填寫的工具
"""

__version__ = "1.0.0"
__author__ = "ClockMate Team"
__email__ = "support@clockmate.com"

# 延遲匯入避免循環依賴
def run_cli():
    from main import run_llm_cli as _run_cli
    return _run_cli()

def get_tokens_from_browser():
    from get_token import get_tokens_from_browser as _get_tokens
    return _get_tokens()

__all__ = ["main", "run_ssh_server", 'run_llm_cli', 'get_tokens_from_browser']