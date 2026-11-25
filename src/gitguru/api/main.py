"""App factory: build a fully wired FastAPI app from settings."""

import logging
from contextlib import asynccontextmanager

from fastapi import APIRouter, FastAPI

from gitguru.api.errors import register_error_handlers
from gitguru.api.logging_config import configure_logging
from gitguru.api.middleware import request_context
from gitguru.api.routes import chat, documents, health
from gitguru.config import Settings, get_settings
from gitguru.db.llm_calls import make_recorder
from gitguru.db.session import make_engine, make_sessionmaker
from gitguru.llm.gateway import build_gateway

logger = logging.getLogger("gitguru")


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()

    configure_logging()

    engine = make_engine(settings)
    session_factory = make_sessionmaker(engine)

    recorder = make_recorder(session_factory)
    gateway = build_gateway(settings, recorder=recorder)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        logger.info("starting", extra={"status": settings.app_env})
        yield
        await engine.dispose()

    app = FastAPI(
        title="GitGuru",
        version="0.2.0",
        lifespan=lifespan,
    )

    # Application state
    app.state.settings = settings
    app.state.app_env = settings.app_env
    app.state.git_sha = "dev"
    app.state.engine = engine
    app.state.sessionmaker = session_factory
    app.state.gateway = gateway
    app.state.system_prompt = chat.load_prompt(settings.prompts_dir)

    # Middleware and error handlers
    app.middleware("http")(request_context)
    register_error_handlers(app)

    # Routes
    v1 = APIRouter(prefix="/v1")

    v1.include_router(documents.router)
    v1.include_router(chat.router)

    app.include_router(health.router)
    app.include_router(v1)

    return app


app = create_app()
