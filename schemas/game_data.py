from pydantic import BaseModel
from typing import Optional

class GameData(BaseModel):
    """Dados normalizados para salvar no banco"""
    title: str
    platform: str  # Nome da store (Steam, Epic, etc)
    external_id: str  # deal_id ou game_id
    price: float
    original_price: Optional[float] = None
    discount_percentage: float = 0.0
    url: str
    image_url: Optional[str] = None
    is_on_sale: bool = False