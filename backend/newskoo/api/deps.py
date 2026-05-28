"""Shared FastAPI dependencies: DB session + optional API-key auth."""

from __future__ import annotations

from collections.abc import AsyncIterator

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from newskoo.core.config import get_settings
from newskoo.core.db import get_session


async def db_session() -> AsyncIterator[AsyncSession]:
    async for s in get_session():
        yield s


async def require_api_key(x_api_key: str | None = Header(default=None)) -> None:
    configured = get_settings().api_key
    if configured and x_api_key != configured:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "invalid or missing API key")


SessionDep = Depends(db_session)
AuthDep = Depends(require_api_key)
