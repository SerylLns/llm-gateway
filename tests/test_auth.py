import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_is_open():
    assert client.get("/health").status_code == 200


@pytest.mark.parametrize("token", [b"wrong-key", "test-master-kéy".encode(), b""])
def test_a_bad_token_is_rejected(token):
    response = client.post("/v1/ocr", headers={"Authorization": b"Bearer " + token}, json={"image": "x"})

    assert response.status_code == 401


@pytest.mark.parametrize("path", ["/docs", "/redoc", "/openapi.json"])
def test_the_api_docs_are_not_served_without_a_token(path):
    assert client.get(path).status_code == 401


@pytest.mark.parametrize("path", ["/docs", "/redoc", "/openapi.json"])
def test_the_api_docs_are_disabled(path):
    response = client.get(path, headers={"Authorization": "Bearer test-master-key"})

    assert response.status_code == 404
