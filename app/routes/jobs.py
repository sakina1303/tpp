import os
import shutil

from fastapi import APIRouter, UploadFile, File, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.job import Job
from app.models.transaction import Transaction
from app.models.summary import JobSummary

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

    os.makedirs("uploads", exist_ok=True)

    filepath = os.path.join(
        "uploads",
        file.filename
    )

    with open(filepath, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    job = Job(
        filename=file.filename,
        status="pending"
    )

    db.add(job)
    db.commit()
    db.refresh(job)

    process_job.delay(
        job.id,
        filepath
    )

    return {
        "job_id": job.id,
        "filename": job.filename,
        "status": "pending",
        "message": "Job queued successfully"
    }


@router.get("")
def get_jobs(
    status: str | None = Query(None),
    db: Session = Depends(get_db)
):

    query = db.query(Job)

    if status:

        query = query.filter(
            Job.status == status
        )

    return query.all()


@router.get("/{job_id}/status")
def get_job_status(
    job_id: int,
    db: Session = Depends(get_db)
):

    job = db.query(Job).filter(
        Job.id == job_id
    ).first()

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


@router.get("/{job_id}/results")
def get_results(
    job_id: int,
    db: Session = Depends(get_db)
):

    job = db.query(Job).filter(
        Job.id == job_id
    ).first()

    if job is None:

        return {
            "error": "Job not found"
        }

    summary = db.query(JobSummary).filter(
        JobSummary.job_id == job_id
    ).first()

    transactions = db.query(Transaction).filter(
        Transaction.job_id == job_id
    ).all()

    anomalies = [

        txn

        for txn in transactions

        if txn.is_anomaly

    ]

    category_spend = {}

    for txn in transactions:

        category = txn.llm_category or txn.category

        if category not in category_spend:

            category_spend[category] = 0

        category_spend[category] += txn.amount

    return {

        "job": {

            "id": job.id,

            "filename": job.filename,

            "status": job.status,

            "raw_rows": job.row_count_raw,

            "clean_rows": job.row_count_clean

        },

        "summary": summary,

        "category_breakdown": category_spend,

        "anomalies": anomalies,

        "transactions": transactions

    }