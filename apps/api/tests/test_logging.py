import json
import logging

from fastapi.testclient import TestClient

from app.logging import JsonFormatter


def test_request_log_is_json_without_secrets(client: TestClient, caplog) -> None:  # type: ignore[no-untyped-def]
    caplog.set_level(logging.INFO, logger="app")
    client.get(
        "/health?email=private@example.test", headers={"Authorization": "Bearer abc.def.ghi"}
    )
    record = next(r for r in caplog.records if r.getMessage() == "request")
    line = JsonFormatter().format(record)
    data = json.loads(line)
    assert data["path"] == "/health"
    assert data["status"] == 200
    assert data["method"] == "GET"
    assert "duration_ms" in data
    assert "private@example.test" not in line
    assert "abc.def.ghi" not in line


def test_unhandled_exception_returns_generic_500() -> None:
    from fastapi import APIRouter

    from app.config import Settings
    from app.core.auth import JWTVerifier
    from app.main import create_app

    app = create_app(Settings(), JWTVerifier(lambda _t: None, "authenticated"))
    router = APIRouter()

    @router.get("/boom")
    def boom() -> None:
        raise RuntimeError("database password is hunter2")

    app.include_router(router)
    with TestClient(app, raise_server_exceptions=False) as client:
        response = client.get("/boom")
    assert response.status_code == 500
    assert "hunter2" not in response.text
    assert response.json()["detail"] == "Internal server error"
