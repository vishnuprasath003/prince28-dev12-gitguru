import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from gitguru.api.main import app
from gitguru.config import Settings

client = TestClient(app)


def test_app_env_is_required():
    with pytest.raises(ValidationError):
        Settings(_env_file=None)


def test_health():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_ready():
    response = client.get("/ready")

    assert response.status_code == 200
    assert response.json() == {"status": "ready"}


def test_get_all_documents():
    response = client.get("/v1/documents")

    assert response.status_code == 200
    assert len(response.json()) == 20


def test_get_document_by_valid_id():
    response = client.get("/v1/documents/1")

    assert response.status_code == 200
    assert response.json()["id"] == 1
    assert response.json()["command"] == "git init"


def test_get_document_not_found():
    response = client.get("/v1/documents/999")

    assert response.status_code == 404


def test_problem_details_format():
    response = client.get("/v1/documents/999")

    data = response.json()

    assert response.status_code == 404
    assert data["type"] == "about:blank"
    assert data["title"] == "Not Found"
    assert data["status"] == 404
    assert data["detail"] == "Document not found"


def test_request_id_header():
    response = client.get("/health")

    assert response.status_code == 200
    assert "X-Request-ID" in response.headers
