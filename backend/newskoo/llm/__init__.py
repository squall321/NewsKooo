"""Multi-provider LLM abstraction. Import :func:`get_provider` to obtain the
configured backend; implement :class:`LLMProvider` to add new backends."""

from newskoo.llm.base import (
    ChatMessage,
    EmbeddingResult,
    LLMProvider,
    LLMResponse,
    Role,
)
from newskoo.llm.registry import get_provider, register_provider

__all__ = [
    "ChatMessage",
    "EmbeddingResult",
    "LLMProvider",
    "LLMResponse",
    "Role",
    "get_provider",
    "register_provider",
]
