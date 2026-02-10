from typing import Optional, List
from sqlalchemy.orm import Session
from db.models.Deal import Deal
from repositories.base_repository import BaseRepository


class DealRepository(BaseRepository[Deal]):
    def __init__(self, db: Session):
        super().__init__(Deal, db)

    def get_by_deal_id(self, deal_id: str) -> Optional[Deal]:
        return self.db.query(self.model).filter(
            self.model.deal_id == deal_id
        ).first()  # type: ignore

    def get_by_game(self, game_id: int) -> List[Deal]:
        return self.db.query(self.model).filter(
            self.model.game_id == game_id
        ).all()  # type: ignore

    def get_on_sale(self) -> List[Deal]:
        return self.db.query(self.model).filter(
            self.model.is_on_sale
        ).all()  # type: ignore
