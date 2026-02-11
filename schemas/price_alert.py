from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class PriceAlertResponse(BaseModel):
    id: int
    deal_id: int
    alert_type: str
    previous_price: Optional[float] = None
    new_price: float
    discount_percentage: Optional[float] = None
    message: Optional[str] = None
    is_read: bool
    created_at: datetime

    model_config = {"from_attributes": True}
