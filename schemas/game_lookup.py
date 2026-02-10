from pydantic import BaseModel
from typing import List, Optional
from schemas.game_data import GameData


class GameLookupResponse(BaseModel):
    title: str
    image_url: Optional[str] = None
    deals: List[GameData]
