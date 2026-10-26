from collections.abc import Iterator

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.auth import AuthenticatedUser, AuthError, JWTVerifier
from app.db.session import RLS_USER_KEY

_bearer = HTTPBearer(auto_error=False)


def _unauthorized() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Not authenticated",
        headers={"WWW-Authenticate": "Bearer"},
    )


def current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> AuthenticatedUser:
    if credentials is None:
        raise _unauthorized()
    verifier: JWTVerifier = request.app.state.verifier
    try:
        return verifier.verify(credentials.credentials)
    except AuthError:
        raise _unauthorized() from None


def get_db(request: Request, user: AuthenticatedUser = Depends(current_user)) -> Iterator[Session]:
    """Session bound to the caller: RLS identity is applied at the start of every transaction.

    Handlers must commit explicitly; the session is closed (and rolled back) afterwards.
    """
    session: Session = request.app.state.sessionmaker()
    session.info[RLS_USER_KEY] = user.id
    try:
        yield session
    finally:
        session.close()
