"""
ClockMate - 工時填報助手
一個自動化工時表單填寫的工具
"""

__version__ = "1.0.0"
__author__ = "ClockMate Team"
__email__ = "support@clockmate.com"

# 延遲匯入避免循環依賴
def run_cli():
    from .main import run_cli as _run_cli
    return _run_cli()

def get_tokens_from_browser():
    from .get_token import get_tokens_from_browser as _get_tokens
    return _get_tokens()

__all__ = ['run_cli', 'get_tokens_from_browser']
