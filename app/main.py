from fastapi import FastAPI

from app.database import Base, engine
from app.routes.jobs import router as jobs_router

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="AI Transaction Processing Pipeline",
    description=(
        "An asynchronous transaction processing pipeline built with "
        "FastAPI, Celery, Redis, PostgreSQL, and Gemini AI."
    ),
    version="1.0.0",
)

app.include_router(jobs_router)


@app.get("/")
def home():
    return {
        "status": "running",
        "message": "AI Transaction Processing Pipeline API",
        "docs": "/docs"
    }