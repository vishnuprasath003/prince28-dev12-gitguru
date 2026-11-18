import logging
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from starlette.exceptions import HTTPException as StarletteHTTPException

from gitguru.api.errors import http_exception_handler
from gitguru.api.logging_config import configure_logging, request_id_var
from gitguru.api.routes.documents import router as documents_router
from gitguru.api.routes.health import router as health_router
from gitguru.config import Settings
from gitguru.config import settings as default_settings
from gitguru.db.session import make_engine, make_sessionmaker

logger = logging.getLogger("gitguru")


def create_app(config: Settings | None = None) -> FastAPI:
    config = config or default_settings
    configure_logging()

    engine = make_engine(config)
    session_factory = make_sessionmaker(engine)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        yield
        await engine.dispose()

    app = FastAPI(title="GitGuru", lifespan=lifespan)
    app.state.app_env = config.app_env
    app.state.session_factory = session_factory

    app.add_exception_handler(StarletteHTTPException, http_exception_handler)

    @app.middleware("http")
    async def request_middleware(request: Request, call_next):
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        token = request_id_var.set(request_id)

        try:
            response = await call_next(request)
            response.headers["X-Request-ID"] = request_id
            logger.info(
                "%s %s - %s",
                request.method,
                request.url.path,
                response.status_code,
            )
            return response
        finally:
            request_id_var.reset(token)

    app.include_router(health_router)
    app.include_router(documents_router, prefix="/v1")

    return app


app = create_app()
