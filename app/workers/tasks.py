from datetime import datetime
import traceback

from app.database import SessionLocal
from app.models.job import Job

from app.services.csv_processor import process_csv
from app.services.db_writer import save_transactions
from app.services.gemini_service import classify_transactions_batch
from app.services.summary_service import generate_summary

from app.workers.celery_app import celery


@celery.task
def process_job(job_id, filepath):

    db = SessionLocal()

    try:

        job = db.query(Job).filter(Job.id == job_id).first()

        if job is None:
            return

        # -----------------------------
        # Update Job Status
        # -----------------------------
        job.status = "processing"
        db.commit()

        # -----------------------------
        # Process CSV
        # -----------------------------
        result = process_csv(filepath)

        df = result["data"]

        # ----------------------------------
        # Create llm_category column
        # ----------------------------------
        df["llm_category"] = ""

        # ----------------------------------
        # Gemini classifies EVERY transaction
        # ----------------------------------
        category_map = classify_transactions_batch(df)

        for index, category in category_map.items():
            df.at[index, "llm_category"] = category

        # ----------------------------------
        # Save Transactions
        # ----------------------------------
        save_transactions(
            db=db,
            df=df,
            job_id=job_id
        )

        # ----------------------------------
        # Generate AI Summary
        # ----------------------------------
        generate_summary(
            db=db,
            job_id=job_id,
            df=df
        )

        # ----------------------------------
        # Update Job
        # ----------------------------------
        job.row_count_raw = result["raw_rows"]
        job.row_count_clean = result["clean_rows"]
        job.completed_at = datetime.utcnow()
        job.status = "completed"

        db.commit()

        print(f"✅ Job {job.id} completed successfully")

    except Exception as e:

        traceback.print_exc()

        if "job" in locals() and job:
            job.status = "failed"
            job.error_message = str(e)
            db.commit()

    finally:

        db.close()