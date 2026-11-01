import logging
import re
import time
import uuid
from collections.abc import Awaitable, Callable

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import Settings, get_settings
from app.core.auth import JWTVerifier
from app.db.session import make_engine, make_sessionmaker
from app.logging import configure_logging, request_id_var
from app.routers import health, me

_REQUEST_ID_RE = re.compile(r"^[A-Za-z0-9._-]{8,64}$")
logger = logging.getLogger("app")


def create_app(settings: Settings | None = None, verifier: JWTVerifier | None = None) -> FastAPI:
    settings = settings or get_settings()
    configure_logging(settings.log_level)

    app = FastAPI(
        title="JobPilot AI API", docs_url=None if settings.app_env == "production" else "/docs"
    )
    engine = make_engine(settings.database_url)
    app.state.engine = engine
    app.state.sessionmaker = make_sessionmaker(engine)
    app.state.logger = logger
    app.state.verifier = verifier or JWTVerifier.from_jwks(
        settings.supabase_jwks_url or "http://invalid.local/jwks",
        settings.jwt_audience,
        settings.jwt_issuer,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
        allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
    )

    @app.middleware("http")
    async def request_context(
        request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        incoming = request.headers.get("x-request-id", "")
        request_id = incoming if _REQUEST_ID_RE.match(incoming) else uuid.uuid4().hex
        token = request_id_var.set(request_id)
        started = time.perf_counter()
        status_code = 500
        try:
            response = await call_next(request)
            status_code = response.status_code
            response.headers["X-Request-ID"] = request_id
            return response
        finally:
            # Path only: query strings may carry personal data.
            logger.info(
                "request",
                extra={
                    "method": request.method,
                    "path": request.url.path,
                    "status": status_code,
                    "duration_ms": round((time.perf_counter() - started) * 1000, 1),
                },
            )
            request_id_var.reset(token)

    @app.exception_handler(Exception)
    async def unhandled(_request: Request, exc: Exception) -> JSONResponse:
        logger.error("unhandled exception", exc_info=exc)
        return JSONResponse(
            {"detail": "Internal server error", "request_id": request_id_var.get()},
            status_code=500,
        )

    app.include_router(health.router)
    app.include_router(me.router)
    return app
