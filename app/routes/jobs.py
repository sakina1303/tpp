import os
import shutil

from fastapi import APIRouter, UploadFile, File, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.job import Job
from app.workers.tasks import process_job

router = APIRouter(
    prefix="/jobs",
    tags=["Jobs"]
)


@router.post("/upload")
async def upload_csv(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    # Create uploads directory
    os.makedirs("uploads", exist_ok=True)

    # Save uploaded file
    filepath = os.path.join("uploads", file.filename)

    with open(filepath, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Create Job
    job = Job(
        filename=file.filename,
        status="pending"
    )

    db.add(job)
    db.commit()
    db.refresh(job)

    # Send processing to Celery
    process_job.delay(
        job.id,
        filepath
    )

    # Immediately return
    return {
        "job_id": job.id,
        "filename": job.filename,
        "status": "pending",
        "message": "Job queued successfully"
    }


@router.get("")
def get_jobs(db: Session = Depends(get_db)):
    jobs = db.query(Job).all()
    return jobs


@router.get("/{job_id}/status")
def get_job_status(
    job_id: int,
    db: Session = Depends(get_db)
):
    job = db.query(Job).filter(Job.id == job_id).first()

    if job is None:
        return {
            "error": "Job not found"
        }

    return {
        "job_id": job.id,
        "filename": job.filename,
        "status": job.status,
        "raw_rows": job.row_count_raw,
        "clean_rows": job.row_count_clean,
        "created_at": job.created_at,
        "completed_at": job.completed_at,
        "error_message": job.error_message
    }