"""Local backend (Ollama) for the :class:`LLMProvider` interface.

Talks to an Ollama server over plain HTTP via :mod:`httpx` (no extra SDK). The
base URL comes from ``settings.ollama_base_url``.

* ``chat`` → ``POST /api/chat`` (non-streaming) → :class:`LLMResponse`.
* ``extract`` → ``POST /api/chat`` with ``format="json"`` plus a schema
  instruction appended to the system prompt; the assistant message content is
  parsed as JSON.
* ``embed`` → ``POST /api/embed`` (newer) falling back to ``/api/embeddings``
  (older), one call covering all texts → :class:`EmbeddingResult`.

Registers itself as ``"local"`` at import time.
"""

from __future__ import annotations

import json
from typing import Any

import httpx

from newskoo.core.config import Settings, get_settings
from newskoo.core.logging import get_logger
from newskoo.llm.base import ChatMessage, EmbeddingResult, LLMProvider, LLMResponse, Role
from newskoo.llm.registry import register_provider

log = get_logger(__name__)

_DEFAULT_TIMEOUT = 120.0


class LocalProvider(LLMProvider):
    """Ollama backend. Safe for concurrent use (httpx clients are per-call)."""

    name = "local"

    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()
        self._base_url = self._settings.ollama_base_url.rstrip("/")

    def _client(self) -> httpx.AsyncClient:
        return httpx.AsyncClient(base_url=self._base_url, timeout=_DEFAULT_TIMEOUT)

    # ── message shaping ─────────────────────────────────────────────────────
    @staticmethod
    def _to_messages(messages: list[ChatMessage]) -> list[dict[str, str]]:
        return [{"role": msg.role.value, "content": msg.content} for msg in messages]

    @staticmethod
    def _usage_tokens(payload: dict[str, Any]) -> tuple[int, int]:
        return (
            int(payload.get("prompt_eval_count", 0) or 0),
            int(payload.get("eval_count", 0) or 0),
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
        model_id = model or self._settings.llm_model
        temp = self._settings.llm_temperature if temperature is None else temperature
        body: dict[str, Any] = {
            "model": model_id,
            "messages": self._to_messages(messages),
            "stream": False,
            "options": {
                "temperature": temp,
                "num_predict": max_tokens or self._settings.llm_max_tokens,
            },
        }
        async with self._client() as client:
            resp = await client.post("/api/chat", json=body)
            resp.raise_for_status()
            data = resp.json()

        text = (data.get("message") or {}).get("content", "")
        input_tokens, output_tokens = self._usage_tokens(data)
        return LLMResponse(
            text=text,
            model=data.get("model", model_id),
            provider=self.name,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            raw={"done_reason": data.get("done_reason")},
        )

    async def extract(
        self,
        messages: list[ChatMessage],
        schema: dict,
        *,
        model: str | None = None,
    ) -> dict:
        """Return schema-shaped JSON using Ollama's ``format="json"`` mode.

        Ollama has no tool-use, so we steer with a system instruction carrying
        the JSON Schema and request JSON-mode output, then parse the content.
        """
        model_id = model or self._settings.llm_model
        steered = self._inject_schema(messages, schema)
        body: dict[str, Any] = {
            "model": model_id,
            "messages": self._to_messages(steered),
            "stream": False,
            "format": "json",
            "options": {
                "temperature": self._settings.llm_temperature,
                "num_predict": self._settings.llm_max_tokens,
            },
        }
        async with self._client() as client:
            resp = await client.post("/api/chat", json=body)
            resp.raise_for_status()
            data = resp.json()

        content = (data.get("message") or {}).get("content", "")
        parsed = json.loads(content)
        if not isinstance(parsed, dict):
            raise ValueError("Expected a JSON object from local extract")
        return parsed

    @staticmethod
    def _inject_schema(messages: list[ChatMessage], schema: dict) -> list[ChatMessage]:
        """Append a JSON-Schema instruction to a (possibly synthetic) system block."""
        instruction = (
            "Respond with a single JSON object that strictly conforms to this "
            f"JSON Schema. Output JSON only, no prose:\n{json.dumps(schema)}"
        )
        out = list(messages)
        for i, msg in enumerate(out):
            if msg.role == Role.SYSTEM:
                out[i] = msg.model_copy(update={"content": f"{msg.content}\n\n{instruction}"})
                return out
        out.insert(0, ChatMessage(role=Role.SYSTEM, content=instruction))
        return out

    async def embed(
        self,
        texts: list[str],
        *,
        model: str | None = None,
    ) -> EmbeddingResult:
        model_id = model or self._settings.embedding_model
        async with self._client() as client:
            data = await self._embed_request(client, model_id, texts)

        vectors = self._extract_vectors(data)
        dim = len(vectors[0]) if vectors else 0
        return EmbeddingResult(
            vectors=vectors,
            model=data.get("model", model_id),
            provider=self.name,
            dim=dim,
            tokens=int(data.get("prompt_eval_count", 0) or 0),
        )

    async def _embed_request(
        self, client: httpx.AsyncClient, model_id: str, texts: list[str]
    ) -> dict[str, Any]:
        """Try the newer batch ``/api/embed`` endpoint, fall back to ``/api/embeddings``."""
        resp = await client.post("/api/embed", json={"model": model_id, "input": texts})
        if resp.status_code == httpx.codes.NOT_FOUND:
            # Older Ollama: single-prompt endpoint; one request per text.
            results: list[list[float]] = []
            for text in texts:
                legacy = await client.post(
                    "/api/embeddings", json={"model": model_id, "prompt": text}
                )
                legacy.raise_for_status()
                results.append(legacy.json().get("embedding", []))
            return {"embeddings": results, "model": model_id}
        resp.raise_for_status()
        return resp.json()

    @staticmethod
    def _extract_vectors(data: dict[str, Any]) -> list[list[float]]:
        if "embeddings" in data:  # /api/embed batch shape
            return [list(v) for v in data["embeddings"]]
        if "embedding" in data:  # single-vector shape
            return [list(data["embedding"])]
        return []


def _build(settings: Settings) -> LLMProvider:
    return LocalProvider(settings)


register_provider("local", _build)
