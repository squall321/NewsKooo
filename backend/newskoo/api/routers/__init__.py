"""API routers (Phase 7).

Each module exposes an ``APIRouter`` named ``router``. ``main.create_app``
includes them under the ``/api`` prefix.
"""

from __future__ import annotations

from fastapi import Query

# Shared pagination query params reused across list endpoints.
LimitQuery = Query(default=50, ge=1, le=200, description="page size")
OffsetQuery = Query(default=0, ge=0, description="rows to skip")
