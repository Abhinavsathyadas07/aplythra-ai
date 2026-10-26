from collections.abc import Callable
from uuid import UUID, uuid4

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text

from app.db.session import RLS_USER_KEY, make_sessionmaker
from tests.conftest import APP_URL, auth


def _count(user_id: UUID, table: str, where: str = "true") -> int:
    """Count rows as the given user through the runtime role (RLS applies to everyone)."""
    engine = create_engine(APP_URL)
    session = make_sessionmaker(engine)()
    session.info[RLS_USER_KEY] = user_id
    try:
        return int(
            session.execute(
                text(f"SELECT count(*) FROM {table} WHERE {where}")  # noqa: S608 - test constants only
            ).scalar_one()
        )
    finally:
        session.close()
        engine.dispose()


def test_me_creates_user_once_and_audits(
    client: TestClient, make_token: Callable[..., str]
) -> None:
    user_id = uuid4()
    token = make_token(sub=user_id, email="a@example.test")

    first = client.get("/me", headers=auth(token))
    second = client.get("/me", headers=auth(token))

    assert first.status_code == second.status_code == 200
    assert first.json()["id"] == str(user_id)
    assert first.json()["email"] == "a@example.test"
    assert first.json()["created_at"] == second.json()["created_at"]
    assert _count(user_id, "users") == 1
    assert _count(user_id, "audit_logs", "action = 'user.created'") == 1


def test_users_are_isolated(client: TestClient, make_token: Callable[..., str]) -> None:
    a, b = uuid4(), uuid4()
    client.get("/me", headers=auth(make_token(sub=a, email="a@example.test")))
    me_b = client.get("/me", headers=auth(make_token(sub=b, email="b@example.test"))).json()
    assert me_b["id"] == str(b)
    assert me_b["email"] == "b@example.test"
