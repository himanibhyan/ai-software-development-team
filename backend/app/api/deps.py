from __future__ import annotations

from typing import Annotated

from fastapi import Depends, HTTPException, Header, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import verify_api_key
from app.db.session import get_db_session

SessionDep = Annotated[AsyncSession, Depends(get_db_session)]


async def verify_api_key_header(x_api_key: str | None = Header(None)) -> None:
    """Dependency to verify API key for authenticated endpoints."""
    if x_api_key is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing API key",
        )
    if not verify_api_key(x_api_key):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
        )
