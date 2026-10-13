import json
import logging
from contextlib import contextmanager
from contextvars import ContextVar
from datetime import datetime, timezone

# The id of the request (or job) currently being handled. Each request runs in
# its own context, so concurrent requests never see each other's value.
request_id_var: ContextVar[str | None] = ContextVar("request_id", default=None)

TEXT_FORMAT = "%(asctime)s %(levelname)-7s [%(request_id)s] %(name)s: %(message)s"

# Attributes every LogRecord has. Anything else was passed through `extra=`.
_STANDARD_ATTRS = set(logging.makeLogRecord({}).__dict__) | {
    "message",
    "asctime",
    "request_id",
}


@contextmanager
def bound_request_id(request_id: str | None):
    token = request_id_var.set(request_id)
    try:
        yield
    finally:
        request_id_var.reset(token)


class RequestIdFilter(logging.Filter):
    """Stamps the current request id onto every record."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = request_id_var.get() or "-"
        return True


class JsonFormatter(logging.Formatter):
    """One JSON object per line, including any fields passed via extra=."""

    def format(self, record: logging.LogRecord) -> str:
        request_id = getattr(record, "request_id", None)
        payload = {
            "time": datetime.fromtimestamp(record.created, timezone.utc).isoformat(
                timespec="milliseconds"
            ),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "request_id": None if request_id in (None, "-") else request_id,
        }
        for key, value in record.__dict__.items():
            if key not in _STANDARD_ATTRS:
                payload[key] = value
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, default=str)


def configure_logging(level: str = "INFO", json_logs: bool = False) -> None:
    handler = logging.StreamHandler()
    handler.addFilter(RequestIdFilter())
    handler.setFormatter(JsonFormatter() if json_logs else logging.Formatter(TEXT_FORMAT))
    handler._app_handler = True

    root = logging.getLogger()
    # Safe to call more than once (--reload, worker imports): replace only our handler.
    for existing in list(root.handlers):
        if getattr(existing, "_app_handler", False):
            root.removeHandler(existing)
    root.addHandler(handler)
    root.setLevel(level)

    # Send uvicorn's messages through our handler too, and silence its own
    # access log, because the middleware writes a richer one.
    for name in ("uvicorn", "uvicorn.error", "uvicorn.access"):
        uvicorn_logger = logging.getLogger(name)
        uvicorn_logger.handlers.clear()
        uvicorn_logger.propagate = True
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    for noisy in ("httpx", "httpx2"):
        logging.getLogger(noisy).setLevel(logging.WARNING)