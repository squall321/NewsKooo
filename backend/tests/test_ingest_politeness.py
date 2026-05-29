"""Politeness-engine tests: token-bucket gating (fake limiter), robots.txt
allow/deny (respx-mocked), UA rotation, and round-robin interleave order.

No live Redis / network: a tiny in-memory fake stands in for ``RateLimiter`` and
``respx`` intercepts the robots.txt fetch.
"""

from __future__ import annotations

import httpx
import pytest
import respx
from newskoo.ingest.politeness import PolitenessEngine, domain_of


class FakeRateLimiter:
    """In-memory token bucket good enough for gating assertions.

    Mirrors ``RateLimiter.allow(domain, rate, capacity)``: each call consumes one
    token; tokens refill at ``rate`` per virtual-second advanced via ``tick()``.
    """

    def __init__(self, capacity: float = 1.0) -> None:
        self.capacity = capacity
        self.tokens: dict[str, float] = {}
        self.calls: list[str] = []

    async def allow(self, domain: str, rate: float, capacity: float = 1.0) -> bool:
        self.calls.append(domain)
        have = self.tokens.get(domain, capacity)
        if have >= 1.0:
            self.tokens[domain] = have - 1.0
            return True
        return False

    def refill(self, domain: str, amount: float) -> None:
        self.tokens[domain] = min(self.capacity, self.tokens.get(domain, 0.0) + amount)


def _engine(limiter: FakeRateLimiter) -> PolitenessEngine:
    # Inject the fake limiter and a no-op async sleep so tests never block.
    clock = {"t": 0.0}

    async def _sleep(_secs: float) -> None:
        clock["t"] += 30.0  # advance virtual time so acquire() can time out fast

    return PolitenessEngine(
        rate_limiter=limiter,  # type: ignore[arg-type]
        user_agents=["UA-A/1.0", "UA-B/1.0"],
        respect_robots=True,
        default_rps=1.0,
        clock=lambda: clock["t"],
        sleep=_sleep,
    )


def test_domain_of() -> None:
    assert domain_of("https://Example.com:8443/path?x=1") == "example.com"
    assert domain_of("not a url") == ""


def test_user_agent_rotation_cycles() -> None:
    eng = _engine(FakeRateLimiter())
    seq = [eng.next_user_agent() for _ in range(4)]
    assert seq == ["UA-A/1.0", "UA-B/1.0", "UA-A/1.0", "UA-B/1.0"]


async def test_acquire_allows_immediately_when_token_available() -> None:
    limiter = FakeRateLimiter(capacity=1.0)
    eng = _engine(limiter)
    await eng.acquire("a.com", rps=1.0)
    assert limiter.calls == ["a.com"]  # one bucket check, allowed first try


async def test_acquire_blocks_then_succeeds_after_refill() -> None:
    limiter = FakeRateLimiter(capacity=1.0)
    eng = _engine(limiter)
    await eng.acquire("a.com", rps=1.0)  # consumes the only token

    # Next acquire will be throttled until we refill; refill after first deny.
    original_allow = limiter.allow
    state = {"calls": 0}

    async def gated_allow(domain: str, rate: float, capacity: float = 1.0) -> bool:
        state["calls"] += 1
        if state["calls"] == 2:  # second overall call -> refill so it passes
            limiter.refill(domain, 1.0)
        return await original_allow(domain, rate, capacity)

    limiter.allow = gated_allow  # type: ignore[assignment]
    await eng.acquire("a.com", rps=1.0)
    assert state["calls"] >= 2  # was throttled at least once before succeeding


async def test_acquire_times_out_without_deadlock() -> None:
    limiter = FakeRateLimiter(capacity=1.0)
    eng = _engine(limiter)
    await eng.acquire("a.com", rps=1.0)  # drain
    # No refill ever happens; acquire must give up (virtual clock advances on sleep).
    await eng.acquire("a.com", rps=1.0)
    assert len(limiter.calls) > 1  # retried, then bailed out


@respx.mock
async def test_can_fetch_allows_and_denies_per_robots() -> None:
    robots = "User-agent: *\nDisallow: /private/\nAllow: /\n"
    respx.get("https://site.test/robots.txt").mock(
        return_value=httpx.Response(200, text=robots)
    )
    eng = _engine(FakeRateLimiter())
    assert await eng.can_fetch("https://site.test/news/article-1", "UA-A/1.0") is True
    assert await eng.can_fetch("https://site.test/private/secret", "UA-A/1.0") is False


@respx.mock
async def test_can_fetch_caches_robots_single_fetch() -> None:
    route = respx.get("https://cache.test/robots.txt").mock(
        return_value=httpx.Response(200, text="User-agent: *\nDisallow:\n")
    )
    eng = _engine(FakeRateLimiter())
    await eng.can_fetch("https://cache.test/a", "UA-A/1.0")
    await eng.can_fetch("https://cache.test/b", "UA-A/1.0")
    assert route.call_count == 1  # second lookup served from TTL cache


@respx.mock
async def test_can_fetch_fails_open_on_robots_error() -> None:
    respx.get("https://broken.test/robots.txt").mock(
        side_effect=httpx.ConnectError("boom")
    )
    eng = _engine(FakeRateLimiter())
    assert await eng.can_fetch("https://broken.test/anything", "UA-A/1.0") is True


async def test_can_fetch_bypassed_when_respect_robots_false() -> None:
    eng = _engine(FakeRateLimiter())
    eng.respect_robots = False
    # No respx mock registered; must not attempt a fetch.
    assert await eng.can_fetch("https://norobots.test/x", "UA-A/1.0") is True


def test_interleave_round_robin_order() -> None:
    urls_by_domain = {
        "a.com": ["a1", "a2", "a3"],
        "b.com": ["b1"],
        "c.com": ["c1", "c2"],
    }
    order = list(PolitenessEngine.interleave(urls_by_domain))
    # Round one: one from each domain in insertion order.
    assert order[:3] == ["a1", "b1", "c1"]
    # Round two: b.com exhausted, so a then c.
    assert order[3:5] == ["a2", "c2"]
    # Round three: only a.com remains.
    assert order[5:] == ["a3"]
    assert sorted(order) == ["a1", "a2", "a3", "b1", "c1", "c2"]


def test_interleave_empty() -> None:
    assert list(PolitenessEngine.interleave({})) == []
    assert list(PolitenessEngine.interleave({"a.com": []})) == []


async def test_stream_interleaved_acquires_per_url() -> None:
    limiter = FakeRateLimiter(capacity=10.0)
    eng = _engine(limiter)
    urls = {"a.com": ["https://a.com/1", "https://a.com/2"], "b.com": ["https://b.com/1"]}
    out = [u async for u in eng.stream_interleaved(urls, rps=10.0)]
    assert out == ["https://a.com/1", "https://b.com/1", "https://a.com/2"]
    # One bucket acquisition per URL, by domain.
    assert limiter.calls == ["a.com", "b.com", "a.com"]


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(pytest.main([__file__, "-q"]))
