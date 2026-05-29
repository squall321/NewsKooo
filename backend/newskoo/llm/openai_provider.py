"""OpenAI backend for the :class:`LLMProvider` interface.

Uses the ``openai`` SDK's :class:`~openai.AsyncOpenAI` client. The SDK is an
*optional* dependency (``pyproject`` extra ``llm``); imported lazily so the
module is importable without it and raises a clear error only on first use.

* ``chat`` → ``chat.completions.create``; maps usage onto :class:`LLMResponse`.
* ``extract`` → forced function/tool calling: a single function whose
  ``parameters`` is the caller schema with ``tool_choice`` pinned to it; returns
  the parsed argument dict. Falls back to JSON mode if no tool call is returned.
* ``embed`` → ``embeddings.create`` (``text-embedding-3-small/large`` per
  ``settings.embedding_model``) → :class:`EmbeddingResult` with the model dim.

Registers itself as ``"openai"`` at import time.
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

from newskoo.core.config import Settings, get_settings
from newskoo.core.logging import get_logger
from newskoo.llm.base import ChatMessage, EmbeddingResult, LLMProvider, LLMResponse
from newskoo.llm.registry import register_provider

if TYPE_CHECKING:  # pragma: no cover - typing only
    from openai import AsyncOpenAI

log = get_logger(__name__)


def _import_async_openai() -> type[AsyncOpenAI]:
    """Import :class:`AsyncOpenAI` lazily with a clear error if missing."""
    try:
        from openai import AsyncOpenAI
    except ImportError as exc:  # pragma: no cover - exercised via monkeypatch in tests
        raise ImportError(
            "The 'openai' package is required for the OpenAI LLM provider. "
            "Install it with the optional extra: `uv sync --extra llm` "
            "(or `pip install openai`)."
        ) from exc
    return AsyncOpenAI


class OpenAIProvider(LLMProvider):
    """OpenAI backend. Safe for concurrent use (a single async client is shared)."""

    name = "openai"

    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()
        self._client: AsyncOpenAI | None = None

    # ── client lifecycle ────────────────────────────────────────────────────
    def _get_client(self) -> AsyncOpenAI:
        if self._client is None:
            async_openai = _import_async_openai()
            self._client = async_openai(api_key=self._settings.openai_api_key or None)
        return self._client

    async def aclose(self) -> None:
        if self._client is not None:
            await self._client.close()
            self._client = None

    # ── message shaping ─────────────────────────────────────────────────────
    @staticmethod
    def _to_messages(messages: list[ChatMessage]) -> list[dict[str, str]]:
        """OpenAI takes a flat role/content list (system included)."""
        return [{"role": msg.role.value, "content": msg.content} for msg in messages]

    @staticmethod
    def _usage_tokens(usage: Any) -> tuple[int, int]:
        if usage is None:
            return 0, 0
        return (
            int(getattr(usage, "prompt_tokens", 0) or 0),
            int(getattr(usage, "completion_tokens", 0) or 0),
        )

    # ── LLMProvider API ──────────────────────────────────────────────────────
    async def chat(
        self,
        messages: list[ChatMessage],
        *,
        model: str | None = None,
        max_tokens: int | None = None,
        temperature: float | None = None,
    ) -> LLMResponse:
        client = self._get_client()
        model_id = model or self._settings.llm_model
        temp = self._settings.llm_temperature if temperature is None else temperature

        resp = await client.chat.completions.create(
            model=model_id,
            messages=self._to_messages(messages),
            max_tokens=max_tokens or self._settings.llm_max_tokens,
            temperature=temp,
        )
        choice = resp.choices[0]
        text = choice.message.content or ""
        input_tokens, output_tokens = self._usage_tokens(getattr(resp, "usage", None))
        return LLMResponse(
            text=text,
            model=getattr(resp, "model", model_id),
            provider=self.name,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            raw={"finish_reason": getattr(choice, "finish_reason", None)},
        )

    async def extract(
        self,
        messages: list[ChatMessage],
        schema: dict,
        *,
        model: str | None = None,
    ) -> dict:
        """Return schema-shaped JSON via forced function calling."""
        client = self._get_client()
        model_id = model or self._settings.llm_model

        function = {
            "type": "function",
            "function": {
                "name": "extract",
                "description": "Return the requested structured analysis.",
                "parameters": schema,
            },
        }
        resp = await client.chat.completions.create(
            model=model_id,
            messages=self._to_messages(messages),
            max_tokens=self._settings.llm_max_tokens,
            temperature=self._settings.llm_temperature,
            tools=[function],
            tool_choice={"type": "function", "function": {"name": "extract"}},
        )
        message = resp.choices[0].message
        tool_calls = getattr(message, "tool_calls", None) or []
        for call in tool_calls:
            if getattr(call.function, "name", None) == "extract":
                return self._loads(call.function.arguments)
        # Fallback: some deployments return plain JSON content instead.
        if message.content:
            return self._loads(message.content)
        raise ValueError("OpenAI response contained no tool call for 'extract'")

    @staticmethod
    def _loads(payload: Any) -> dict:
        if isinstance(payload, dict):
            return payload
        data = json.loads(payload)
        if not isinstance(data, dict):
            raise ValueError("Expected a JSON object from OpenAI extract")
        return data

    async def embed(
        self,
        texts: list[str],
        *,
        model: str | None = None,
    ) -> EmbeddingResult:
        client = self._get_client()
        model_id = model or self._settings.embedding_model
        resp = await client.embeddings.create(model=model_id, input=texts)
        # Preserve request order (OpenAI returns an ``index`` per item).
        items = sorted(resp.data, key=lambda d: getattr(d, "index", 0))
        vectors = [list(item.embedding) for item in items]
        dim = len(vectors[0]) if vectors else 0
        tokens = int(getattr(getattr(resp, "usage", None), "prompt_tokens", 0) or 0)
        return EmbeddingResult(
            vectors=vectors,
            model=getattr(resp, "model", model_id),
            provider=self.name,
            dim=dim,
            tokens=tokens,
        )


def _build(settings: Settings) -> LLMProvider:
    return OpenAIProvider(settings)


register_provider("openai", _build)
