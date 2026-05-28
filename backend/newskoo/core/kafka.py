"""Async Kafka helpers (aiokafka): JSON producer/consumer factories and a
typed publish/consume convenience layer over the :mod:`contracts` payloads."""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import TypeVar

import orjson
from aiokafka import AIOKafkaConsumer, AIOKafkaProducer
from pydantic import BaseModel

from newskoo.core.config import get_settings
from newskoo.core.contracts import Topic

T = TypeVar("T", bound=BaseModel)


def _serialize(value: BaseModel) -> bytes:
    return orjson.dumps(value.model_dump(mode="json"))


async def make_producer() -> AIOKafkaProducer:
    s = get_settings()
    producer = AIOKafkaProducer(
        bootstrap_servers=s.kafka_bootstrap_servers,
        client_id=s.kafka_client_id,
        value_serializer=_serialize,
        enable_idempotence=True,
        acks="all",
        linger_ms=20,
    )
    await producer.start()
    return producer


async def make_consumer(*topics: Topic, group: str) -> AIOKafkaConsumer:
    s = get_settings()
    consumer = AIOKafkaConsumer(
        *[str(t) for t in topics],
        bootstrap_servers=s.kafka_bootstrap_servers,
        client_id=s.kafka_client_id,
        group_id=f"{s.kafka_consumer_group_prefix}.{group}",
        value_deserializer=orjson.loads,
        enable_auto_commit=False,
        auto_offset_reset="earliest",
        max_poll_records=200,
    )
    await consumer.start()
    return consumer


async def publish(producer: AIOKafkaProducer, topic: Topic, payload: BaseModel, *, key: str | None = None) -> None:
    await producer.send_and_wait(
        str(topic),
        payload,
        key=key.encode() if key else None,
    )


async def consume(
    consumer: AIOKafkaConsumer, model: type[T]
) -> AsyncIterator[tuple[T, object]]:
    """Yield ``(parsed_model, raw_message)``. Caller commits offsets after
    successful handling: ``await consumer.commit()``."""
    async for msg in consumer:
        yield model.model_validate(msg.value), msg
