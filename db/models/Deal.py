from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime, timezone

from db.Base import Base


class Deal(Base):
    __tablename__ = "deals"
    __table_args__ = (
        UniqueConstraint("deal_id", name="uq_deal_deal_id"),
    )

    id = Column(Integer, primary_key=True, index=True)
    game_id = Column(Integer, ForeignKey("games.id"), nullable=False, index=True)

    deal_id = Column(String, nullable=False, index=True)
    store_id = Column(String, nullable=True)
    store_name = Column(String, nullable=True)

    current_price = Column(Float, nullable=False)
    original_price = Column(Float, nullable=True)
    discount_percentage = Column(Float, nullable=False, default=0.0)
    is_on_sale = Column(Boolean, nullable=False, default=False)
    url = Column(String, nullable=True)
    last_checked_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    game = relationship("Game", back_populates="deals")
    price_history = relationship(
        "PriceHistory",
        back_populates="deal",
        cascade="all, delete-orphan"
    )
