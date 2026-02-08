from pydantic import BaseModel, HttpUrl
from datetime import datetime
from typing import Optional

class CheapSharkDeal(BaseModel):
    """Dados vindos da CheapShark API"""
    deal_id: str
    title: str
    store_id: str
    store_name: Optional[str] = None
    sale_price: float
    normal_price: float
    savings: float  # Porcentagem de desconto
    thumb: Optional[str] = None

