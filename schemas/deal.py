from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class DealBase(BaseModel):
    deal_id: str
    store_id: Optional[str] = None
    store_name: Optional[str] = None
    current_price: float
    original_price: Optional[float] = None
    discount_percentage: float = 0.0
    is_on_sale: bool = False
    url: Optional[str] = None
    last_checked_at: Optional[datetime] = None


class DealResponse(DealBase):
    id: int
    game_id: int

    model_config = {"from_attributes": True}
