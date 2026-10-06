from datetime import datetime

from fastapi import FastAPI

from app.schemas import StudentCreate, StudentResponse
app = FastAPI(
    title="Student Database System",
    description="REST API for managing student records.",
    version="0.1.0",
)


@app.get("/health")
def health():
    return {"status": "ok"}


# TEMPORARY: echoes the input back so we can test validation.
# Phase 5 replaces this with real create logic.
@app.post("/students", response_model=StudentResponse, status_code=201)
def create_student(student: StudentCreate):
    return StudentResponse(
        id=1,
        created_at=datetime.now(),
        **student.model_dump(),
    )