import logging
import time
from typing import List, Optional
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from repositories.game_repository import GameRepository
from repositories.deal_repository import DealRepository
from repositories.price_history_repository import PriceHistoryRepository
from repositories.price_alert_repository import PriceAlertRepository
from services.cheap_shark_service import CheapSharkService
from schemas.monitoring import MonitoringStats, GameCheckResult
from schemas.game_lookup import GameLookupResponse

logger = logging.getLogger(__name__)


class PriceMonitorService:
    """Serviço para monitoramento contínuo de preços e detecção de promoções"""

    def __init__(self, db: Session):
        self.db = db
        self.games = GameRepository(db)
        self.deals = DealRepository(db)
        self.history = PriceHistoryRepository(db)
        self.alerts = PriceAlertRepository(db)
        self.cheapshark = CheapSharkService()

    async def monitor_all_tracked_games(self) -> MonitoringStats:
        """
        Monitora todos os jogos rastreados e detecta mudanças de preço

        Returns:
            MonitoringStats: Estatísticas completas da execução
        """
        start_time = time.time()  # Para calcular duração
        started_at = datetime.now(timezone.utc)  # Timestamp para o schema

        stats = MonitoringStats(
            games_checked=0,
            deals_updated=0,
            new_sales=0,
            price_drops=0,
            errors=0,
            started_at=started_at
        )

        logger.info("Iniciando monitoramento de preços...")

        # Pega todos os jogos rastreados
        tracked_games = self.games.get_all(limit=1000)
        stats.games_checked = len(tracked_games)

        for game in tracked_games:
            try:
                result = await self._check_game_deals(game.id)
                stats.deals_updated += result.deals_updated
                stats.new_sales += result.new_sales
                stats.price_drops += result.price_drops

            except Exception as e:
                logger.error(f"Erro ao verificar jogo {game.title} (ID: {game.id}): {e}")
                stats.errors += 1

        # Finalizar estatísticas
        stats.finished_at = datetime.now(timezone.utc)
        stats.duration_seconds = round(time.time() - start_time, 2)

        logger.info(f"""
        Monitoramento concluído em {stats.duration_seconds}s:
        - Jogos verificados: {stats.games_checked}
        - Deals atualizados: {stats.deals_updated}
        - Novas promoções: {stats.new_sales}
        - Quedas de preço: {stats.price_drops}
        - Erros: {stats.errors}
        """)

        return stats

    async def _check_game_deals(self, game_id: int) -> GameCheckResult:
        """Verifica deals de um jogo específico e detecta mudanças"""
        game = self.games.get_by_id(game_id)
        if not game:
            return GameCheckResult(
                game_id=game_id,
                game_title="Unknown",
                error="Game not found"
            )

        result = GameCheckResult(
            game_id=game.id,
            game_title=game.title
        )

        # Busca deals atuais na API
        deals_response: Optional[GameLookupResponse] = await self.cheapshark.get_game_deals(game.external_id)
        if not deals_response:
            result.error = "Failed to fetch deals from API"
            return result

        now = datetime.now(timezone.utc)

        for deal_data in deals_response.deals:
            if not deal_data.deal_id:
                continue

            # Verifica se deal já existe no banco
            existing_deal = self.deals.get_by_deal_id(deal_data.deal_id)

            if existing_deal:
                # Deal existente - verifica mudanças
                changes = await self._check_price_changes(existing_deal, deal_data, now)
                result.deals_updated += 1
                if changes.get('new_sale'):
                    result.new_sales += 1
                if changes.get('price_drop'):
                    result.price_drops += 1
            else:
                # Novo deal - cria e registra alerta
                is_sale = await self._create_new_deal(game.id, deal_data, now)
                result.deals_updated += 1
                if is_sale:
                    result.new_sales += 1

        return result

    async def _check_price_changes(self, existing_deal, new_deal_data, now: datetime) -> dict:
        """
        Verifica e registra mudanças de preço

        Returns:
            dict: {'new_sale': bool, 'price_drop': bool}
        """
        changes = {'new_sale': False, 'price_drop': False}

        old_price = existing_deal.current_price
        new_price = new_deal_data.price
        old_is_on_sale = existing_deal.is_on_sale
        new_is_on_sale = new_deal_data.is_on_sale

        # Atualiza deal
        self.deals.update(existing_deal.id, {
            "current_price": new_price,
            "original_price": new_deal_data.original_price,
            "discount_percentage": new_deal_data.discount_percentage,
            "is_on_sale": new_is_on_sale,
            "url": new_deal_data.url,
            "last_checked_at": now,
        })

        # Registra no histórico
        self.history.create({
            "deal_id": existing_deal.id,
            "price": new_price,
            "discount_percent": new_deal_data.discount_percentage,
            "checked_at": now,
        })

        # Detecta mudanças significativas
        price_changed = abs(old_price - new_price) > 0.01
        sale_status_changed = old_is_on_sale != new_is_on_sale

        # NOVA PROMOÇÃO
        if not old_is_on_sale and new_is_on_sale:
            changes['new_sale'] = True
            message = (
                f"Nova promoção em {new_deal_data.store_name}! "
                f"De ${old_price:.2f} por ${new_price:.2f} "
                f"(-{new_deal_data.discount_percentage:.0f}%)"
            )
            self.alerts.create({
                "deal_id": existing_deal.id,
                "alert_type": "new_sale",
                "previous_price": old_price,
                "new_price": new_price,
                "discount_percentage": new_deal_data.discount_percentage,
                "message": message,
            })
            logger.info(f"{message}")

        # QUEDA DE PREÇO
        elif price_changed and new_price < old_price:
            price_drop_percent = ((old_price - new_price) / old_price) * 100

            # Só alerta se queda for significativa (>5%)
            if price_drop_percent >= 5:
                changes['price_drop'] = True
                message = (
                    f"Preço caiu em {new_deal_data.store_name}! "
                    f"De ${old_price:.2f} para ${new_price:.2f} "
                    f"(-{price_drop_percent:.1f}%)"
                )
                self.alerts.create({
                    "deal_id": existing_deal.id,
                    "alert_type": "price_drop",
                    "previous_price": old_price,
                    "new_price": new_price,
                    "discount_percentage": price_drop_percent,
                    "message": message,
                })
                logger.info(f"{message}")

        return changes

    async def _create_new_deal(self, game_id: int, deal_data, now: datetime) -> bool:
        """
        Cria novo deal e registra alerta

        Returns:
            bool: True se o deal está em promoção
        """
        deal = self.deals.create({
            "game_id": game_id,
            "deal_id": deal_data.deal_id,
            "store_id": deal_data.store_id,
            "store_name": deal_data.store_name,
            "current_price": deal_data.price,
            "original_price": deal_data.original_price,
            "discount_percentage": deal_data.discount_percentage,
            "is_on_sale": deal_data.is_on_sale,
            "url": deal_data.url,
            "last_checked_at": now,
        })

        if not deal:
            return False

        # Registra no histórico
        self.history.create({
            "deal_id": deal.id,
            "price": deal_data.price,
            "discount_percent": deal_data.discount_percentage,
            "checked_at": now,
        })

        # Se já estiver em promoção, cria alerta
        if deal_data.is_on_sale:
            message = (
                f"Novo deal encontrado em {deal_data.store_name}! "
                f"${deal_data.price:.2f} "
                f"(-{deal_data.discount_percentage:.0f}%)"
            )
            self.alerts.create({
                "deal_id": deal.id,
                "alert_type": "new_deal",
                "previous_price": None,
                "new_price": deal_data.price,
                "discount_percentage": deal_data.discount_percentage,
                "message": message,
            })
            logger.info(f"{message}")
            return True

        return False

    def get_recent_alerts(self, limit: int = 50) -> List:
        """Retorna alertas recentes"""
        return self.alerts.get_unread(limit=limit)

    def get_all_alerts(self, skip: int = 0, limit: int = 100) -> List:
        """Retorna todos os alertas"""
        return self.alerts.get_all(skip=skip, limit=limit)
