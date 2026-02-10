from pydantic import BaseModel
from typing import Optional


class GameData(BaseModel):
    """Dados normalizados para respostas da CheapShark"""
    title: str
    game_id: Optional[str] = None
    deal_id: Optional[str] = None
    store_id: Optional[str] = None
    store_name: Optional[str] = None
    price: float
    original_price: Optional[float] = None
    discount_percentage: float = 0.0
    url: Optional[str] = None
    image_url: Optional[str] = None
    is_on_sale: bool = False
