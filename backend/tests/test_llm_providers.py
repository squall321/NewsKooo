"""LLM provider tests (no network).

Anthropic/OpenAI: monkeypatch the SDK client classes with fakes that return
canned response shapes. Ollama: respx-mock the HTTP endpoints. Each test also
asserts the provider registers under its name so ``get_provider`` resolves it.
"""

from __future__ import annotations

import sys
import types
from typing import Any

import httpx
import pytest
import respx
from newskoo.core.config import Settings
from newskoo.llm.base import ChatMessage, Role
from newskoo.llm.registry import _BUILDERS, _CACHE, get_provider

_SETTINGS = Settings(
    llm_provider="anthropic",
    llm_model="claude-sonnet-4-6",
    embedding_provider="local",
    embedding_model="bge-m3",
    embedding_dim=4,
    ollama_base_url="http://ollama.test:11434",
)

_SCHEMA = {
    "type": "object",
    "properties": {"summary": {"type": "string"}},
    "required": ["summary"],
}


@pytest.fixture(autouse=True)
def _clear_provider_cache():
    """Keep the registry cache from leaking provider instances between tests."""
    _CACHE.clear()
    yield
    _CACHE.clear()


# ── Anthropic ────────────────────────────────────────────────────────────────


class _FakeAnthropicMessages:
    def __init__(self, recorder: dict[str, Any]) -> None:
        self._recorder = recorder

    async def create(self, **kwargs: Any) -> Any:
        self._recorder["kwargs"] = kwargs
        if "tools" in kwargs:
            block = types.SimpleNamespace(
                type="tool_use", name="extract", input={"summary": "extracted"}
            )
        else:
            block = types.SimpleNamespace(type="text", text="hello from claude")
        usage = types.SimpleNamespace(
            input_tokens=10,
            output_tokens=5,
            cache_creation_input_tokens=2,
            cache_read_input_tokens=3,
        )
        return types.SimpleNamespace(
            content=[block], model=kwargs["model"], usage=usage, stop_reason="end_turn"
        )


class _FakeAsyncAnthropic:
    def __init__(self, **kwargs: Any) -> None:
        self.init_kwargs = kwargs
        self.recorder: dict[str, Any] = {}
        self.messages = _FakeAnthropicMessages(self.recorder)

    async def close(self) -> None:
        return None


@pytest.fixture
def _fake_anthropic_module(monkeypatch: pytest.MonkeyPatch) -> _FakeAsyncAnthropic:
    module = types.ModuleType("anthropic")
    module.AsyncAnthropic = _FakeAsyncAnthropic  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "anthropic", module)
    return _FakeAsyncAnthropic


async def test_anthropic_registers_and_chat(_fake_anthropic_module) -> None:
    from newskoo.llm.anthropic_provider import AnthropicProvider

    assert "anthropic" in _BUILDERS
    # The registry builder resolves to our provider class (client built lazily).
    assert isinstance(get_provider("anthropic"), AnthropicProvider)

    provider = AnthropicProvider(_SETTINGS)
    resp = await provider.chat(
        [
            ChatMessage(role=Role.SYSTEM, content="You are helpful.", cache=True),
            ChatMessage(role=Role.USER, content="Hi"),
        ]
    )
    assert resp.text == "hello from claude"
    assert resp.provider == "anthropic"
    # cache + creation + read folded into input_tokens (10 + 2 + 3).
    assert resp.input_tokens == 15
    assert resp.output_tokens == 5
    # system block carries cache_control; conversation excludes the system turn.
    kwargs = provider._get_client().recorder["kwargs"]  # type: ignore[attr-defined]
    assert kwargs["system"][0]["cache_control"] == {"type": "ephemeral"}
    assert kwargs["messages"] == [{"role": "user", "content": "Hi"}]


async def test_anthropic_extract_uses_forced_tool(_fake_anthropic_module) -> None:
    from newskoo.llm.anthropic_provider import AnthropicProvider

    provider = AnthropicProvider(_SETTINGS)
    result = await provider.extract(
        [ChatMessage(role=Role.USER, content="Summarize")], _SCHEMA
    )
    assert result == {"summary": "extracted"}
    kwargs = provider._get_client().recorder["kwargs"]  # type: ignore[attr-defined]
    assert kwargs["tool_choice"] == {"type": "tool", "name": "extract"}
    assert kwargs["tools"][0]["input_schema"] == _SCHEMA


async def test_anthropic_embed_not_implemented(_fake_anthropic_module) -> None:
    from newskoo.llm.anthropic_provider import AnthropicProvider

    provider = AnthropicProvider(_SETTINGS)
    with pytest.raises(NotImplementedError):
        await provider.embed(["x"])


# ── OpenAI ───────────────────────────────────────────────────────────────────


class _FakeOpenAIChatCompletions:
    def __init__(self, recorder: dict[str, Any]) -> None:
        self._recorder = recorder

    async def create(self, **kwargs: Any) -> Any:
        self._recorder["chat_kwargs"] = kwargs
        if "tools" in kwargs:
            tool_call = types.SimpleNamespace(
                function=types.SimpleNamespace(name="extract", arguments='{"summary": "via-fn"}')
            )
            message = types.SimpleNamespace(content=None, tool_calls=[tool_call])
        else:
            message = types.SimpleNamespace(content="chat reply", tool_calls=None)
        choice = types.SimpleNamespace(message=message, finish_reason="stop")
        usage = types.SimpleNamespace(prompt_tokens=7, completion_tokens=4)
        return types.SimpleNamespace(choices=[choice], model=kwargs["model"], usage=usage)


class _FakeOpenAIEmbeddings:
    async def create(self, **kwargs: Any) -> Any:
        n = len(kwargs["input"])
        data = [
            types.SimpleNamespace(index=i, embedding=[0.1, 0.2, 0.3, 0.4]) for i in range(n)
        ]
        return types.SimpleNamespace(
            data=data, model=kwargs["model"], usage=types.SimpleNamespace(prompt_tokens=3)
        )


class _FakeAsyncOpenAI:
    def __init__(self, **kwargs: Any) -> None:
        self.recorder: dict[str, Any] = {}
        self.chat = types.SimpleNamespace(
            completions=_FakeOpenAIChatCompletions(self.recorder)
        )
        self.embeddings = _FakeOpenAIEmbeddings()

    async def close(self) -> None:
        return None


@pytest.fixture
def _fake_openai_module(monkeypatch: pytest.MonkeyPatch) -> _FakeAsyncOpenAI:
    module = types.ModuleType("openai")
    module.AsyncOpenAI = _FakeAsyncOpenAI  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "openai", module)
    return _FakeAsyncOpenAI


async def test_openai_registers_and_chat(_fake_openai_module) -> None:
    from newskoo.llm.openai_provider import OpenAIProvider

    assert "openai" in _BUILDERS
    provider = OpenAIProvider(_SETTINGS)
    resp = await provider.chat([ChatMessage(role=Role.USER, content="Hi")], model="gpt-x")
    assert resp.text == "chat reply"
    assert resp.input_tokens == 7
    assert resp.output_tokens == 4
    assert resp.provider == "openai"


async def test_openai_extract_function_call(_fake_openai_module) -> None:
    from newskoo.llm.openai_provider import OpenAIProvider

    provider = OpenAIProvider(_SETTINGS)
    result = await provider.extract([ChatMessage(role=Role.USER, content="Sum")], _SCHEMA)
    assert result == {"summary": "via-fn"}
    kwargs = provider._get_client().recorder["chat_kwargs"]  # type: ignore[attr-defined]
    assert kwargs["tool_choice"] == {"type": "function", "function": {"name": "extract"}}


async def test_openai_embed_returns_dim(_fake_openai_module) -> None:
    from newskoo.llm.openai_provider import OpenAIProvider

    provider = OpenAIProvider(_SETTINGS)
    result = await provider.embed(["a", "b"], model="text-embedding-3-small")
    assert result.dim == 4
    assert len(result.vectors) == 2
    assert result.vectors[0] == [0.1, 0.2, 0.3, 0.4]
    assert result.provider == "openai"


# ── Local / Ollama ────────────────────────────────────────────────────────────


def _local_provider():
    from newskoo.llm.local_provider import LocalProvider

    return LocalProvider(_SETTINGS)


@respx.mock
async def test_local_registers_and_chat() -> None:
    import newskoo.llm.local_provider  # noqa: F401 - triggers registration

    assert "local" in _BUILDERS

    respx.post("http://ollama.test:11434/api/chat").mock(
        return_value=httpx.Response(
            200,
            json={
                "model": "bge-m3",
                "message": {"role": "assistant", "content": "local reply"},
                "prompt_eval_count": 11,
                "eval_count": 6,
                "done_reason": "stop",
            },
        )
    )
    provider = _local_provider()
    resp = await provider.chat([ChatMessage(role=Role.USER, content="Hi")])
    assert resp.text == "local reply"
    assert resp.input_tokens == 11
    assert resp.output_tokens == 6
    assert resp.provider == "local"


@respx.mock
async def test_local_extract_json_mode() -> None:
    route = respx.post("http://ollama.test:11434/api/chat").mock(
        return_value=httpx.Response(
            200,
            json={"model": "x", "message": {"content": '{"summary": "local-json"}'}},
        )
    )
    provider = _local_provider()
    result = await provider.extract([ChatMessage(role=Role.USER, content="Sum")], _SCHEMA)
    assert result == {"summary": "local-json"}
    sent = route.calls.last.request
    assert b'"format":"json"' in sent.content


@respx.mock
async def test_local_embed_batch_endpoint() -> None:
    respx.post("http://ollama.test:11434/api/embed").mock(
        return_value=httpx.Response(
            200,
            json={"model": "bge-m3", "embeddings": [[0.0, 1.0, 2.0, 3.0], [4.0, 5.0, 6.0, 7.0]]},
        )
    )
    provider = _local_provider()
    result = await provider.embed(["a", "b"])
    assert result.dim == 4
    assert len(result.vectors) == 2
    assert result.vectors[1] == [4.0, 5.0, 6.0, 7.0]


@respx.mock
async def test_local_embed_falls_back_to_legacy_endpoint() -> None:
    respx.post("http://ollama.test:11434/api/embed").mock(
        return_value=httpx.Response(404)
    )
    respx.post("http://ollama.test:11434/api/embeddings").mock(
        return_value=httpx.Response(200, json={"embedding": [9.0, 8.0, 7.0, 6.0]})
    )
    provider = _local_provider()
    result = await provider.embed(["only-one"])
    assert result.vectors == [[9.0, 8.0, 7.0, 6.0]]
    assert result.dim == 4


# ── missing-SDK error surfacing ───────────────────────────────────────────────


async def test_anthropic_missing_sdk_raises_clear_error(monkeypatch: pytest.MonkeyPatch) -> None:
    from newskoo.llm import anthropic_provider

    def _boom() -> None:
        raise ImportError("anthropic not installed")

    monkeypatch.setattr(anthropic_provider, "_import_async_anthropic", _boom)
    provider = anthropic_provider.AnthropicProvider(_SETTINGS)
    with pytest.raises(ImportError, match="anthropic"):
        await provider.chat([ChatMessage(role=Role.USER, content="Hi")])
