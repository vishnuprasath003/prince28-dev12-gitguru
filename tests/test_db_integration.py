"""Integration tests against a real PostgreSQL test database."""

import os

import pytest
from fastapi.testclient import TestClient

from gitguru.api.main import create_app
from gitguru.config import Settings

TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL")

pytestmark = pytest.mark.skipif(
    not TEST_DATABASE_URL,
    reason="Set TEST_DATABASE_URL to run PostgreSQL integration tests",
)


@pytest.fixture
def db_client():
    settings = Settings(
        app_env="test",
        database_url=TEST_DATABASE_URL,
        _env_file=None,
    )
    app = create_app(settings)

    with TestClient(app) as client:
        yield client


def test_database_is_ready(db_client):
    response = db_client.get("/ready")

    assert response.status_code == 200
    assert response.json()["checks"]["database"] is True


def test_documents_endpoint_reads_postgres(db_client):
    response = db_client.get("/v1/documents/?limit=5")

    assert response.status_code == 200

    data = response.json()
    assert "total" in data
    assert "documents" in data
    assert isinstance(data["documents"], list)


def test_documents_support_metadata_filter(db_client):
    response = db_client.get("/v1/documents/?command=__integration_test_value__")

    assert response.status_code == 200
    assert response.json()["filters"] == {"command": "__integration_test_value__"}
