"""Database models for Competitive Pricing Intelligence."""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Index, JSON
from app.database import Base


class Category(Base):
    __tablename__ = "categories"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(200), nullable=False, unique=True)
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)


class Competitor(Base):
    __tablename__ = "competitors"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(200), nullable=False)
    website = Column(String(500))
    category_id = Column(Integer, nullable=False)
    tier = Column(String(50))  # budget, mid-range, premium, enterprise
    market_share_pct = Column(Float, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (Index("ix_competitor_category", "category_id"),)


class Product(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True, autoincrement=True)
    competitor_id = Column(Integer, nullable=False)
    name = Column(String(300), nullable=False)
    sku = Column(String(100))
    category_id = Column(Integer, nullable=False)
    features = Column(JSON)  # list of feature strings
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("ix_product_competitor", "competitor_id"),
        Index("ix_product_category", "category_id"),
    )


class PricePoint(Base):
    __tablename__ = "price_points"
    id = Column(Integer, primary_key=True, autoincrement=True)
    product_id = Column(Integer, nullable=False)
    competitor_id = Column(Integer, nullable=False)
    price = Column(Float, nullable=False)
    original_price = Column(Float)  # before discount
    currency = Column(String(10), default="USD")
    price_type = Column(String(50))  # monthly, annual, one-time, per-user
    recorded_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("ix_price_product", "product_id"),
        Index("ix_price_competitor", "competitor_id"),
        Index("ix_price_date", "recorded_at"),
    )


class PriceAlert(Base):
    __tablename__ = "price_alerts"
    id = Column(Integer, primary_key=True, autoincrement=True)
    product_id = Column(Integer, nullable=False)
    competitor_id = Column(Integer, nullable=False)
    alert_type = Column(String(50))  # price_drop, price_increase, new_product, undercut
    old_price = Column(Float)
    new_price = Column(Float)
    change_pct = Column(Float)
    message = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (Index("ix_alert_date", "created_at"),)


class MarketEvent(Base):
    __tablename__ = "market_events"
    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(500), nullable=False)
    description = Column(Text)
    event_type = Column(String(50))  # product_launch, price_war, acquisition, funding
    category_id = Column(Integer)
    event_date = Column(DateTime, default=datetime.utcnow)
