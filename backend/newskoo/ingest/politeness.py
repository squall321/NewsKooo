"""Politeness engine for Phase-3 ingestion.

Everything that touches the network funnels through :class:`PolitenessEngine`,
which enforces the project's "polite by default" crawling stance (ADR-0001):

* **Per-domain token-bucket rate limiting** backed by Redis
  (:class:`newskoo.core.redis.RateLimiter`). The rate (requests/sec) comes from
  the source's politeness policy, falling back to
  ``settings.crawler_default_rps_per_domain``.
* **Randomized jitter** sleeps between requests so traffic to a domain never
  looks metronomic.
* **User-agent rotation** across ``settings.crawler_user_agents``.
* **Optional egress proxy** via ``settings.crawler_proxy_url``.
* **robots.txt** fetching + TTL caching + ``can_fetch(url, ua)`` using the
  stdlib :mod:`urllib.robotparser`, honoring ``settings.crawler_respect_robots``.
* A **round-robin scheduler** (:meth:`interleave`) that yields URLs across many
  domains so no single site sees bursty traffic.
* A shared :class:`httpx.AsyncClient` factory (timeout / http2 / proxy / UA).

The engine is safe for concurrent use: the token bucket is atomic in Redis and
the robots cache is guarded by a per-domain :class:`asyncio.Lock`.
"""

from __future__ import annotations

import asyncio
import itertools
import random
import time
from collections import deque
from collections.abc import (
    AsyncIterator,
    Awaitable,
    Callable,
    Iterable,
    Iterator,
    Mapping,
)
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from urllib.parse import urlsplit
from urllib.robotparser import RobotFileParser

import httpx

from newskoo.core.config import get_settings
from newskoo.core.logging import get_logger
from newskoo.core.redis import RateLimiter

log = get_logger(__name__)

# How long a fetched robots.txt is trusted before re-fetching.
_ROBOTS_TTL_S = 3600.0
# Bound on how long acquire() will poll the token bucket before giving up.
_ACQUIRE_MAX_WAIT_S = 60.0


def domain_of(url: str) -> str:
    """Return the lowercased host of ``url`` (without port), or ``""``."""
    host = urlsplit(url).hostname or ""
    return host.lower()


@dataclass(slots=True)
class _RobotsEntry:
    parser: RobotFileParser | None
    fetched_at: float


@dataclass(slots=True)
class PolitenessEngine:
    """Per-domain politeness coordinator (rate limit, robots, UA/proxy).

    Construct once per worker and share it across connectors. ``rate_limiter``
    and the monotonic ``clock`` are injectable for tests (no live Redis).
    """

    rate_limiter: RateLimiter | None = None
    user_agents: list[str] | None = None
    proxy_url: str | None = None
    respect_robots: bool | None = None
    default_rps: float | None = None
    timeout_s: float | None = None
    robots_ttl_s: float = _ROBOTS_TTL_S
    #: monotonic clock (overridable in tests).
    clock: Callable[[], float] | None = None
    #: async sleep (overridable in tests to avoid real waits).
    sleep: Callable[[float], Awaitable[None]] | None = None

    _ua_cycle: Iterator[str] = field(init=False, repr=False)
    _robots: dict[str, _RobotsEntry] = field(default_factory=dict, init=False, repr=False)
    _robots_locks: dict[str, asyncio.Lock] = field(
        default_factory=dict, init=False, repr=False
    )

    def __post_init__(self) -> None:
        settings = get_settings()
        if self.rate_limiter is None:
            self.rate_limiter = RateLimiter()
        if self.user_agents is None:
            self.user_agents = list(settings.crawler_user_agents)
        if not self.user_agents:
            self.user_agents = ["NewsKooBot/0.1"]
        if self.proxy_url is None:
            self.proxy_url = settings.crawler_proxy_url or None
        if self.respect_robots is None:
            self.respect_robots = settings.crawler_respect_robots
        if self.default_rps is None:
            self.default_rps = settings.crawler_default_rps_per_domain
        if self.timeout_s is None:
            self.timeout_s = settings.crawler_request_timeout_s
        if self.clock is None:
            self.clock = time.monotonic
        if self.sleep is None:
            self.sleep = asyncio.sleep
        self._ua_cycle = itertools.cycle(self.user_agents)

    # ── User-agent rotation ──────────────────────────────────────────────────
    def next_user_agent(self) -> str:
        """Return the next user-agent in the rotation."""
        return next(self._ua_cycle)

    # ── Rate limiting ────────────────────────────────────────────────────────
    async def acquire(self, domain: str, rps: float | None = None) -> None:
        """Block politely until a request to ``domain`` is allowed.

        Polls the Redis token bucket; on throttle, sleeps ~1/rps with jitter and
        retries. Gives up after ``_ACQUIRE_MAX_WAIT_S`` (logs and proceeds rather
        than deadlocking a collection cycle).
        """
        assert self.rate_limiter is not None and self.clock is not None
        rate = rps if rps and rps > 0 else (self.default_rps or 0.5)
        deadline = self.clock() + _ACQUIRE_MAX_WAIT_S
        # Allow a small burst so the very first request never waits a full period.
        capacity = max(1.0, rate)
        while True:
            allowed = await self.rate_limiter.allow(domain, rate, capacity)
            if allowed:
                return
            if self.clock() >= deadline:
                log.warning("politeness.acquire_timeout", domain=domain, rps=rate)
                return
            base = 1.0 / rate if rate > 0 else 1.0
            await self._jitter_sleep(base)

    async def _jitter_sleep(self, base_s: float) -> None:
        """Sleep ``base_s`` plus uniform jitter in ``[0, base_s/2]``."""
        assert self.sleep is not None
        jitter = random.uniform(0.0, max(0.0, base_s) / 2.0)
        await self.sleep(max(0.0, base_s) + jitter)

    async def jitter(self, base_s: float = 0.0) -> None:
        """Public polite delay used between requests inside a connector."""
        await self._jitter_sleep(base_s)

    # ── robots.txt ───────────────────────────────────────────────────────────
    def _robots_url(self, url: str) -> str:
        parts = urlsplit(url)
        scheme = parts.scheme or "https"
        return f"{scheme}://{parts.netloc}/robots.txt"

    def _lock_for(self, domain: str) -> asyncio.Lock:
        lock = self._robots_locks.get(domain)
        if lock is None:
            lock = asyncio.Lock()
            self._robots_locks[domain] = lock
        return lock

    async def _load_robots(
        self, url: str, client: httpx.AsyncClient | None
    ) -> RobotFileParser | None:
        """Fetch + cache the robots.txt covering ``url`` (TTL-bounded)."""
        assert self.clock is not None
        domain = domain_of(url)
        now = self.clock()
        cached = self._robots.get(domain)
        if cached is not None and (now - cached.fetched_at) < self.robots_ttl_s:
            return cached.parser

        async with self._lock_for(domain):
            cached = self._robots.get(domain)
            if cached is not None and (now - cached.fetched_at) < self.robots_ttl_s:
                return cached.parser

            robots_url = self._robots_url(url)
            parser: RobotFileParser | None = RobotFileParser()
            parser.set_url(robots_url)
            owned = client is None
            cli = client or self._build_client()
            try:
                resp = await cli.get(robots_url)
                if resp.status_code >= 400:
                    # 4xx/5xx: treat as "no restrictions" per common convention.
                    parser.parse([])
                else:
                    parser.parse(resp.text.splitlines())
            except httpx.HTTPError as exc:
                log.warning("robots.fetch_failed", domain=domain, error=str(exc))
                # On failure we fail-open (allow) but cache briefly via TTL.
                parser = None
            finally:
                if owned:
                    await cli.aclose()

            self._robots[domain] = _RobotsEntry(parser=parser, fetched_at=now)
            return parser

    async def can_fetch(
        self, url: str, ua: str | None = None, *, client: httpx.AsyncClient | None = None
    ) -> bool:
        """Return whether ``ua`` may fetch ``url`` per robots.txt.

        Returns ``True`` immediately when ``respect_robots`` is disabled, and
        fails open (``True``) if robots.txt could not be fetched/parsed.
        """
        if not self.respect_robots:
            return True
        agent = ua or (self.user_agents[0] if self.user_agents else "*")
        parser = await self._load_robots(url, client)
        if parser is None:
            return True
        return parser.can_fetch(agent, url)

    # ── HTTP client factory ──────────────────────────────────────────────────
    def _build_client(self, *, ua: str | None = None) -> httpx.AsyncClient:
        headers = {"User-Agent": ua or self.next_user_agent()}
        kwargs: dict[str, object] = {
            "timeout": self.timeout_s,
            "follow_redirects": True,
            "http2": True,
            "headers": headers,
        }
        if self.proxy_url:
            kwargs["proxy"] = self.proxy_url
        return httpx.AsyncClient(**kwargs)  # type: ignore[arg-type]

    @asynccontextmanager
    async def client(
        self, *, ua: str | None = None, existing: httpx.AsyncClient | None = None
    ) -> AsyncIterator[httpx.AsyncClient]:
        """Yield a shared httpx client (caller's if provided, else a fresh one).

        Rotates the User-Agent header per acquisition when no ``ua`` is pinned.
        """
        if existing is not None:
            yield existing
            return
        cli = self._build_client(ua=ua)
        try:
            yield cli
        finally:
            await cli.aclose()

    # ── Round-robin scheduler ────────────────────────────────────────────────
    @staticmethod
    def interleave(urls_by_domain: Mapping[str, Iterable[str]]) -> Iterator[str]:
        """Yield URLs round-robin across domains.

        Given ``{"a.com": [u1, u2], "b.com": [u3]}`` yields ``u1, u3, u2`` so a
        single domain is never hit in a burst. Domain order follows insertion
        order of the mapping; exhausted domains drop out of the rotation.
        """
        queues: list[deque[str]] = [deque(urls) for urls in urls_by_domain.values()]
        queues = [q for q in queues if q]
        while queues:
            still_active: list[deque[str]] = []
            for q in queues:
                yield q.popleft()
                if q:
                    still_active.append(q)
            queues = still_active

    async def stream_interleaved(
        self, urls_by_domain: Mapping[str, Iterable[str]], rps: float | None = None
    ) -> AsyncIterator[str]:
        """Async variant of :meth:`interleave` that acquires a per-domain token
        before yielding each URL (so consumers can fetch immediately, politely).
        """
        for url in self.interleave(urls_by_domain):
            await self.acquire(domain_of(url), rps)
            yield url
