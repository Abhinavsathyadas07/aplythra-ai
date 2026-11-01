from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.core.auth import AuthenticatedUser
from app.db.models import AuditLog, User
from app.deps import current_user, get_db

router = APIRouter(tags=["me"])


class MeResponse(BaseModel):
    id: UUID
    email: str | None
    created_at: datetime


@router.get("/me", response_model=MeResponse)
def read_me(user: AuthenticatedUser = Depends(current_user), db: Session = Depends(get_db)) -> User:
    """Return the caller's profile, creating it on first sign-in (idempotent)."""
    created = db.execute(
        insert(User)
        .values(id=user.id, email=user.email)
        .on_conflict_do_nothing(index_elements=[User.id])
        .returning(User.id)
    ).first()
    if created:
        db.add(AuditLog(user_id=user.id, action="user.created", entity_type="user"))
    db.commit()
    return db.get_one(User, user.id)
