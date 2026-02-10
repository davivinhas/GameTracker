# services/game_aggregator_service.py
from typing import List, Optional, Tuple, Dict, Any
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from services.cheap_shark_service import CheapSharkService
from repositories.game_repository import GameRepository
from repositories.deal_repository import DealRepository
from repositories.price_history_repository import PriceHistoryRepository
from schemas.game_data import GameData
from schemas.price_change import GamePriceChangeResponse, DealPriceChange, BestPriceChange


class GameAggregatorService:
    def __init__(self, db: Session):
        self.db = db
        self.games = GameRepository(db)
        self.deals = DealRepository(db)
        self.history = PriceHistoryRepository(db)
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

    async def lookup_game_by_title(self, title: str) -> Optional[dict]:
        """Busca um jogo por nome e retorna todas as ofertas"""
        results = await self.cheapshark.search_games(title, limit=1)
        if not results:
            return None

        game_id = results[0].game_id
        if not game_id:
            return None

        return await self.cheapshark.get_game_deals(game_id)

    async def track_deal(self, deal_id: str) -> Optional[Tuple[int, int]]:
        """Adiciona um deal para rastrear e cria histórico"""
        deal_data = await self.cheapshark.get_deal_by_id(deal_id)
        if not deal_data:
            return None

        if not deal_data.game_id:
            return None

        game = self.games.get_by_external_id(deal_data.game_id)
        if not game:
            game = self.games.create({
                "external_id": deal_data.game_id,
                "title": deal_data.title,
                "image_url": deal_data.image_url,
            })

        deal = self.deals.get_by_deal_id(deal_id)
        now = datetime.now(timezone.utc)
        deal_payload = {
            "game_id": game.id,
            "deal_id": deal_id,
            "store_id": deal_data.store_id,
            "store_name": deal_data.store_name,
            "current_price": deal_data.price,
            "original_price": deal_data.original_price,
            "discount_percentage": deal_data.discount_percentage,
            "is_on_sale": deal_data.is_on_sale,
            "url": deal_data.url,
            "last_checked_at": now,
        }

        if deal:
            deal = self.deals.update(deal.id, deal_payload)
        else:
            deal = self.deals.create(deal_payload)

        if deal:
            self.history.create({
                "deal_id": deal.id,
                "price": deal_data.price,
                "discount_percent": deal_data.discount_percentage,
                "checked_at": now,
            })

        return (game.id, deal.id) if deal else None

    async def track_game_by_title(self, title: str) -> Optional[Tuple[int, int]]:
        """Rastreia um jogo pelo nome e salva todos os deals atuais"""
        results = await self.cheapshark.search_games(title, limit=1)
        if not results:
            return None

        game_id = results[0].game_id
        if not game_id:
            return None

        game = self.games.get_by_external_id(game_id)
        if not game:
            game = self.games.create({
                "external_id": game_id,
                "title": results[0].title,
                "image_url": results[0].image_url,
            })

        deals_data = await self.cheapshark.get_game_deals(game_id)
        if not deals_data:
            return None

        created_deals = 0
        now = datetime.now(timezone.utc)
        for deal in deals_data["deals"]:
            existing = self.deals.get_by_deal_id(deal.deal_id) if deal.deal_id else None
            payload = {
                "game_id": game.id,
                "deal_id": deal.deal_id,
                "store_id": deal.store_id,
                "store_name": deal.store_name,
                "current_price": deal.price,
                "original_price": deal.original_price,
                "discount_percentage": deal.discount_percentage,
                "is_on_sale": deal.is_on_sale,
                "url": deal.url,
                "last_checked_at": now,
            }

            if existing:
                if existing.current_price != deal.price:
                    deal_row = self.deals.update(existing.id, payload)
                    if deal_row:
                        self.history.create({
                            "deal_id": deal_row.id,
                            "price": deal.price,
                            "discount_percent": deal.discount_percentage,
                            "checked_at": now,
                        })
            else:
                deal_row = self.deals.create(payload)
                created_deals += 1
                if deal_row:
                    self.history.create({
                        "deal_id": deal_row.id,
                        "price": deal.price,
                        "discount_percent": deal.discount_percentage,
                        "checked_at": now,
                    })

        return (game.id, created_deals)

    async def track_game_by_id(self, game_id: str) -> Optional[Tuple[int, int]]:
        """Rastreia um jogo pelo ID da CheapShark e salva todos os deals atuais"""
        if not game_id:
            return None

        deals_data = await self.cheapshark.get_game_deals(game_id)
        if not deals_data:
            return None

        game = self.games.get_by_external_id(game_id)
        if not game:
            game = self.games.create({
                "external_id": game_id,
                "title": deals_data["title"],
                "image_url": deals_data.get("image_url"),
            })

        created_deals = 0
        now = datetime.now(timezone.utc)
        for deal in deals_data["deals"]:
            existing = self.deals.get_by_deal_id(deal.deal_id) if deal.deal_id else None
            payload = {
                "game_id": game.id,
                "deal_id": deal.deal_id,
                "store_id": deal.store_id,
                "store_name": deal.store_name,
                "current_price": deal.price,
                "original_price": deal.original_price,
                "discount_percentage": deal.discount_percentage,
                "is_on_sale": deal.is_on_sale,
                "url": deal.url,
                "last_checked_at": now,
            }

            if existing:
                if existing.current_price != deal.price:
                    deal_row = self.deals.update(existing.id, payload)
                    if deal_row:
                        self.history.create({
                            "deal_id": deal_row.id,
                            "price": deal.price,
                            "discount_percent": deal.discount_percentage,
                            "checked_at": now,
                        })
            else:
                deal_row = self.deals.create(payload)
                created_deals += 1
                if deal_row:
                    self.history.create({
                        "deal_id": deal_row.id,
                        "price": deal.price,
                        "discount_percent": deal.discount_percentage,
                        "checked_at": now,
                    })

        return (game.id, created_deals)

    async def update_tracked_deal(self, deal_id: str) -> Optional[GameData]:
        """Atualiza preço de um deal rastreado"""
        deal = self.deals.get_by_deal_id(deal_id)
        if not deal:
            return None

        updated = await self.cheapshark.get_deal_by_id(deal_id)
        if not updated:
            return None

        now = datetime.now(timezone.utc)
        if deal.current_price != updated.price:
            self.deals.update(deal.id, {
                "current_price": updated.price,
                "original_price": updated.original_price,
                "discount_percentage": updated.discount_percentage,
                "is_on_sale": updated.is_on_sale,
                "url": updated.url,
                "last_checked_at": now,
            })

            self.history.create({
                "deal_id": deal.id,
                "price": updated.price,
                "discount_percent": updated.discount_percentage,
                "checked_at": now,
            })

        return updated

    async def check_price_changes_for_game(self, game_id: int) -> Optional[GamePriceChangeResponse]:
        """Atualiza deals do jogo e retorna mudanças desde o último snapshot"""
        game = self.games.get_by_id(game_id)
        if not game:
            return None

        deals_data = await self.cheapshark.get_game_deals(game.external_id)
        if not deals_data:
            return None

        now = datetime.now(timezone.utc)
        deal_changes: List[DealPriceChange] = []
        previous_prices: List[float] = []
        current_prices: List[float] = []
        best_current: Optional[Dict[str, Any]] = None

        for deal in deals_data["deals"]:
            if not deal.deal_id:
                continue

            existing = self.deals.get_by_deal_id(deal.deal_id)
            last_history = self.history.get_latest_by_deal(existing.id) if existing else None

            payload = {
                "game_id": game.id,
                "deal_id": deal.deal_id,
                "store_id": deal.store_id,
                "store_name": deal.store_name,
                "current_price": deal.price,
                "original_price": deal.original_price,
                "discount_percentage": deal.discount_percentage,
                "is_on_sale": deal.is_on_sale,
                "url": deal.url,
                "last_checked_at": now,
            }

            if existing:
                deal_row = self.deals.update(existing.id, payload)
            else:
                deal_row = self.deals.create(payload)

            if deal_row:
                self.history.create({
                    "deal_id": deal_row.id,
                    "price": deal.price,
                    "discount_percent": deal.discount_percentage,
                    "checked_at": now,
                })

            previous_price = last_history.price if last_history else None
            change_amount = (deal.price - previous_price) if previous_price is not None else None
            change_percent = ((deal.price - previous_price) / previous_price * 100) if previous_price else None

            if previous_price is not None:
                previous_prices.append(previous_price)
            current_prices.append(deal.price)

            if not best_current or deal.price < best_current["price"]:
                best_current = {
                    "price": deal.price,
                    "store_name": deal.store_name,
                    "deal_id": deal.deal_id,
                }

            deal_changes.append(DealPriceChange(
                deal_id=deal.deal_id,
                store_name=deal.store_name,
                previous_price=previous_price,
                current_price=deal.price,
                change_amount=change_amount,
                change_percent=round(change_percent, 2) if change_percent is not None else None,
                is_price_lower=(deal.price < previous_price) if previous_price is not None else None,
            ))

        previous_best = min(previous_prices) if previous_prices else None
        current_best = min(current_prices) if current_prices else None

        best_price = BestPriceChange(
            previous_best_price=previous_best,
            current_best_price=current_best,
            best_store_name=best_current["store_name"] if best_current else None,
            best_deal_id=best_current["deal_id"] if best_current else None,
            is_lower=(current_best < previous_best) if (previous_best is not None and current_best is not None) else None,
        )

        return GamePriceChangeResponse(
            game_id=game.id,
            title=game.title,
            deals=deal_changes,
            best_price=best_price,
        )

    async def update_all_tracked_deals(self) -> int:
        """Atualiza preços de todos os deals rastreados"""
        deals = self.deals.get_all()
        updated_count = 0
        for deal in deals:
            updated = await self.update_tracked_deal(deal.deal_id)
            if updated:
                updated_count += 1
        return updated_count

    def get_tracked_games(self, skip: int = 0, limit: int = 100):
        """Lista jogos rastreados"""
        return self.games.get_all_with_deals(skip, limit)

    def get_tracked_game(self, game_id: int):
        game = self.games.get_by_id(game_id)
        if not game:
            return None
        return game

    def get_tracked_deals(self, skip: int = 0, limit: int = 100):
        return self.deals.get_all(skip, limit)

    def get_tracked_deals_on_sale(self):
        """Lista deals rastreados que estão em promoção"""
        return self.deals.get_on_sale()

    def get_deal_history(self, deal_id: str):
        deal = self.deals.get_by_deal_id(deal_id)
        if not deal:
            return None
        return self.history.get_by_deal(deal.id)
