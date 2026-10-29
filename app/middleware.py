import logging
import re
import time
import uuid

from fastapi import Request

from app.logging_config import request_id_var

access_logger = logging.getLogger("app.access")

SLOW_REQUEST_MS = 500
_VALID_REQUEST_ID = re.compile(r"[A-Za-z0-9_-]{8,64}")


def _log_request(request: Request, status_code: int, started: float) -> None:
    duration_ms = round((time.perf_counter() - started) * 1000, 1)
    if status_code >= 500:
        level = logging.ERROR
    elif duration_ms > SLOW_REQUEST_MS:
        level = logging.WARNING
    elif request.url.path.startswith("/health") and status_code < 400:
        level = logging.DEBUG
    else:
        level = logging.INFO

    # Path only: the query string can hold personal data (search terms).
    access_logger.log(
        level,
        "%s %s -> %s in %.1f ms",
        request.method,
        request.url.path,
        status_code,
        duration_ms,
        extra={
            "method": request.method,
            "path": request.url.path,
            "status_code": status_code,
            "duration_ms": duration_ms,
        },
    )

async def request_logging_middleware(request: Request, call_next):
    incoming = request.headers.get("X-Request-ID", "")
    request_id = incoming if _VALID_REQUEST_ID.fullmatch(incoming) else uuid.uuid4().hex

    # Each request is handled in its own task, so this value disappears with it.
    request_id_var.set(request_id)

    started = time.perf_counter()
    try:
        response = await call_next(request)
    except Exception:
        _log_request(request, 500, started)
        raise

    _log_request(request, response.status_code, started)
    response.headers["X-Request-ID"] = request_id
    return response