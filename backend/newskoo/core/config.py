"""Central application configuration (12-factor, env-driven).

Every service (api, workers, crawlers) imports ``get_settings()``. Override via
environment variables prefixed ``NEWSKOO_`` or a local ``.env`` file. See
``.env.example`` at the repo root for the full list.
"""

from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="NEWSKOO_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ── Environment ────────────────────────────────────────────────────────
    environment: str = "dev"  # dev | staging | prod
    log_level: str = "INFO"
    log_json: bool = False  # True in prod for structured logs

    # ── PostgreSQL ─────────────────────────────────────────────────────────
    postgres_dsn: str = "postgresql+asyncpg://newskoo:newskoo@localhost:5432/newskoo"
    # Sync DSN used by Alembic (psycopg). Derived if left blank.
    postgres_sync_dsn: str = ""
    db_pool_size: int = 10
    db_max_overflow: int = 20
    db_echo: bool = False

    # ── Kafka (KRaft, single or multi broker) ───────────────────────────────
    kafka_bootstrap_servers: str = "localhost:9092"
    kafka_client_id: str = "newskoo"
    kafka_consumer_group_prefix: str = "newskoo"
    kafka_num_partitions: int = 12
    kafka_replication_factor: int = 1

    # ── Redis (cache / rate-limit / seen-set) ────────────────────────────────
    redis_url: str = "redis://localhost:6379/0"

    # ── LLM (multi-provider abstraction) ─────────────────────────────────────
    llm_provider: str = "anthropic"  # anthropic | openai | local
    llm_model: str = "claude-sonnet-4-6"
    llm_max_tokens: int = 4096
    llm_temperature: float = 0.2
    embedding_provider: str = "local"  # anthropic has no embeddings; local|openai
    embedding_model: str = "bge-m3"
    embedding_dim: int = 1024  # MUST match the pgvector column dimension

    anthropic_api_key: str = ""
    openai_api_key: str = ""
    ollama_base_url: str = "http://localhost:11434"

    # ── Crawling / politeness ────────────────────────────────────────────────
    crawler_user_agents: list[str] = Field(
        default_factory=lambda: [
            "NewsKooBot/0.1 (+https://github.com/squall321/NewsKooo)",
        ]
    )
    crawler_default_rps_per_domain: float = 0.5  # requests/sec per domain (polite)
    crawler_max_concurrency: int = 16
    crawler_request_timeout_s: float = 20.0
    crawler_respect_robots: bool = True
    crawler_proxy_url: str = ""  # optional egress proxy

    # ── External news APIs ───────────────────────────────────────────────────
    newsapi_key: str = ""  # https://newsapi.org (optional; connector no-ops if empty)
    gdelt_enabled: bool = True  # GDELT 2.0 needs no key

    # ── Dedup / clustering / issue detection ─────────────────────────────────
    dedup_hamming_threshold: int = 3  # simhash distance <= this ⇒ near-duplicate
    cluster_similarity_threshold: float = 0.82  # cosine sim to join an event
    issue_zscore_threshold: float = 3.0  # mention z-score that fires an alert
    issue_window_minutes: int = 60  # time-series bucket size

    # ── API ───────────────────────────────────────────────────────────────────
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:5173"])
    api_key: str = ""  # if set, required via X-API-Key header

    @property
    def sync_dsn(self) -> str:
        """Synchronous DSN for Alembic; derive from async DSN if not set."""
        if self.postgres_sync_dsn:
            return self.postgres_sync_dsn
        return self.postgres_dsn.replace("+asyncpg", "+psycopg")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Cached settings singleton."""
    return Settings()
