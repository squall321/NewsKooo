"""Provider-agnostic LLM interface.

All analysis code depends only on :class:`LLMProvider`. Concrete backends
(Claude, OpenAI, local/Ollama) live in sibling modules and register themselves.
Designed for multilingual input (original-language article text) and for
prompt caching where the backend supports it.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from enum import StrEnum

from pydantic import BaseModel, Field


class Role(StrEnum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"


class ChatMessage(BaseModel):
    role: Role
    content: str
    cache: bool = False  # hint: cache this block if the backend supports it


class LLMResponse(BaseModel):
    text: str
    model: str
    provider: str
    input_tokens: int = 0
    output_tokens: int = 0
    cost_usd: float = 0.0
    raw: dict = Field(default_factory=dict)


class EmbeddingResult(BaseModel):
    vectors: list[list[float]]
    model: str
    provider: str
    dim: int
    tokens: int = 0


class LLMProvider(ABC):
    """Backend contract. Implementations must be safe for concurrent use."""

    name: str

    @abstractmethod
    async def chat(
        self,
        messages: list[ChatMessage],
        *,
        model: str | None = None,
        max_tokens: int | None = None,
        temperature: float | None = None,
    ) -> LLMResponse: ...

    @abstractmethod
    async def extract(
        self,
        messages: list[ChatMessage],
        schema: dict,
        *,
        model: str | None = None,
    ) -> dict:
        """Return structured JSON conforming to ``schema`` (JSON Schema).
        Backends should use native tool/function-calling or JSON mode."""

    @abstractmethod
    async def embed(
        self,
        texts: list[str],
        *,
        model: str | None = None,
    ) -> EmbeddingResult: ...

    async def aclose(self) -> None:  # optional cleanup hook
        return None
