import hashlib
import json
import os
import subprocess
import sys

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from gitguru.api.main import create_app
from gitguru.config import Settings
from gitguru.db.models import Document
from gitguru.db.repository import DocumentRepository
from gitguru.db.session import make_engine, make_sessionmaker

ROWS = [
    {"title": "Alpha", "kind": "circular", "year": "2024", "tag": "b"},
    {"title": "Beta", "kind": "guideline", "year": "2025", "tag": "b"},
    {"title": "Gamma", "kind": "circular", "year": "2025", "tag": "a"},
]


@pytest.fixture
def settings(database_url):
    return Settings(app_env="ci", database_url=database_url, _env_file=None)


@pytest.fixture
async def seeded(settings):
    """Insert fresh test documents and return their database settings."""
    engine = make_engine(settings)

    async with make_sessionmaker(engine)() as session, session.begin():
        await session.execute(text("DELETE FROM documents"))

        for row in ROWS:
            session.add(
                Document(
                    title=row["title"],
                    sha256=hashlib.sha256(row["title"].encode()).hexdigest(),
                    metadata_={
                        "kind": row["kind"],
                        "year": row["year"],
                        "tag": row["tag"],
                    },
                )
            )

    await engine.dispose()
    return settings


async def test_migrations_created_the_tables(settings):
    engine = make_engine(settings)

    async with engine.connect() as conn:
        tables = set(
            await conn.scalars(
                text(
                    "SELECT table_name FROM information_schema.tables "
                    "WHERE table_schema='public'"
                )
            )
        )
        version = await conn.scalar(text("SELECT version_num FROM alembic_version"))

    await engine.dispose()

    assert {"documents", "pages", "alembic_version"} <= tables
    assert version


@pytest.mark.parametrize(
    ("filters", "expected"),
    [
        ({"kind": "circular"}, ["Alpha", "Gamma"]),
        ({"year": "2025"}, ["Beta", "Gamma"]),
        ({"tag": "b"}, ["Alpha", "Beta"]),
        ({"kind": "circular", "year": "2025"}, ["Gamma"]),
    ],
)
async def test_repository_filters(seeded, filters, expected):
    engine = make_engine(seeded)

    async with make_sessionmaker(engine)() as session:
        total, items = await DocumentRepository(session).list(
            q=None, filters=filters, limit=10, offset=0
        )

    await engine.dispose()

    assert [item["title"] for item in items] == expected
    assert total == len(expected)


def test_api_against_real_database(seeded):
    with TestClient(create_app(seeded)) as client:
        assert client.get("/ready").json()["checks"]["database"] is True

        response = client.get("/v1/documents/", params={"q": "gamm"})
        assert response.status_code == 200
        assert response.json()["total"] == 1
        assert response.json()["documents"][0]["title"] == "Gamma"


def test_loader_is_idempotent(database_url, tmp_path):
    data = tmp_path / "records.json"
    data.write_text(
        json.dumps([{"id": "L1", "x": 1}, {"id": "L2", "x": 2}]),
        encoding="utf-8",
    )

    env = {
        **os.environ,
        "APP_ENV": "ci",
        "DATABASE_URL": database_url,
        "DATA_FILE": str(data),
    }

    def run() -> str:
        cmd = [sys.executable, "scripts/load_db.py"]
        return subprocess.run(
            cmd, env=env, check=True, capture_output=True, text=True
        ).stdout

    assert "inserted=2" in run()
    assert "inserted=0 updated=0 unchanged=2" in run()
