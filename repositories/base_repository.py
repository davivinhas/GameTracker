# repositories/base.py
from typing import TypeVar, Generic, Type
from sqlalchemy.orm import Session
from sqlalchemy import select

T = TypeVar("T")


class BaseRepository(Generic[T]):
    def __init__(self, model: Type[T]):
        self.model = model

    def get_by_id(self, db: Session, id: int) -> T | None:
        return db.get(self.model, id)

    def list_all(self, db: Session) -> list[T]:
        stmt = select(self.model)
        return list(db.execute(stmt).scalars().all())

    def delete(self, db: Session, obj: T) -> None:
        db.delete(obj)
        db.commit()

    def create(self, db: Session, obj: T) -> T:
        db.add(obj)
        db.commit()
        db.refresh(obj)
        return obj
