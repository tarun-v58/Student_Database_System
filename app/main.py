from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.exceptions import DuplicateEmailError, StudentNotFoundError
from app.routers import students

app = FastAPI(
    title="Student Database System",
    description="REST API for managing student records.",
    version="0.1.0",
)

app.include_router(students.router)


@app.exception_handler(StudentNotFoundError)
async def student_not_found_handler(request: Request, exc: StudentNotFoundError):
    return JSONResponse(status_code=404, content={"detail": str(exc)})


@app.exception_handler(DuplicateEmailError)
async def duplicate_email_handler(request: Request, exc: DuplicateEmailError):
    return JSONResponse(status_code=409, content={"detail": str(exc)})


@app.get("/health")
def health():
    return {"status": "ok"}