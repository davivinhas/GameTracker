from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class TrackedGameBase(BaseModel):
    title: str
    platform: str
    external_id: str
    price: float
    original_price: Optional[float] = None
    discount_percentage: float = 0.0
    url: str
    image_url: Optional[str] = None
    is_on_sale: bool = False


class TrackedGameUpdate(BaseModel):
    price: Optional[float] = None
    original_price: Optional[float] = None
    discount_percentage: Optional[float] = None
    is_on_sale: Optional[bool] = None
    url: Optional[str] = None
    image_url: Optional[str] = None


class TrackedGameResponse(TrackedGameBase):
    id: int
    last_checked: datetime
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}