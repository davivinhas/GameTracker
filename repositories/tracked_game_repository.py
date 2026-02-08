# repositories/tracked_game_repository.py
from typing import List, Optional
from sqlalchemy.orm import Session
from db.models.TrackedGame import TrackedGame
from repositories.base_repository import BaseRepository


class TrackedGameRepository(BaseRepository[TrackedGame]):
    def __init__(self, db: Session):
        super().__init__(TrackedGame, db)

    def get_by_title(self, title: str) -> Optional[TrackedGame]:
        return self.db.query(self.model).filter(
            self.model.title.ilike(f"%{title}%")
        ).first()  # type: ignore

    def get_by_external_id(self, external_id: str) -> Optional[TrackedGame]:
        return self.db.query(self.model).filter(
            self.model.external_id == external_id
        ).first()  # type: ignore

    def get_games_on_sale(self) -> List[TrackedGame]:
        return self.db.query(self.model).filter(
            self.model.is_on_sale
        ).all()  # type: ignore

    def get_by_platform(self, platform: str) -> List[TrackedGame]:
        return self.db.query(self.model).filter(
            self.model.platform == platform
        ).all()  # type: ignore

    def get_with_discount_above(self, percentage: float) -> List[TrackedGame]:
        return self.db.query(self.model).filter(
            self.model.discount_percentage >= percentage
        ).all()  # type: ignore