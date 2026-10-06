from fastapi import FastAPI

app = FastAPI(
    title="Student Database System",
    description="REST API for managing student records.",
    version="0.1.0",
)


@app.get("/health")
def health():
    return {"status": "ok"}