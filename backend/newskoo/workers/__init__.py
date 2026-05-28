"""Kafka consumer workers + APScheduler jobs. Each stage runs as a consumer
group: parser, dedup/persist, analyzer, issue-detector. Entrypoints live here."""
