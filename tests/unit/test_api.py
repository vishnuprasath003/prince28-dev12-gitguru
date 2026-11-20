import pytest
from pydantic import ValidationError

from gitguru.config import Settings


def test_app_env_is_required():
    with pytest.raises(ValidationError):
        Settings(_env_file=None)


def test_health_is_ok(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"
    assert r.json()["app"] == "gitguru"
    assert r.json()["version"] == "dev"


def test_health_returns_environment_and_version(client):
    r = client.get("/health")
    data = r.json()
    assert data["env"] == "ci"
    assert data["version"] == "dev"


def test_ready(client):
    r = client.get("/ready")
    assert r.status_code == 200
    assert r.json() == {"status": "ready", "checks": {"database": True}}


def test_ready_when_database_down(client, db_state):
    db_state["up"] = False
    r = client.get("/ready")
    assert r.status_code == 503


def test_list_documents(client):
    r = client.get("/v1/documents/")
    assert r.status_code == 200
    assert r.json()["total"] == 3


def test_list_returns_documents(client):
    data = client.get("/v1/documents/").json()
    assert len(data["documents"]) == 3


def test_limit(client):
    r = client.get("/v1/documents/?limit=2")
    assert len(r.json()["documents"]) == 2


def test_offset(client):
    r = client.get("/v1/documents/?offset=1")
    assert len(r.json()["documents"]) == 2


def test_search_query(client):
    r = client.get("/v1/documents/?q=Alpha")
    assert r.json()["total"] == 1


def test_filter_kind(client):
    r = client.get("/v1/documents/?kind=circular")
    assert r.json()["total"] == 2


def test_filter_year(client):
    r = client.get("/v1/documents/?year=2023")
    assert r.json()["total"] == 1


def test_multiple_filters(client):
    r = client.get("/v1/documents/?year=2024&kind=circular")
    assert r.json()["total"] == 1


def test_invalid_filter_name(client):
    r = client.get("/v1/documents/?Bad-Name=1")
    assert r.status_code == 400


def test_limit_too_large(client):
    r = client.get("/v1/documents/?limit=101")
    assert r.status_code == 422


def test_negative_offset(client):
    r = client.get("/v1/documents/?offset=-1")
    assert r.status_code == 422


def test_filters_are_returned(client):
    r = client.get("/v1/documents/?kind=circular")
    assert r.json()["filters"] == {"kind": "circular"}
