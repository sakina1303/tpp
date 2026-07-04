from datetime import datetime

from pydantic import BaseModel, ConfigDict


class SummaryStatusResponse(BaseModel):
    risk_level: str
    anomaly_count: int
    total_spend_inr: float
    total_spend_usd: float

    model_config = ConfigDict(
        from_attributes=True
    )


class JobResponse(BaseModel):
    id: int
    filename: str
    status: str
    row_count_raw: int
    row_count_clean: int
    created_at: datetime
    completed_at: datetime | None
    error_message: str | None

    model_config = ConfigDict(
        from_attributes=True
    )


class JobStatusResponse(BaseModel):
    job_id: int
    filename: str
    status: str
    raw_rows: int
    clean_rows: int
    created_at: datetime
    completed_at: datetime | None
    error_message: str | None = None
    summary: SummaryStatusResponse | None = None