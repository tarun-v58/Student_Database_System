import logging

from fastapi import FastAPI

from app.error_handlers import register_error_handlers
from app.routers import reports, students

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)

app = FastAPI(
    title="Student Database System",
    description="REST API for managing student records.",
    version="0.1.0",
)

register_error_handlers(app)
app.include_router(students.router)
app.include_router(reports.router)


@app.get("/health")
def health():
    return {"status": "ok"}