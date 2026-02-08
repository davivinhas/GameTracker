# services/game_aggregator_service.py
from typing import List, Optional
from sqlalchemy.orm import Session
from services.cheapshark_service import CheapSharkService
from repositories.tracked_game_repository import TrackedGameRepository
from schemas.tracked_game import GameData, TrackedGameCreate


class GameAggregatorService:
    def __init__(self, db: Session):
        self.db = db
        self.repository = TrackedGameRepository(db)
        self.cheapshark = CheapSharkService()

    async def search_games(self, query: str, limit: int = 10) -> List[GameData]:
        """Busca jogos na CheapShark"""
        return await self.cheapshark.search_games(query, limit)

    async def get_deals(
            self,
            store_id: Optional[str] = None,
            min_discount: int = 0,
            max_price: Optional[float] = None,
            limit: int = 60
    ) -> List[GameData]:
        """Obtém promoções"""
        return await self.cheapshark.get_deals(store_id, min_discount, max_price, limit)

    async def track_game(self, game_data: GameData) -> int:
        """Adiciona um jogo para rastrear"""
        # Verifica se já existe
        existing = self.repository.get_by_external_id(game_data.external_id)
        if existing:
            # Atualiza o preço
            self.repository.update(existing.id, {
                "price": game_data.price,
                "original_price": game_data.original_price,
                "discount_percentage": game_data.discount_percentage,
                "is_on_sale": game_data.is_on_sale,
            })
            return existing.id

        # Cria novo
        game_dict = game_data.model_dump()
        new_game = self.repository.create(game_dict)
        return new_game.id

    async def update_tracked_game(self, game_id: int) -> Optional[GameData]:
        """Atualiza preços de um jogo rastreado"""
        game = self.repository.get_by_id(game_id)
        if not game:
            return None

        # Busca dados atualizados
        updated_data = await self.cheapshark.get_deal_by_id(game.external_id)
        if not updated_data:
            return None

        # Atualiza no banco
        self.repository.update(game_id, {
            "price": updated_data.price,
            "original_price": updated_data.original_price,
            "discount_percentage": updated_data.discount_percentage,
            "is_on_sale": updated_data.is_on_sale,
        })

        return updated_data

    async def get_tracked_games(self, skip: int = 0, limit: int = 100):
        """Lista jogos rastreados"""
        return self.repository.get_all(skip, limit)

    async def get_tracked_games_on_sale(self):
        """Lista jogos rastreados que estão em promoção"""
        return self.repository.get_games_on_sale()