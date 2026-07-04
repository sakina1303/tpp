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

        job.status = "processing"
        db.commit()

        # -----------------------------
        # Process CSV
        # -----------------------------
        result = process_csv(filepath)

        df = result["data"]

        # -----------------------------
        # Initialize AI columns
        # -----------------------------
        df["llm_category"] = "Others"
        df["llm_failed"] = False

        # -----------------------------
        # Gemini Classification
        # -----------------------------
        gemini_result = classify_transactions_batch(df)

        category_map = gemini_result["categories"]
        failed_rows = gemini_result["failed_rows"]

        print("\n========== CATEGORY MAP ==========")
        print(category_map)
        print("==================================\n")

        # Fill dataframe with Gemini categories
        for index, category in category_map.items():

            if index in df.index:

                df.at[index, "llm_category"] = category

        # Mark rows where Gemini failed
        for index in failed_rows:

            if index in df.index:

                df.at[index, "llm_failed"] = True

        print("\n========== DATAFRAME AFTER GEMINI ==========")
        print(
            df[
                [
                    "merchant",
                    "llm_category",
                    "llm_failed"
                ]
            ].head(30)
        )
        print("============================================\n")

        # -----------------------------
        # Save Transactions
        # -----------------------------
        save_transactions(
            db=db,
            df=df,
            job_id=job_id
        )

        # -----------------------------
        # Generate Summary
        # -----------------------------
        generate_summary(
            db=db,
            job_id=job_id,
            df=df
        )

        # -----------------------------
        # Update Job
        # -----------------------------
        job.row_count_raw = result["raw_rows"]
        job.row_count_clean = result["clean_rows"]
        job.completed_at = datetime.utcnow()
        job.status = "completed"

        db.commit()

        print(f"\n✅ Job {job.id} completed successfully\n")

    except Exception as e:

        traceback.print_exc()

        if "job" in locals() and job:

            job.status = "failed"
            job.error_message = str(e)

            db.commit()

    finally:

        db.close()