from fastapi import APIRouter, Request, Response, status
from sqlalchemy import text

router = APIRouter(tags=["health"])


@router.get("/health")
def liveness() -> dict[str, str]:
    """Process is up. Does not touch dependencies."""
    return {"status": "ok"}


@router.get("/health/ready")
def readiness(request: Request, response: Response) -> dict[str, str]:
    """Database reachable. Returns 503 otherwise; details stay in the logs."""
    try:
        with request.app.state.engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception:
        request.app.state.logger.exception("readiness check failed")
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {"status": "unavailable"}
    return {"status": "ok"}
