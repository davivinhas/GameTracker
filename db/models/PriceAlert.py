from sqlalchemy import Column, String, Integer, Float, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime, timezone

from db.Base import Base

class PriceAlert(Base):
    __tablename__ = 'price_alerts'
    id = Column(Integer, primary_key=True)
    deal_id = Column(Integer, ForeignKey('deals.id'), nullable=False, index=True)

    alert_type = Column(String, nullable=False)  # 'new_deal', 'price_drop', 'new_sale'
    previous_price = Column(Float, nullable=True)
    new_price = Column(Float, nullable=False)
    discount_percentage = Column(Float, nullable=True)

    message = Column(String, nullable=True)
    is_read = Column(Boolean, default=False)

    created_at = Column(DateTime, default=datetime.now(timezone.utc), nullable=False)

    deal = relationship("Deal", back_populates="alerts")
