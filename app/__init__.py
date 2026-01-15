from .main import (
    run_llm_cli,
)

try:
    from .llm_prompt import (
        prompt_create,
    )
except ImportError:
    from llm_prompt import (
        prompt_create,
    )

__all__ = [
    "run_llm_cli",
    "prompt_create",
]
"""
Pax - 便利工作助手
一個自動化工時表單填寫的工具
"""

__version__ = "1.0.0"
__author__ = "Pax Team"
__email__ = "tsaiyuforwork@gmail.com"