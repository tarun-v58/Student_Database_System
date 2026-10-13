import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.exceptions import AppError
from app.logging_config import request_id_var

logger = logging.getLogger("app.errors")


def error_response(
    status_code: int,
    code: str,
    message: str,
    details: list | None = None,
    headers: dict | None = None,
) -> JSONResponse:
    body = {"error": code, "message": message}
    if details:
        body["details"] = details
    return JSONResponse(status_code=status_code, content=body, headers=headers)


async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    logger.info("Request rejected: %s", exc.code, extra={"error_code": exc.code})
    return error_response(exc.status_code, exc.code, exc.message)


async def validation_error_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    details = [
        {
            "field": ".".join(str(part) for part in err["loc"][1:]) or str(err["loc"][0]),
            "message": err["msg"],
        }
        for err in exc.errors()
    ]
    logger.info(
        "Validation failed",
        extra={
            "error_code": "validation_error",
            "fields": [d["field"] for d in details],
        },
    )
    return error_response(422, "validation_error", "Request validation failed", details)


async def http_error_handler(
    request: Request, exc: StarletteHTTPException
) -> JSONResponse:
    codes = {404: "not_found", 405: "method_not_allowed"}
    code = codes.get(exc.status_code, "http_error")
    return error_response(exc.status_code, code, str(exc.detail))


async def unhandled_error_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.error(
        "Unhandled error on %s %s", request.method, request.url.path, exc_info=exc
    )
    request_id = request_id_var.get()
    headers = {"X-Request-ID": request_id} if request_id else None
    return error_response(
        500, "internal_error", "Something went wrong on our side", headers=headers
    )


def register_error_handlers(app: FastAPI) -> None:
    app.add_exception_handler(AppError, app_error_handler)
    app.add_exception_handler(RequestValidationError, validation_error_handler)
    app.add_exception_handler(StarletteHTTPException, http_error_handler)
    app.add_exception_handler(Exception, unhandled_error_handler)