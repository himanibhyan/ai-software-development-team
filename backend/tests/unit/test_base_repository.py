from __future__ import annotations

from uuid import uuid4

import pytest
import pytest_asyncio
from sqlalchemy import String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.db.repositories.base import BaseRepository


class _TestBase(DeclarativeBase):
    pass


class _TestModel(_TestBase):
    __tablename__ = "test_models"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    name: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")


class TestBaseRepository:
    @pytest_asyncio.fixture
    async def session(self):
        engine = create_async_engine("sqlite+aiosqlite://", echo=False)
        async with engine.begin() as conn:
            await conn.run_sync(_TestBase.metadata.create_all)

        factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        async with factory() as s:
            yield s

        async with engine.begin() as conn:
            await conn.run_sync(_TestBase.metadata.drop_all)
        await engine.dispose()

    @pytest_asyncio.fixture
    async def repo(self, session: AsyncSession) -> BaseRepository[_TestModel]:
        return BaseRepository(_TestModel, session)

    @pytest_asyncio.fixture
    async def seeded(self, session: AsyncSession) -> _TestModel:
        obj = _TestModel(name="seed", status="active")
        session.add(obj)
        await session.flush()
        return obj

    async def test_create(self, repo: BaseRepository[_TestModel]):
        instance = await repo.create(name="test", status="active")
        assert instance.id is not None
        assert instance.name == "test"
        assert instance.status == "active"

    async def test_get_found(self, repo: BaseRepository[_TestModel], seeded: _TestModel):
        instance = await repo.get(seeded.id)
        assert instance is not None
        assert instance.id == seeded.id
        assert instance.name == "seed"

    async def test_get_not_found(self, repo: BaseRepository[_TestModel]):
        instance = await repo.get(str(uuid4()))
        assert instance is None

    async def test_list_all(self, repo: BaseRepository[_TestModel], session: AsyncSession):
        for i in range(3):
            session.add(_TestModel(name=f"item_{i}", status="active"))
        await session.flush()

        results = await repo.list()
        assert len(results) == 3

    async def test_list_with_filter(self, repo: BaseRepository[_TestModel], session: AsyncSession):
        session.add(_TestModel(name="a", status="active"))
        session.add(_TestModel(name="b", status="inactive"))
        await session.flush()

        results = await repo.list(status="active")
        assert len(results) == 1
        assert results[0].name == "a"

    async def test_list_with_skip_limit(self, repo: BaseRepository[_TestModel], session: AsyncSession):
        for i in range(10):
            session.add(_TestModel(name=f"item_{i}", status="active"))
        await session.flush()

        results = await repo.list(skip=3, limit=4)
        assert len(results) == 4

    async def test_list_ignores_unrecognized_filter(self, repo: BaseRepository[_TestModel], session: AsyncSession):
        session.add(_TestModel(name="x", status="active"))
        await session.flush()

        results = await repo.list(nonexistent="value")
        assert len(results) == 1

    async def test_count_all(self, repo: BaseRepository[_TestModel], session: AsyncSession):
        for i in range(5):
            session.add(_TestModel(name=f"n_{i}", status="active"))
        await session.flush()

        count = await repo.count()
        assert count == 5

    async def test_count_with_filter(self, repo: BaseRepository[_TestModel], session: AsyncSession):
        session.add(_TestModel(name="a", status="active"))
        session.add(_TestModel(name="b", status="inactive"))
        session.add(_TestModel(name="c", status="inactive"))
        await session.flush()

        count = await repo.count(status="inactive")
        assert count == 2

    async def test_count_ignores_unrecognized_filter(self, repo: BaseRepository[_TestModel], session: AsyncSession):
        session.add(_TestModel(name="x", status="active"))
        await session.flush()

        count = await repo.count(fake="val")
        assert count == 1

    async def test_update_found(self, repo: BaseRepository[_TestModel], seeded: _TestModel):
        updated = await repo.update(seeded.id, name="updated")
        assert updated is not None
        assert updated.name == "updated"

    async def test_update_not_found(self, repo: BaseRepository[_TestModel]):
        updated = await repo.update(str(uuid4()), name="ghost")
        assert updated is None

    async def test_update_ignores_unrecognized_fields(self, repo: BaseRepository[_TestModel], seeded: _TestModel):
        updated = await repo.update(seeded.id, name="changed", fake_field="ignored")
        assert updated is not None
        assert updated.name == "changed"

    async def test_delete_found(self, repo: BaseRepository[_TestModel], seeded: _TestModel):
        result = await repo.delete(seeded.id)
        assert result is True

        found = await repo.get(seeded.id)
        assert found is None

    async def test_delete_not_found(self, repo: BaseRepository[_TestModel]):
        result = await repo.delete(str(uuid4()))
        assert result is False
