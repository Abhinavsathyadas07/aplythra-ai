"""Engine/session helpers. RLS identity is applied per transaction, never per connection."""

from uuid import UUID

from sqlalchemy import Connection, Engine, create_engine, event, text
from sqlalchemy.orm import Session, SessionTransaction, sessionmaker

RLS_USER_KEY = "rls_user_id"
_SET_CLAIM = text("SELECT set_config('request.jwt.claim.sub', :uid, true)")


def make_engine(url: str) -> Engine:
    return create_engine(url, pool_pre_ping=True, pool_size=5, max_overflow=5)


def make_sessionmaker(engine: Engine) -> sessionmaker[Session]:
    return sessionmaker(engine, expire_on_commit=False)


@event.listens_for(Session, "after_begin")
def _apply_rls_claim(session: Session, _tx: SessionTransaction, connection: Connection) -> None:
    """Re-apply the authenticated user at the start of every transaction (set_config is local)."""
    user_id: UUID | None = session.info.get(RLS_USER_KEY)
    connection.execute(_SET_CLAIM, {"uid": str(user_id) if user_id else ""})
