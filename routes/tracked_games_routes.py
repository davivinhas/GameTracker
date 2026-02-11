# routes/tracked_games.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from db.engine import get_db
from schemas.game import GameResponse
from schemas.deal import DealResponse
from schemas.price_history import PriceHistoryResponse
from schemas.game_data import GameData
from schemas.game_search import GameSearchResponse
from schemas.game_lookup import GameLookupResponse
from schemas.price_change import GamePriceChangeResponse
from schemas.requests import (
    SearchGamesQuery,
    LookupGameQuery,
    DealsQuery,
    TrackGameByTitleQuery,
    TrackGameByIdQuery,
    PaginationQuery,
    GameIdPath,
    DealIdPath,
)
from schemas.responses import (
    MessageResponse,
    TrackGameResponse,
    StoreResponse,
)
from services.game_aggregator_service import GameAggregatorService
from services.cheap_shark_service import CheapSharkService

router = APIRouter(prefix="/games", tags=["games"])


@router.get("/search", response_model=List[GameSearchResponse])
async def search_games(
        params: SearchGamesQuery = Depends(),
        db: Session = Depends(get_db)
):
    """Busca jogos na CheapShark API"""
    service = GameAggregatorService(db)
    return await service.search_games(params.q, params.limit)


@router.get("/lookup", response_model=GameLookupResponse)
async def lookup_game(
        params: LookupGameQuery = Depends(),
        db: Session = Depends(get_db)
):
    """Busca um jogo e retorna todas as ofertas disponíveis"""
    service = GameAggregatorService(db)
    result = await service.lookup_game_by_title(params.title)
    if not result:
        raise HTTPException(status_code=404, detail="Game not found")
    return result


@router.get("/deals", response_model=List[GameData], tags=["admin"])
async def get_deals(
        params: DealsQuery = Depends(),
        db: Session = Depends(get_db)
):
    """Obtém promoções atuais"""
    service = GameAggregatorService(db)
    return await service.get_deals(params.store_id, params.min_discount, params.max_price, params.limit)


@router.get("/stores", response_model=List[StoreResponse], tags=["admin"])
async def get_stores():
    """Lista todas as stores disponíveis"""
    cheapshark = CheapSharkService()
    return await cheapshark.get_stores()


@router.post("/track-game", response_model=TrackGameResponse)
async def track_game_by_title(
        params: TrackGameByTitleQuery = Depends(),
        db: Session = Depends(get_db)
):
    """Adiciona um jogo para rastrear preços em todas as lojas"""
    service = GameAggregatorService(db)
    result = await service.track_game_by_title(params.title)
    if not result:
        raise HTTPException(status_code=404, detail="Game not found")
    game_id, created_deals = result
    return TrackGameResponse(message="Game tracked successfully", game_id=game_id, deals_tracked=created_deals)


@router.post("/track-game-by-id", response_model=TrackGameResponse, tags=["admin"])
async def track_game_by_id(
        params: TrackGameByIdQuery = Depends(),
        db: Session = Depends(get_db)
):
    """Adiciona um jogo para rastrear preços em todas as lojas pelo ID"""
    service = GameAggregatorService(db)
    result = await service.track_game_by_id(params.game_id)
    if not result:
        raise HTTPException(status_code=404, detail="Game not found")
    tracked_game_id, created_deals = result
    return TrackGameResponse(message="Game tracked successfully", game_id=tracked_game_id, deals_tracked=created_deals)


@router.get("/tracked", response_model=List[GameResponse])
async def get_tracked_games(
        params: PaginationQuery = Depends(),
        db: Session = Depends(get_db)
):
    """Lista jogos rastreados"""
    service = GameAggregatorService(db)
    return service.get_tracked_games(params.skip, params.limit)


@router.get("/tracked/games/{game_id}", response_model=GameResponse)
async def get_tracked_game(
        params: GameIdPath = Depends(),
        db: Session = Depends(get_db)
):
    """Detalhe de um jogo rastreado"""
    service = GameAggregatorService(db)
    game = service.get_tracked_game(params.game_id)
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    return game


@router.get("/tracked/games/{game_id}/changes", response_model=GamePriceChangeResponse)
async def get_game_price_changes(
        params: GameIdPath = Depends(),
        db: Session = Depends(get_db)
):
    """Atualiza e retorna mudanças de preço desde o último snapshot"""
    service = GameAggregatorService(db)
    changes = await service.check_price_changes_for_game(params.game_id)
    if not changes:
        raise HTTPException(status_code=404, detail="Game not found")
    return changes


@router.get("/tracked/deals", response_model=List[DealResponse], tags=["admin"])
async def get_tracked_deals(
        params: PaginationQuery = Depends(),
        db: Session = Depends(get_db)
):
    """Lista deals rastreados"""
    service = GameAggregatorService(db)
    return service.get_tracked_deals(params.skip, params.limit)


@router.get("/tracked/sales", response_model=List[DealResponse], tags=["admin"])
async def get_tracked_sales(db: Session = Depends(get_db)):
    """Lista deals rastreados que estão em promoção"""
    service = GameAggregatorService(db)
    return service.get_tracked_deals_on_sale()


@router.get("/tracked/deals/{deal_id}/history", response_model=List[PriceHistoryResponse], tags=["admin"])
async def get_deal_history(
        params: DealIdPath = Depends(),
        db: Session = Depends(get_db)
):
    """Lista histórico de preço de um deal"""
    service = GameAggregatorService(db)
    history = service.get_deal_history(params.deal_id)
    if history is None:
        raise HTTPException(status_code=404, detail="Deal not found")
    return history


@router.delete("/tracked/deals/{deal_id}", response_model=MessageResponse, tags=["admin"])
async def untrack_deal(
        params: DealIdPath = Depends(),
        db: Session = Depends(get_db)
):
    """Remove um deal do rastreamento"""
    service = GameAggregatorService(db)
    deal = service.deals.get_by_deal_id(params.deal_id)
    if not deal:
        raise HTTPException(status_code=404, detail="Deal not found")

    if not service.deals.delete(deal.id):
        raise HTTPException(status_code=404, detail="Deal not found")

    return MessageResponse(message="Deal untracked successfully")


@router.delete("/tracked/games/{game_id}", response_model=MessageResponse)
async def untrack_game(
        params: GameIdPath = Depends(),
        db: Session = Depends(get_db)
):
    """Remove um jogo e todos os seus deals"""
    service = GameAggregatorService(db)
    game = service.games.get_by_id(params.game_id)
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")

    if not service.games.delete(params.game_id):
        raise HTTPException(status_code=404, detail="Game not found")

    return MessageResponse(message="Game untracked successfully")
