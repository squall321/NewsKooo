"""Provider registry + factory. Backends register a builder under a name; the
configured provider is constructed lazily via :func:`get_provider`."""

from __future__ import annotations

from collections.abc import Callable

from newskoo.core.config import Settings, get_settings
from newskoo.llm.base import LLMProvider

_BUILDERS: dict[str, Callable[[Settings], LLMProvider]] = {}
_CACHE: dict[str, LLMProvider] = {}


def register_provider(name: str, builder: Callable[[Settings], LLMProvider]) -> None:
    _BUILDERS[name] = builder


def get_provider(name: str | None = None) -> LLMProvider:
    settings = get_settings()
    key = name or settings.llm_provider
    if key in _CACHE:
        return _CACHE[key]
    # Lazy-import built-in backends on first use to avoid hard dependencies.
    if key not in _BUILDERS:
        _load_builtin(key)
    if key not in _BUILDERS:
        raise ValueError(f"Unknown LLM provider: {key!r}. Registered: {list(_BUILDERS)}")
    provider = _BUILDERS[key](settings)
    _CACHE[key] = provider
    return provider


def _load_builtin(key: str) -> None:
    try:
        if key == "anthropic":
            from newskoo.llm import anthropic_provider  # noqa: F401
        elif key == "openai":
            from newskoo.llm import openai_provider  # noqa: F401
        elif key == "local":
            from newskoo.llm import local_provider  # noqa: F401
    except ImportError:
        # Backend optional dependency not installed; surfaced by get_provider.
        pass
