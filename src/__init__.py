"""
本质看板 (The Essence Logic) 4.0 - 源代码包
"""

from .aibuilders_client import AIBuildersClient, get_client
from .system_prompt import SYSTEM_PROMPT

__all__ = ["AIBuildersClient", "get_client", "SYSTEM_PROMPT"]
