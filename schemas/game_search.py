from pydantic import BaseModel
from typing import Optional


class GameSearchResponse(BaseModel):
    """Resposta enxuta para /games/search (sem store)"""
    title: str
    game_id: Optional[str] = None
    deal_id: Optional[str] = None
    price: float
    discount_percentage: float = 0.0
    url: Optional[str] = None
    image_url: Optional[str] = None
    is_on_sale: bool = False
