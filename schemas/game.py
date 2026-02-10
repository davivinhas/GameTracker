from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from schemas.deal import DealResponse


class GameBase(BaseModel):
    external_id: str
    title: str
    image_url: Optional[str] = None


class GameResponse(GameBase):
    id: int
    created_at: datetime
    deals: List[DealResponse] = []

    model_config = {"from_attributes": True}
