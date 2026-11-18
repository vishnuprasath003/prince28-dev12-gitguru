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


def test_health_content_type():
    response = client.get("/health")
    assert "application/json" in response.headers["content-type"]


def test_custom_request_id():
    response = client.get("/health", headers={"X-Request-ID": "test-request-123"})
    assert response.headers["X-Request-ID"] == "test-request-123"


def test_ready_content_type():
    response = client.get("/ready")
    assert "application/json" in response.headers["content-type"]


def test_documents_content_type():
    response = client.get("/v1/documents")
    assert "application/json" in response.headers["content-type"]


def test_documents_response_is_list():
    response = client.get("/v1/documents")
    assert isinstance(response.json(), list)


def test_document_has_required_fields():
    response = client.get("/v1/documents/1")
    data = response.json()
    assert {"id", "command", "topic", "source"} <= data.keys()


def test_invalid_document_id():
    response = client.get("/v1/documents/abc")
    assert response.status_code == 422


def test_document_id_is_integer():
    response = client.get("/v1/documents/1")
    assert isinstance(response.json()["id"], int)
