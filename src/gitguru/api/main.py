import logging
import uuid

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from gitguru.api.errors import http_exception_handler
from gitguru.api.logging_config import configure_logging, request_id_var
from gitguru.api.routes import router
from gitguru.api.settings import get_settings

logger = logging.getLogger("gitguru")


def create_app():
    settings = get_settings()

    configure_logging()

    app = FastAPI(title=settings.app_name)

    app.add_exception_handler(StarletteHTTPException, http_exception_handler)

    @app.middleware("http")
    async def request_middleware(request: Request, call_next):
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))

        token = request_id_var.set(request_id)

        try:
            response = await call_next(request)
            response.headers["X-Request-ID"] = request_id

            logger.info(
                "%s %s - %s", request.method, request.url.path, response.status_code
            )

            return response
        finally:
            request_id_var.reset(token)

    @app.get("/health")
    def health():
        return {"status": "healthy"}

    @app.get("/ready")
    def ready():
        if not settings.data_file.is_file():
            return JSONResponse(status_code=503, content={"status": "not ready"})

        return {"status": "ready"}

    app.include_router(router, prefix=settings.api_prefix)

    return app


app = create_app()
