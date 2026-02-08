from sqlalchemy import Column, Integer, Enum, String, Float, DateTime
from sqlalchemy.orm import relationship
from db.Base import Base
from core.enums.StoreEnum import StoreEnum
from datetime import datetime, timezone


class TrackedGame(Base):
    __tablename__ = "tracked_games"

    id = Column(Integer, primary_key=True, index=True)

    title = Column(String, nullable=False)
    store = Column(Enum(StoreEnum), nullable=False)
    external_id = Column(String, nullable=False, index=True)

    current_price = Column(Float, nullable=True)
    last_checked_at = Column(DateTime, nullable=True)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    price_history = relationship(
        "PriceHistory",
        back_populates="game",
        cascade="all, delete-orphan"
    )
