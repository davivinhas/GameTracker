from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class PriceHistoryResponse(BaseModel):
    id: int
    price: float
    discount_percent: Optional[float] = None
    checked_at: datetime

    model_config = {"from_attributes": True}
