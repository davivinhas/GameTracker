# routes/tracked_games.py
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from db.engine import get_db
from schemas.game import GameResponse
from schemas.deal import DealResponse
from schemas.price_history import PriceHistoryResponse
from schemas.game_data import GameData
from schemas.game_lookup import GameLookupResponse
from schemas.price_change import GamePriceChangeResponse
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


@router.get("/lookup", response_model=GameLookupResponse)
async def lookup_game(
        title: str = Query(..., description="Nome do jogo para listar lojas e preços"),
        db: Session = Depends(get_db)
):
    """Busca um jogo e retorna todas as ofertas disponíveis"""
    service = GameAggregatorService(db)
    result = await service.lookup_game_by_title(title)
    if not result:
        raise HTTPException(status_code=404, detail="Game not found")
    return result


@router.get("/deals", response_model=List[GameData], tags=["admin"])
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


@router.get("/stores", tags=["admin"])
async def get_stores():
    """Lista todas as stores disponíveis"""
    cheapshark = CheapSharkService()
    return await cheapshark.get_stores()


@router.post("/track-game", response_model=dict)
async def track_game_by_title(
        title: str = Query(..., description="Nome do jogo para rastrear"),
        db: Session = Depends(get_db)
):
    """Adiciona um jogo para rastrear preços em todas as lojas"""
    service = GameAggregatorService(db)
    result = await service.track_game_by_title(title)
    if not result:
        raise HTTPException(status_code=404, detail="Game not found")
    game_id, created_deals = result
    return {"message": "Game tracked successfully", "game_id": game_id, "deals_tracked": created_deals}


@router.post("/track-game-by-id", response_model=dict, tags=["admin"])
async def track_game_by_id(
        game_id: str = Query(..., description="Game ID da CheapShark"),
        db: Session = Depends(get_db)
):
    """Adiciona um jogo para rastrear preços em todas as lojas pelo ID"""
    service = GameAggregatorService(db)
    result = await service.track_game_by_id(game_id)
    if not result:
        raise HTTPException(status_code=404, detail="Game not found")
    tracked_game_id, created_deals = result
    return {"message": "Game tracked successfully", "game_id": tracked_game_id, "deals_tracked": created_deals}


@router.get("/tracked", response_model=List[GameResponse])
async def get_tracked_games(
        skip: int = 0,
        limit: int = 100,
        db: Session = Depends(get_db)
):
    """Lista jogos rastreados"""
    service = GameAggregatorService(db)
    return service.get_tracked_games(skip, limit)


@router.get("/tracked/games/{game_id}", response_model=GameResponse)
async def get_tracked_game(
        game_id: int,
        db: Session = Depends(get_db)
):
    """Detalhe de um jogo rastreado"""
    service = GameAggregatorService(db)
    game = service.get_tracked_game(game_id)
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    return game


@router.get("/tracked/games/{game_id}/changes", response_model=GamePriceChangeResponse)
async def get_game_price_changes(
        game_id: int,
        db: Session = Depends(get_db)
):
    """Atualiza e retorna mudanças de preço desde o último snapshot"""
    service = GameAggregatorService(db)
    changes = await service.check_price_changes_for_game(game_id)
    if not changes:
        raise HTTPException(status_code=404, detail="Game not found")
    return changes


@router.get("/tracked/deals", response_model=List[DealResponse], tags=["admin"])
async def get_tracked_deals(
        skip: int = 0,
        limit: int = 100,
        db: Session = Depends(get_db)
):
    """Lista deals rastreados"""
    service = GameAggregatorService(db)
    return service.get_tracked_deals(skip, limit)


@router.get("/tracked/sales", response_model=List[DealResponse], tags=["admin"])
async def get_tracked_sales(db: Session = Depends(get_db)):
    """Lista deals rastreados que estão em promoção"""
    service = GameAggregatorService(db)
    return service.get_tracked_deals_on_sale()


@router.get("/tracked/deals/{deal_id}/history", response_model=List[PriceHistoryResponse], tags=["admin"])
async def get_deal_history(
        deal_id: str,
        db: Session = Depends(get_db)
):
    """Lista histórico de preço de um deal"""
    service = GameAggregatorService(db)
    history = service.get_deal_history(deal_id)
    if history is None:
        raise HTTPException(status_code=404, detail="Deal not found")
    return history


@router.delete("/tracked/deals/{deal_id}", tags=["admin"])
async def untrack_deal(
        deal_id: str,
        db: Session = Depends(get_db)
):
    """Remove um deal do rastreamento"""
    service = GameAggregatorService(db)
    deal = service.deals.get_by_deal_id(deal_id)
    if not deal:
        raise HTTPException(status_code=404, detail="Deal not found")

    if not service.deals.delete(deal.id):
        raise HTTPException(status_code=404, detail="Deal not found")

    return {"message": "Deal untracked successfully"}


@router.delete("/tracked/games/{game_id}")
async def untrack_game(
        game_id: int,
        db: Session = Depends(get_db)
):
    """Remove um jogo e todos os seus deals"""
    service = GameAggregatorService(db)
    game = service.games.get_by_id(game_id)
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")

    if not service.games.delete(game_id):
        raise HTTPException(status_code=404, detail="Game not found")

    return {"message": "Game untracked successfully"}
