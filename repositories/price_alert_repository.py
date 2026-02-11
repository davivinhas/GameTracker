from typing import List, Optional, Any
from sqlalchemy.orm import Session
from db.models.PriceAlert import PriceAlert
from repositories.base_repository import BaseRepository

class PriceAlertRepository(BaseRepository[PriceAlert]):
    def __init__(self, db: Session):
        super().__init__(PriceAlert, db)

    def get_unread(self, limit=100) -> list[type[PriceAlert]]:
        """Retorna alertas não lidos"""
        return (
            self.db.query(self.model)
            .filter(self.model.is_read.is_(False))
            .order_by(self.model.created_at.desc())
            .limit(limit)
            .all()
        )

    def get_by_deal(self, deal_id: int, limit: int = 50) -> list[type[PriceAlert]]:
        """Retorna alertas de um deal específico"""
        return self.db.query(self.model).filter(self.model.deal_id==deal_id).order_by(self.model.created_at.desc()).limit(limit).all()

    def mark_as_read(self, alert_id: int) -> PriceAlert | None:
        """Marca alerta como lido"""
        alert = self.get_by_id(alert_id)
        if not alert:
            return None
        alert.is_read = True
        self.db.commit()
        return alert

    def mark_all_as_read(self, alert_ids: List[int]) -> int:
        """Marca todos alertas como lidos"""
        count = self.db.query(self.model).filter(
            self.model.is_read == False
        ).update({"is_read": True})
        self.db.commit()
        return count