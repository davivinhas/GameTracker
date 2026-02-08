from pydantic import BaseModel
from datetime import datetime


class PriceHistoryResponse(BaseModel):
    id: int
    price: float
    discount_percent: int | None
    checked_at: datetime

    class Config:
        from_attributes = True
