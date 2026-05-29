"""Async Kafka topic management (aiokafka admin).

Creates and lists the NewsKoo pipeline topics (see :data:`contracts.ALL_TOPICS`)
with the partition count / replication factor from settings. Idempotent:
topics that already exist are treated as success.

Run as a one-shot provisioning step::

    python -m newskoo.core.topics
"""

from __future__ import annotations

import asyncio

from aiokafka.admin import AIOKafkaAdminClient, NewTopic
from aiokafka.errors import TopicAlreadyExistsError

from newskoo.core.config import get_settings
from newskoo.core.contracts import ALL_TOPICS
from newskoo.core.logging import get_logger

log = get_logger(__name__)


async def create_topics(bootstrap_servers: str | None = None) -> list[str]:
    """Create every topic in :data:`ALL_TOPICS` (incl. the dead-letter topic).

    Each topic is created with ``kafka_num_partitions`` partitions and
    ``kafka_replication_factor`` replicas. The call is idempotent: a topic that
    already exists is logged and counted as created.

    Returns the sorted list of topic names that now exist (created or
    pre-existing).
    """
    settings = get_settings()
    servers = bootstrap_servers or settings.kafka_bootstrap_servers

    client = AIOKafkaAdminClient(
        bootstrap_servers=servers,
        client_id=settings.kafka_client_id,
    )
    await client.start()
    try:
        new_topics = [
            NewTopic(
                name=str(topic),
                num_partitions=settings.kafka_num_partitions,
                replication_factor=settings.kafka_replication_factor,
            )
            for topic in ALL_TOPICS
        ]
        ensured: list[str] = []
        for new_topic in new_topics:
            try:
                await client.create_topics([new_topic])
                log.info(
                    "topic.created",
                    topic=new_topic.name,
                    partitions=new_topic.num_partitions,
                    replication=new_topic.replication_factor,
                )
            except TopicAlreadyExistsError:
                log.info("topic.exists", topic=new_topic.name)
            ensured.append(new_topic.name)
        return sorted(ensured)
    finally:
        await client.close()


async def list_topics(bootstrap_servers: str | None = None) -> list[str]:
    """Return the sorted list of topic names currently known to the cluster."""
    settings = get_settings()
    servers = bootstrap_servers or settings.kafka_bootstrap_servers

    client = AIOKafkaAdminClient(
        bootstrap_servers=servers,
        client_id=settings.kafka_client_id,
    )
    await client.start()
    try:
        topics = await client.list_topics()
        return sorted(topics)
    finally:
        await client.close()


async def _main() -> None:
    created = await create_topics()
    existing = await list_topics()
    log.info("topics.provisioned", ensured=created, cluster_topics=existing)
    for name in created:
        print(name)


if __name__ == "__main__":
    asyncio.run(_main())
