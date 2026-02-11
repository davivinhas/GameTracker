from pydantic import BaseModel, Field
from typing import Optional


class SearchGamesQuery(BaseModel):
    q: str = Field(..., description="Nome do jogo para buscar")
    limit: int = Field(10, ge=1, le=60)


class LookupGameQuery(BaseModel):
    title: str = Field(..., description="Nome do jogo para listar lojas e preços")


class DealsQuery(BaseModel):
    store_id: Optional[str] = Field(None, description="ID da store (1=Steam, 25=Epic, etc)")
    min_discount: int = Field(0, ge=0, le=100, description="Desconto mínimo em %")
    max_price: Optional[float] = Field(None, ge=0, description="Preço máximo")
    limit: int = Field(60, ge=1, le=60)


class TrackGameByTitleQuery(BaseModel):
    title: str = Field(..., description="Nome do jogo para rastrear")


class TrackGameByIdQuery(BaseModel):
    game_id: str = Field(..., description="Game ID da CheapShark")


class PaginationQuery(BaseModel):
    skip: int = 0
    limit: int = 100


class GameIdPath(BaseModel):
    game_id: int


class DealIdPath(BaseModel):
    deal_id: str
