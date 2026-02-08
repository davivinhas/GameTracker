# routes/tracked_games.py
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from db.Base import get_db
from schemas.tracked_game import TrackedGameResponse
from schemas.game_data import GameData
from services.game_aggregator_service import GameAggregatorService
from services.cheap_shark_service import CheapSharkService

router = APIRouter(prefix="/games", tags=["games"])


@router.get("/search", response_model=List[GameData])
async def search_games(
        q: str = Query(..., description="Nome do jogo para buscar"),
        limit: int = Query(10, ge=1, le=60),
        db: Session = Depends(get_db)
):
    """Busca jogos na CheapShark API"""
    service = GameAggregatorService(db)
    return await service.search_games(q, limit)


@router.get("/deals", response_model=List[GameData])
async def get_deals(
        store_id: Optional[str] = Query(None, description="ID da store (1=Steam, 25=Epic, etc)"),
        min_discount: int = Query(0, ge=0, le=100, description="Desconto mínimo em %"),
        max_price: Optional[float] = Query(None, ge=0, description="Preço máximo"),
        limit: int = Query(60, ge=1, le=60),
        db: Session = Depends(get_db)
):
    """Obtém promoções atuais"""
    service = GameAggregatorService(db)
    return await service.get_deals(store_id, min_discount, max_price, limit)


@router.get("/stores")
async def get_stores():
    """Lista todas as stores disponíveis"""
    cheapshark = CheapSharkService()
    return await cheapshark.get_stores()


@router.post("/track", response_model=dict)
async def track_game(
        deal_id: str = Query(..., description="ID do deal para rastrear"),
        db: Session = Depends(get_db)
):
    """Adiciona um jogo para rastrear preços"""
    cheapshark = CheapSharkService()
    game_data = await cheapshark.get_deal_by_id(deal_id)

    if not game_data:
        raise HTTPException(status_code=404, detail="Deal not found")

    service = GameAggregatorService(db)
    game_id = await service.track_game(game_data)

    return {"message": "Game tracked successfully", "game_id": game_id}


@router.get("/tracked", response_model=List[TrackedGameResponse])
async def get_tracked_games(
        skip: int = 0,
        limit: int = 100,
        db: Session = Depends(get_db)
):
    """Lista jogos rastreados"""
    service = GameAggregatorService(db)
    return await service.get_tracked_games(skip, limit)


@router.get("/tracked/sales", response_model=List[TrackedGameResponse])
async def get_tracked_sales(db: Session = Depends(get_db)):
    """Lista jogos rastreados que estão em promoção"""
    service = GameAggregatorService(db)
    return await service.get_tracked_games_on_sale()


@router.put("/tracked/{game_id}/update")
async def update_tracked_game(
        game_id: int,
        db: Session = Depends(get_db)
):
    """Atualiza preço de um jogo rastreado"""
    service = GameAggregatorService(db)
    updated = await service.update_tracked_game(game_id)

    if not updated:
        raise HTTPException(status_code=404, detail="Game not found")

    return {"message": "Game updated successfully", "data": updated}


@router.delete("/tracked/{game_id}")
async def untrack_game(
        game_id: int,
        db: Session = Depends(get_db)
):
    """Remove um jogo do rastreamento"""
    service = GameAggregatorService(db)
    if not service.repository.delete(game_id):
        raise HTTPException(status_code=404, detail="Game not found")

    return {"message": "Game untracked successfully"}