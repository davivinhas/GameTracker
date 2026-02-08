from pydantic import BaseModel
from core.enums.StoreEnum import StoreEnum
from datetime import datetime


class TrackedGameCreate(BaseModel):
    title: str
    store: StoreEnum
    external_id: str


class TrackedGameResponse(BaseModel):
    id: int
    title: str
    store: StoreEnum
    external_id: str
    current_price: float | None
    last_checked_at: datetime | None
    created_at: datetime

    class Config:
        from_attributes = True
