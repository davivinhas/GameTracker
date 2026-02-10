from pydantic import BaseModel
from typing import List, Optional


class DealPriceChange(BaseModel):
    deal_id: str
    store_name: Optional[str] = None
    previous_price: Optional[float] = None
    current_price: float
    change_amount: Optional[float] = None
    change_percent: Optional[float] = None
    is_price_lower: Optional[bool] = None


class BestPriceChange(BaseModel):
    previous_best_price: Optional[float] = None
    current_best_price: Optional[float] = None
    best_store_name: Optional[str] = None
    best_deal_id: Optional[str] = None
    is_lower: Optional[bool] = None


class GamePriceChangeResponse(BaseModel):
    game_id: int
    title: str
    deals: List[DealPriceChange]
    best_price: BestPriceChange
