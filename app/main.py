from fastapi import FastAPI

from app.config import get_settings
from app.error_handlers import register_error_handlers
from app.logging_config import configure_logging
from app.middleware import request_logging_middleware
from app.routers import reports, students

settings = get_settings()
configure_logging(settings.log_level, settings.log_json)

app = FastAPI(
    title="Student Database System",
    description="REST API for managing student records.",
    version="0.1.0",
)

register_error_handlers(app)
app.middleware("http")(request_logging_middleware)
app.include_router(students.router)
app.include_router(reports.router)


@app.get("/health")
def health():
    return {"status": "ok"}