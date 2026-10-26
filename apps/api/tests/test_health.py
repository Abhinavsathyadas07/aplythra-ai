from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app
from tests.conftest import AUDIENCE


def test_liveness(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_readiness_ok(client: TestClient) -> None:
    assert client.get("/health/ready").json() == {"status": "ok"}


def test_readiness_503_when_database_down() -> None:
    settings = Settings(
        database_url="postgresql+psycopg://nobody:x@127.0.0.1:1/none?connect_timeout=1",
        jwt_audience=AUDIENCE,
    )
    with TestClient(create_app(settings)) as client:
        response = client.get("/health/ready")
    assert response.status_code == 503
    assert response.json() == {"status": "unavailable"}
    assert "nobody" not in response.text


def test_request_id_is_generated_and_echoed(client: TestClient) -> None:
    generated = client.get("/health").headers["x-request-id"]
    assert len(generated) == 32
    assert (
        client.get("/health", headers={"X-Request-ID": "abc-12345678"}).headers["x-request-id"]
        == "abc-12345678"
    )
    # Unsafe ids are replaced, not echoed.
    assert (
        client.get("/health", headers={"X-Request-ID": "bad id\t!"}).headers["x-request-id"]
        != "bad id\t!"
    )
