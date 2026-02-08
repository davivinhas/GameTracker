from sqlalchemy import Column, Integer, DateTime, Float, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

from db.Base import Base

class PriceHistory(Base):
    __tablename__ = "price_history"

    id = Column(Integer, primary_key=True, index=True)
    game_id = Column(Integer, ForeignKey("tracked_games.id"), nullable=False)

    price = Column(Float, nullable=False)
    discount_percent = Column(Integer, nullable=True)
    checked_at = Column(DateTime, default=datetime.utcnow)

    game = relationship("TrackedGame", back_populates="price_history")