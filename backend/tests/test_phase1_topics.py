"""Phase-1 tests: async Kafka topic management.

No live Kafka broker is required — ``AIOKafkaAdminClient`` is replaced with an
in-memory fake that records the topics requested and can simulate the
"already exists" race.
"""

from __future__ import annotations

from typing import ClassVar

import pytest
from newskoo.core import topics as topics_mod
from newskoo.core.config import get_settings
from newskoo.core.contracts import ALL_TOPICS

try:
    from aiokafka.errors import TopicAlreadyExistsError
except ImportError:  # pragma: no cover - fallback if aiokafka layout differs
    class TopicAlreadyExistsError(Exception):  # type: ignore[no-redef]
        pass


class FakeAdminClient:
    """Records create/list calls without touching a broker.

    Set ``raise_exists`` to make every ``create_topics`` call raise
    ``TopicAlreadyExistsError`` (simulating pre-existing topics).
    """

    instances: ClassVar[list[FakeAdminClient]] = []
    raise_exists = False

    def __init__(self, **kwargs: object) -> None:
        self.kwargs = kwargs
        self.started = False
        self.closed = False
        self.requested: list[str] = []
        FakeAdminClient.instances.append(self)

    async def start(self) -> None:
        self.started = True

    async def close(self) -> None:
        self.closed = True

    async def create_topics(self, new_topics: list[object]) -> None:
        for nt in new_topics:
            self.requested.append(nt.name)  # type: ignore[attr-defined]
        if FakeAdminClient.raise_exists:
            raise TopicAlreadyExistsError("already exists")

    async def list_topics(self) -> list[str]:
        return list(self.requested)


@pytest.fixture(autouse=True)
def _patch_admin(monkeypatch: pytest.MonkeyPatch) -> None:
    FakeAdminClient.instances = []
    FakeAdminClient.raise_exists = False
    # Ensure the error type used inside the module matches what the fake raises.
    monkeypatch.setattr(topics_mod, "TopicAlreadyExistsError", TopicAlreadyExistsError)
    monkeypatch.setattr(topics_mod, "AIOKafkaAdminClient", FakeAdminClient)


async def test_create_topics_requests_all_topics() -> None:
    created = await topics_mod.create_topics()

    expected = {str(t) for t in ALL_TOPICS}
    assert set(created) == expected

    client = FakeAdminClient.instances[-1]
    assert set(client.requested) == expected
    assert client.started and client.closed


async def test_create_topics_uses_settings_partitions_and_replication(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: list[tuple[int, int]] = []
    real_new_topic = topics_mod.NewTopic

    def _spy_new_topic(*args: object, **kwargs: object) -> object:
        nt = real_new_topic(*args, **kwargs)
        captured.append((nt.num_partitions, nt.replication_factor))
        return nt

    monkeypatch.setattr(topics_mod, "NewTopic", _spy_new_topic)

    settings = get_settings()
    await topics_mod.create_topics()

    assert captured, "no NewTopic objects were constructed"
    for partitions, replication in captured:
        assert partitions == settings.kafka_num_partitions
        assert replication == settings.kafka_replication_factor


async def test_create_topics_swallows_already_exists() -> None:
    FakeAdminClient.raise_exists = True

    # Must not raise, and must still report every topic as ensured.
    created = await topics_mod.create_topics()

    assert set(created) == {str(t) for t in ALL_TOPICS}
    client = FakeAdminClient.instances[-1]
    assert client.closed  # client cleaned up even on the exists path


async def test_create_topics_honors_explicit_bootstrap() -> None:
    await topics_mod.create_topics(bootstrap_servers="broker-1:9092")

    client = FakeAdminClient.instances[-1]
    assert client.kwargs.get("bootstrap_servers") == "broker-1:9092"


async def test_list_topics_returns_sorted() -> None:
    # Seed a fake cluster by creating topics first, then list.
    await topics_mod.create_topics()
    listed = await topics_mod.list_topics()
    assert listed == sorted(listed)


async def test_dead_letter_topic_included() -> None:
    created = await topics_mod.create_topics()
    assert "dead.letter" in created
