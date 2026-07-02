from app.database import SessionLocal

from app.models.job import Job

from app.services.csv_processor import process_csv
from app.services.db_writer import save_transactions

from app.workers.celery_app import celery


@celery.task
def process_job(job_id, filepath):

    db = SessionLocal()

    try:

        job = db.query(Job).filter(Job.id == job_id).first()

        job.status = "processing"

        db.commit()

        result = process_csv(filepath)

        save_transactions(
            db,
            result["data"],
            job_id
        )

        job.row_count_raw = result["raw_rows"]
        job.row_count_clean = result["clean_rows"]

        job.status = "completed"

        db.commit()

    except Exception as e:

        job.status = "failed"

        job.error_message = str(e)

        db.commit()

    finally:

        db.close()