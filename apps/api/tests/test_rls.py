"""Row Level Security is exercised with the real runtime role (not the table owner)."""

from collections.abc import Iterator
from uuid import UUID, uuid4

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.exc import DBAPIError, ProgrammingError
from sqlalchemy.orm import Session

from app.db.models import AuditLog, User
from app.db.session import RLS_USER_KEY, make_sessionmaker
from tests.conftest import APP_URL


@pytest.fixture
def app_session(clean_db: None) -> Iterator[Session]:
    engine = create_engine(APP_URL)
    session = make_sessionmaker(engine)()
    yield session
    session.close()
    engine.dispose()


def _as(session: Session, user_id: UUID | None) -> None:
    session.rollback()
    session.info[RLS_USER_KEY] = user_id


def _seed(session: Session, user_id: UUID) -> None:
    _as(session, user_id)
    session.add(User(id=user_id, email=f"{user_id}@example.test"))
    session.flush()
    session.add(AuditLog(user_id=user_id, action="test.event"))
    session.commit()


def test_user_sees_only_own_rows(app_session: Session) -> None:
    a, b = uuid4(), uuid4()
    _seed(app_session, a)
    _seed(app_session, b)

    _as(app_session, a)
    assert [u.id for u in app_session.query(User).all()] == [a]
    assert {log.user_id for log in app_session.query(AuditLog).all()} == {a}


def test_no_identity_sees_nothing(app_session: Session) -> None:
    _seed(app_session, uuid4())
    _as(app_session, None)
    assert app_session.query(User).count() == 0
    assert app_session.query(AuditLog).count() == 0


def test_cannot_insert_row_for_another_user(app_session: Session) -> None:
    a, b = uuid4(), uuid4()
    _seed(app_session, b)
    _as(app_session, a)
    app_session.add(User(id=a))
    app_session.flush()
    app_session.add(AuditLog(user_id=b, action="forged"))
    with pytest.raises(DBAPIError):
        app_session.flush()


def test_cannot_update_another_users_row(app_session: Session) -> None:
    a, b = uuid4(), uuid4()
    _seed(app_session, a)
    _seed(app_session, b)
    _as(app_session, a)
    result = app_session.execute(
        text("UPDATE users SET email = 'hacked@example.test' WHERE id = :b"), {"b": b}
    )
    assert result.rowcount == 0


def test_audit_log_is_append_only(app_session: Session) -> None:
    a = uuid4()
    _seed(app_session, a)
    _as(app_session, a)
    with pytest.raises(ProgrammingError):
        app_session.execute(text("UPDATE audit_logs SET action = 'x'"))
    app_session.rollback()
    _as(app_session, a)
    with pytest.raises(ProgrammingError):
        app_session.execute(text("DELETE FROM audit_logs"))


def test_identity_does_not_leak_across_transactions(app_session: Session) -> None:
    a = uuid4()
    _seed(app_session, a)
    _as(app_session, None)
    value = app_session.execute(text("SELECT app_current_user_id()")).scalar_one()
    assert value is None
