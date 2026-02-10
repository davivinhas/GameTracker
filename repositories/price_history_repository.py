from typing import List, Optional
from sqlalchemy.orm import Session
from db.models.PriceHistory import PriceHistory
from repositories.base_repository import BaseRepository


class PriceHistoryRepository(BaseRepository[PriceHistory]):
    def __init__(self, db: Session):
        super().__init__(PriceHistory, db)

    def get_by_deal(self, deal_id: int) -> List[PriceHistory]:
        return self.db.query(self.model).filter(
            self.model.deal_id == deal_id
        ).order_by(self.model.checked_at.desc()).all()  # type: ignore

    def get_latest_by_deal(self, deal_id: int) -> Optional[PriceHistory]:
        return self.db.query(self.model).filter(
            self.model.deal_id == deal_id
        ).order_by(self.model.checked_at.desc()).first()  # type: ignore
