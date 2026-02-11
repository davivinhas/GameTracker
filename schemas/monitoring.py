from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class MonitoringStats(BaseModel):
    """Estatísticas de uma execução de monitoramento"""
    games_checked: int = Field(..., description="Número de jogos verificados")
    deals_updated: int = Field(..., description="Número de deals atualizados")
    new_sales: int = Field(..., description="Número de novas promoções detectadas")
    price_drops: int = Field(..., description="Número de quedas de preço detectadas")
    errors: int = Field(default=0, description="Número de erros encontrados")
    started_at: Optional[datetime] = Field(None, description="Hora de início")
    finished_at: Optional[datetime] = Field(default=None, description="Hora de término")
    duration_seconds: Optional[float] = Field(default=None, description="Duração em segundos")

class GameCheckResult(BaseModel):
    """Resultado da verificação de um jogo específico"""
    game_id: int
    game_title: str
    deals_updated: int = 0
    new_sales: int = 0
    price_drops: int = 0
    error: Optional[str] = None


class MonitoringResponse(BaseModel):
    """Resposta completa do monitoramento com detalhes"""
    message: str = "Price monitoring completed"
    stats: MonitoringStats
    summary: str

    model_config = {
        "json_schema_extra": {
            "example": {
                "message": "Price monitoring completed",
                "stats": {
                    "games_checked": 15,
                    "deals_updated": 45,
                    "new_sales": 3,
                    "price_drops": 2,
                    "errors": 0,
                    "duration_seconds": 12.5
                },
                "summary": "Verificados 15 jogos | 3 novas promoções | 2 quedas de preço"
            }
        }
    }
