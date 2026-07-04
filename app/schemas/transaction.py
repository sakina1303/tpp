from pydantic import BaseModel, ConfigDict


class TransactionResponse(BaseModel):
    txn_id: str
    date: str
    merchant: str
    amount: float
    currency: str
    category: str
    llm_category: str
    status: str
    is_anomaly: bool
    anomaly_reason: str

    model_config = ConfigDict(
        from_attributes=True
    )