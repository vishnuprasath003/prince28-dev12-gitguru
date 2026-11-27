"""App factory: build a fully wired FastAPI app from settings."""

import asyncio
import logging
from contextlib import asynccontextmanager, suppress

from fastapi import APIRouter, FastAPI

from gitguru.api.errors import register_error_handlers
from gitguru.api.middleware import request_context
from gitguru.api.routes import chat, documents, health, ingest
from gitguru.config import Settings, get_settings
from gitguru.db.llm_calls import make_recorder
from gitguru.db.session import make_engine, make_sessionmaker
from gitguru.llm.gateway import build_gateway
from gitguru.logging_setup import setup_logging

logger = logging.getLogger("gitguru")


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    setup_logging(settings.log_level)
    engine = make_engine(settings)  # no connection is opened yet

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        logger.info("starting", extra={"status": settings.app_env})

        worker = None

        if settings.worker_in_api:
            # No separate worker service here: run one in this process
            from gitguru.workers.main import run_embedded

            worker = asyncio.create_task(run_embedded(settings))

        yield

        if worker:
            worker.cancel()
            with suppress(asyncio.CancelledError):
                await worker

        if getattr(app.state, "queue", None):
            await app.state.queue.close()

        await engine.dispose()  # close every pooled connection on shutdown

    app = FastAPI(
        title=settings.app_name,
        version="0.2.0",
        lifespan=lifespan,
    )

    # Application state
    app.state.settings = settings
    app.state.app_env = settings.app_env
    app.state.git_sha = settings.git_sha
    app.state.engine = engine
    app.state.sessionmaker = make_sessionmaker(engine)

    app.state.system_prompt = chat.load_prompt(settings.prompts_dir)
    app.state.gateway = build_gateway(
        settings,
        make_recorder(app.state.sessionmaker),
    )

    # Middleware and error handlers
    app.middleware("http")(request_context)
    register_error_handlers(app)

    # Routes
    v1 = APIRouter(prefix="/v1")

    v1.include_router(documents.router)
    v1.include_router(chat.router)
    v1.include_router(ingest.router)

    app.include_router(health.router)
    app.include_router(v1)

    return app
