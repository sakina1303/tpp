from sqlalchemy.orm import Session

from app.models.transaction import Transaction


def save_transactions(db: Session, df, job_id):

    for _, row in df.iterrows():

        txn = Transaction(
            job_id=job_id,
            txn_id=str(row["txn_id"]),
            date=str(row["date"]),
            merchant=str(row["merchant"]),
            amount=float(row["amount"]),
            currency=str(row["currency"]),
            status=str(row["status"]),
            category=str(row["category"]),
            account_id=str(row["account_id"]),
            notes=str(row["notes"]),
            is_anomaly=bool(row["is_anomaly"]),
            anomaly_reason=str(row["anomaly_reason"]),
            llm_category=str(row.get("llm_category", "")),
            llm_failed=False
        )

        db.add(txn)

    db.commit()