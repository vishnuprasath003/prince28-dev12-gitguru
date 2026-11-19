"""Integration tests: a REAL Postgres, and a brand-new database for every test run."""

import asyncio
import os
import uuid

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import text
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import create_async_engine

from gitguru.config import get_settings
from gitguru.db.url import to_asyncpg_url

BASE_URL = os.getenv("TEST_DATABASE_URL")


def pytest_collection_modifyitems(config, items):
    if BASE_URL:
        return
    skip = pytest.mark.skip(reason="set TEST_DATABASE_URL to run integration tests")
    for item in items:
        if "integration" in item.nodeid:
            item.add_marker(skip)


async def _admin(sql: str) -> None:
    engine = create_async_engine(
        to_asyncpg_url(BASE_URL),
        isolation_level="AUTOCOMMIT",
    )
    try:
        async with engine.connect() as conn:
            await conn.execute(text(sql))
    finally:
        await engine.dispose()


@pytest.fixture(scope="session")
def database_url():
    """Create a test database, run migrations, and drop it afterward."""
    name = f"test_{uuid.uuid4().hex[:8]}"
    url = make_url(to_asyncpg_url(BASE_URL)).set(database=name)
    url_str = url.render_as_string(hide_password=False)

    try:
        asyncio.run(_admin(f'CREATE DATABASE "{name}"'))

        patch = pytest.MonkeyPatch()
        try:
            patch.setenv("APP_ENV", "ci")
            patch.setenv("DATABASE_URL", url_str)
            get_settings.cache_clear()
            command.upgrade(Config("alembic.ini"), "head")
        finally:
            patch.undo()
            get_settings.cache_clear()

        yield url_str
    finally:
        asyncio.run(_admin(f'DROP DATABASE IF EXISTS "{name}" WITH (FORCE)'))
