from typing import Optional, List
from sqlalchemy.orm import Session, joinedload
from db.models.Game import Game
from repositories.base_repository import BaseRepository


class GameRepository(BaseRepository[Game]):
    def __init__(self, db: Session):
        super().__init__(Game, db)

    def get_by_external_id(self, external_id: str) -> Optional[Game]:
        return self.db.query(self.model).filter(
            self.model.external_id == external_id
        ).first()  # type: ignore

    def search_by_title(self, title: str, limit: int = 10) -> List[Game]:
        return self.db.query(self.model).filter(
            self.model.title.ilike(f"%{title}%")
        ).limit(limit).all()  # type: ignore

    def get_all_with_deals(self, skip: int = 0, limit: int = 100) -> List[Game]:
        return (
            self.db.query(self.model)
            .options(joinedload(self.model.deals))
            .offset(skip)
            .limit(limit)
            .all()
        )
