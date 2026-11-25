from fastapi import Request
from fastapi.exceptions import HTTPException, RequestValidationError
from fastapi.responses import JSONResponse


async def http_exception_handler(request: Request, exc: HTTPException):
    titles = {
        400: "Bad Request",
        401: "Unauthorized",
        403: "Forbidden",
        404: "Not Found",
        500: "Internal Server Error",
    }

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "type": "about:blank",
            "title": titles.get(exc.status_code, "HTTP Error"),
            "status": exc.status_code,
            "detail": str(exc.detail),
        },
        media_type="application/problem+json",
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={
            "type": "about:blank",
            "title": "Unprocessable Entity",
            "status": 422,
            "detail": exc.errors(),
        },
        media_type="application/problem+json",
    )


def register_error_handlers(app):
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
