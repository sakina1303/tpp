from typing import Dict

from pydantic import BaseModel, ConfigDict


class SummaryResponse(BaseModel):
    total_spend_inr: float
    total_spend_usd: float
    top_merchants: Dict[str, float]
    anomaly_count: int
    risk_level: str
    narrative: str

    model_config = ConfigDict(
        from_attributes=True
    )