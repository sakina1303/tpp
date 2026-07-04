import os
import shutil

from fastapi import (
    APIRouter,
    UploadFile,
    File,
    Depends,
    Query,
    HTTPException,
    status,
)

from sqlalchemy.orm import Session

from app.database import get_db
from app.models.job import Job
from app.models.summary import JobSummary
from app.models.transaction import Transaction

from app.schemas.job import (
    JobResponse,
    JobStatusResponse,
)

from app.workers.tasks import process_job

router = APIRouter(
    prefix="/jobs",
    tags=["Jobs"]
)


@router.post(
    "/upload",
    status_code=status.HTTP_202_ACCEPTED
)
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
        "message": "Job queued successfully",
        "status_url": f"/jobs/{job.id}/status",
        "results_url": f"/jobs/{job.id}/results"
    }


@router.get(
    "",
    response_model=list[JobResponse]
)
def get_jobs(
    status: str | None = Query(None),
    db: Session = Depends(get_db)
):

    query = db.query(Job)

    if status:
        query = query.filter(Job.status == status)

    return (
        query
        .order_by(Job.id.desc())
        .all()
    )


@router.get(
    "/{job_id}/status",
    response_model=JobStatusResponse
)
def get_job_status(
    job_id: int,
    db: Session = Depends(get_db)
):

    job = (
        db.query(Job)
        .filter(Job.id == job_id)
        .first()
    )

    if job is None:
        raise HTTPException(
            status_code=404,
            detail="Job not found"
        )

    summary = (
        db.query(JobSummary)
        .filter(JobSummary.job_id == job.id)
        .first()
    )

    response = {
        "job_id": job.id,
        "filename": job.filename,
        "status": job.status,
        "raw_rows": job.row_count_raw,
        "clean_rows": job.row_count_clean,
        "created_at": job.created_at,
        "completed_at": job.completed_at,
        "error_message": job.error_message,
        "summary": None
    }

    if summary:

        response["summary"] = {

            "risk_level": summary.risk_level,

            "anomaly_count": summary.anomaly_count,

            "total_spend_inr": summary.total_spend_inr,

            "total_spend_usd": summary.total_spend_usd

        }

    return response


@router.get("/{job_id}/results")
def get_results(
    job_id: int,
    db: Session = Depends(get_db)
):

    job = (
        db.query(Job)
        .filter(Job.id == job_id)
        .first()
    )

    if job is None:
        raise HTTPException(
            status_code=404,
            detail="Job not found"
        )

    summary = (
        db.query(JobSummary)
        .filter(JobSummary.job_id == job_id)
        .first()
    )

    transactions = (
        db.query(Transaction)
        .filter(Transaction.job_id == job_id)
        .all()
    )

    category_breakdown = {}

    anomalies = []

    for txn in transactions:

        category = txn.llm_category or txn.category or "Others"

        category_breakdown[category] = (
            category_breakdown.get(category, 0)
            + txn.amount
        )

        if txn.is_anomaly:

            anomalies.append({
                "txn_id": txn.txn_id,
                "merchant": txn.merchant,
                "amount": txn.amount,
                "reason": txn.anomaly_reason
            })

    return {

        "job": {

            "id": job.id,
            "filename": job.filename,
            "status": job.status,
            "raw_rows": job.row_count_raw,
            "clean_rows": job.row_count_clean

        },

        "summary": None if summary is None else {

            "total_spend_inr": summary.total_spend_inr,

            "total_spend_usd": summary.total_spend_usd,

            "top_merchants": summary.top_merchants,

            "anomaly_count": summary.anomaly_count,

            "risk_level": summary.risk_level,

            "narrative": summary.narrative

        },

        "category_breakdown": category_breakdown,

        "anomalies": anomalies,

        "transactions": transactions

    }