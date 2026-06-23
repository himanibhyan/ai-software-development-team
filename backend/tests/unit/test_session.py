from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db_session


@pytest.mark.asyncio
class TestGetDbSession:
    async def test_success_path_yields_and_commits(self):
        mock_session = AsyncMock(spec=AsyncSession)
        mock_cm = AsyncMock(__aenter__=AsyncMock(return_value=mock_session), __aexit__=AsyncMock(return_value=None))
        mock_factory = MagicMock(return_value=mock_cm)

        with patch("app.db.session.async_session_factory", mock_factory):
            gen = get_db_session()
            session = await gen.__anext__()
            assert session is mock_session
            with pytest.raises(StopAsyncIteration):
                await gen.__anext__()

        mock_session.commit.assert_awaited_once()
        mock_session.close.assert_awaited_once()

    async def test_rollback_on_exception_and_re_raises(self):
        mock_session = AsyncMock(spec=AsyncSession)
        mock_cm = AsyncMock(__aenter__=AsyncMock(return_value=mock_session), __aexit__=AsyncMock(return_value=None))
        mock_factory = MagicMock(return_value=mock_cm)

        with patch("app.db.session.async_session_factory", mock_factory):
            gen = get_db_session()
            session = await gen.__anext__()
            assert session is mock_session

            with pytest.raises(RuntimeError, match="db error"):
                await gen.athrow(RuntimeError("db error"))

        mock_session.commit.assert_not_awaited()
        mock_session.rollback.assert_awaited_once()
        mock_session.close.assert_awaited_once()
