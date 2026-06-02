# NewsKoo convenience targets (run on Linux / WSL). See docs/LIVE_INTEGRATION.md.
.PHONY: help up workers down down-all integrate test lint typecheck coverage harvest seed topics migrate

help:
	@echo "NewsKoo make targets:"
	@echo "  make up         - bring up infra + migrate + seed (no workers)"
	@echo "  make workers    - up + start the worker fleet + API"
	@echo "  make down       - stop workers + API"
	@echo "  make down-all   - stop workers + API + services"
	@echo "  make integrate  - one-shot live integration check (services->smoke->tests)"
	@echo "  make test       - backend unit tests"
	@echo "  make lint       - ruff check"
	@echo "  make coverage   - probe live source coverage"
	@echo "  make harvest    - collect a real-data sample (no DB needed)"

up:
	bash infra/scripts/up.sh

workers:
	WORKERS=1 bash infra/scripts/up.sh

down:
	bash infra/scripts/down.sh

down-all:
	bash infra/scripts/down.sh --all

integrate:
	bash infra/scripts/live-integration.sh

test:
	cd backend && uv run pytest -q

lint:
	cd backend && uv run ruff check .

typecheck:
	cd backend && uv run mypy newskoo || true

coverage:
	cd backend && uv run python -m newskoo.sources.validate --json coverage.json

harvest:
	cd backend && uv run python -m newskoo.harvest --limit-sources 40 --per-feed 5 --out data/harvest_sample.jsonl

migrate:
	cd backend && uv run alembic upgrade head

topics:
	cd backend && uv run python -m newskoo.core.topics

seed:
	cd backend && uv run python -m newskoo.sources.seed_cli && uv run python -m newskoo.signals.cli seed
