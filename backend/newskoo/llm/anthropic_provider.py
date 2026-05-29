"""Anthropic (Claude) backend for the :class:`LLMProvider` interface.

Uses the ``anthropic`` SDK's :class:`~anthropic.AsyncAnthropic` client. The SDK
is an *optional* dependency (``pyproject`` extra ``llm``); it is imported lazily
inside the builder/methods so the module is importable without it installed and
raises a clear error only when a Claude call is actually attempted.

Key behaviours:

* ``chat`` → ``messages.create``; maps Anthropic ``usage`` onto
  :class:`LLMResponse` token counts (cache tokens folded into ``input_tokens``).
* ``extract`` → **tool use**: a single tool whose ``input_schema`` is the caller
  schema, with ``tool_choice`` forced to that tool, returning the tool ``input``
  dict. This is the most reliable way to get schema-shaped JSON from Claude.
* Prompt caching: system blocks flagged ``cache=True`` get
  ``cache_control={"type": "ephemeral"}`` so the stable prefix is cached.
* ``embed`` raises :class:`NotImplementedError` — Anthropic has no embeddings
  endpoint; the analyze stage uses the configured *embedding* provider instead.

Registers itself as ``"anthropic"`` at import time (see
:func:`newskoo.llm.registry._load_builtin`).
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from newskoo.core.config import Settings, get_settings
from newskoo.core.logging import get_logger
from newskoo.llm.base import ChatMessage, EmbeddingResult, LLMProvider, LLMResponse, Role
from newskoo.llm.registry import register_provider

if TYPE_CHECKING:  # pragma: no cover - typing only
    from anthropic import AsyncAnthropic

log = get_logger(__name__)

# Approximate USD per-token pricing (input, output) keyed by model-id prefix.
# Used for best-effort cost reporting only; never load-bearing.
_PRICING: dict[str, tuple[float, float]] = {
    "claude-opus": (5.0e-6, 25.0e-6),
    "claude-sonnet": (3.0e-6, 15.0e-6),
    "claude-haiku": (1.0e-6, 5.0e-6),
}


def _estimate_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    for prefix, (in_rate, out_rate) in _PRICING.items():
        if model.startswith(prefix):
            return input_tokens * in_rate + output_tokens * out_rate
    return 0.0


def _import_async_anthropic() -> type[AsyncAnthropic]:
    """Import :class:`AsyncAnthropic` lazily with a clear error if missing."""
    try:
        from anthropic import AsyncAnthropic
    except ImportError as exc:  # pragma: no cover - exercised via monkeypatch in tests
        raise ImportError(
            "The 'anthropic' package is required for the Anthropic LLM provider. "
            "Install it with the optional extra: `uv sync --extra llm` "
            "(or `pip install anthropic`)."
        ) from exc
    return AsyncAnthropic


class AnthropicProvider(LLMProvider):
    """Claude backend. Safe for concurrent use (a single async client is shared)."""

    name = "anthropic"

    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()
        self._client: AsyncAnthropic | None = None

    # ── client lifecycle ────────────────────────────────────────────────────
    def _get_client(self) -> AsyncAnthropic:
        if self._client is None:
            async_anthropic = _import_async_anthropic()
            self._client = async_anthropic(api_key=self._settings.anthropic_api_key or None)
        return self._client

    async def aclose(self) -> None:
        if self._client is not None:
            await self._client.close()
            self._client = None

    # ── message shaping ─────────────────────────────────────────────────────
    @staticmethod
    def _split_messages(
        messages: list[ChatMessage],
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        """Split into (system_blocks, conversation_messages).

        System blocks become Anthropic text blocks; those flagged ``cache=True``
        carry ``cache_control`` so the stable prefix is cached. User/assistant
        turns become ordinary message dicts.
        """
        system_blocks: list[dict[str, Any]] = []
        conversation: list[dict[str, Any]] = []
        for msg in messages:
            if msg.role == Role.SYSTEM:
                block: dict[str, Any] = {"type": "text", "text": msg.content}
                if msg.cache:
                    block["cache_control"] = {"type": "ephemeral"}
                system_blocks.append(block)
            else:
                conversation.append({"role": msg.role.value, "content": msg.content})
        return system_blocks, conversation

    @staticmethod
    def _usage_tokens(usage: Any) -> tuple[int, int]:
        """Map Anthropic usage → (input_tokens, output_tokens).

        Cache-creation and cache-read tokens are folded into the input total so
        callers see the full prompt size regardless of cache state.
        """
        if usage is None:
            return 0, 0
        input_tokens = int(getattr(usage, "input_tokens", 0) or 0)
        input_tokens += int(getattr(usage, "cache_creation_input_tokens", 0) or 0)
        input_tokens += int(getattr(usage, "cache_read_input_tokens", 0) or 0)
        output_tokens = int(getattr(usage, "output_tokens", 0) or 0)
        return input_tokens, output_tokens

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
        system_blocks, conversation = self._split_messages(messages)

        kwargs: dict[str, Any] = {
            "model": model_id,
            "max_tokens": max_tokens or self._settings.llm_max_tokens,
            "messages": conversation,
        }
        if system_blocks:
            kwargs["system"] = system_blocks
        temp = self._settings.llm_temperature if temperature is None else temperature
        if temp is not None:
            kwargs["temperature"] = temp

        resp = await client.messages.create(**kwargs)

        text = "".join(
            block.text for block in resp.content if getattr(block, "type", None) == "text"
        )
        input_tokens, output_tokens = self._usage_tokens(getattr(resp, "usage", None))
        return LLMResponse(
            text=text,
            model=getattr(resp, "model", model_id),
            provider=self.name,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_usd=_estimate_cost(model_id, input_tokens, output_tokens),
            raw={"stop_reason": getattr(resp, "stop_reason", None)},
        )

    async def extract(
        self,
        messages: list[ChatMessage],
        schema: dict,
        *,
        model: str | None = None,
    ) -> dict:
        """Return schema-shaped JSON via forced single-tool use.

        A synthetic tool ``extract`` is defined with ``input_schema=schema``;
        ``tool_choice`` forces Claude to call it, so the tool ``input`` is the
        structured result.
        """
        client = self._get_client()
        model_id = model or self._settings.llm_model
        system_blocks, conversation = self._split_messages(messages)

        tool = {
            "name": "extract",
            "description": "Return the requested structured analysis.",
            "input_schema": schema,
        }
        kwargs: dict[str, Any] = {
            "model": model_id,
            "max_tokens": self._settings.llm_max_tokens,
            "messages": conversation,
            "tools": [tool],
            "tool_choice": {"type": "tool", "name": "extract"},
        }
        if system_blocks:
            kwargs["system"] = system_blocks

        resp = await client.messages.create(**kwargs)
        for block in resp.content:
            is_tool = getattr(block, "type", None) == "tool_use"
            if is_tool and getattr(block, "name", None) == "extract":
                tool_input = block.input
                return dict(tool_input) if isinstance(tool_input, dict) else {}
        raise ValueError("Anthropic response contained no tool_use block for 'extract'")

    async def embed(
        self,
        texts: list[str],
        *,
        model: str | None = None,
    ) -> EmbeddingResult:
        raise NotImplementedError(
            "Anthropic has no embeddings endpoint; configure embedding_provider "
            "to 'openai' or 'local' for embeddings."
        )


def _build(settings: Settings) -> LLMProvider:
    return AnthropicProvider(settings)


register_provider("anthropic", _build)
