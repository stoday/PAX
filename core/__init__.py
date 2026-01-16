"""
Pax Core Package

核心業務邏輯套件，包含：
- runtime_adapter: 執行環境適配器介面
- llm: LLM 處理邏輯
- mcp_tools: MCP 工具
- models: 資料模型
- actions: 指令定義與執行
"""

from .runtime_adapter import RuntimeAdapter
from .llm import LLMHandler
from .models import (
    ChatRequest,
    ChatResponse,
    CallbackRequest,
    CallbackResponse,
    ActionResult,
)

__version__ = "1.0.0"
__all__ = [
    "RuntimeAdapter",
    "LLMHandler",
    "ChatRequest",
    "ChatResponse",
    "CallbackRequest",
    "CallbackResponse",
    "ActionResult",
]
