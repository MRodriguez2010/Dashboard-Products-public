"""SQLAlchemy models for ESA Dashboard."""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Text, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from app.database import Base


class Company(Base):
    __tablename__ = "companies"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False, unique=True, index=True)
    industry = Column(String(128))
    size = Column(String(64))  # e.g. "1000-5000", "10000+"
    logo_url = Column(String(512))
    website = Column(String(512))
    created_at = Column(DateTime, default=datetime.utcnow)

    reviews = relationship("Review", back_populates="company", cascade="all, delete-orphan")


class Review(Base):
    __tablename__ = "reviews"
    __table_args__ = (
        Index("ix_reviews_company_date", "company_id", "review_date"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False, index=True)
    source = Column(String(64), nullable=False)  # glassdoor, indeed, internal
    title = Column(String(512))
    pros = Column(Text)
    cons = Column(Text)
    review_text = Column(Text)
    rating = Column(Float)  # 1-5 scale
    reviewer_role = Column(String(255))
    reviewer_location = Column(String(255))
    is_current_employee = Column(String(16))  # yes, no, unknown
    review_date = Column(DateTime, index=True)
    scraped_at = Column(DateTime, default=datetime.utcnow)

    # Sentiment scores (computed)
    overall_sentiment = Column(Float)  # -1 to 1
    pros_sentiment = Column(Float)
    cons_sentiment = Column(Float)

    # Topics (JSON-encoded list)
    topics = Column(Text)  # JSON: ["culture", "pay", "leadership"]

    company = relationship("Company", back_populates="reviews")


class SentimentSnapshot(Base):
    """Aggregated sentiment by company/period for fast dashboard queries."""
    __tablename__ = "sentiment_snapshots"
    __table_args__ = (
        Index("ix_snapshot_company_period", "company_id", "period", "period_start"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    period = Column(String(16), nullable=False)  # daily, weekly, monthly
    period_start = Column(DateTime, nullable=False)
    avg_sentiment = Column(Float)
    avg_rating = Column(Float)
    review_count = Column(Integer)
    positive_count = Column(Integer)
    negative_count = Column(Integer)
    neutral_count = Column(Integer)
    top_topics = Column(Text)  # JSON
    created_at = Column(DateTime, default=datetime.utcnow)


class Event(Base):
    """Notable events for overlay on sentiment timeline."""
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=True)  # null = industry-wide
    event_type = Column(String(64))  # layoff, policy_change, earnings, merger
    title = Column(String(512), nullable=False)
    description = Column(Text)
    event_date = Column(DateTime, nullable=False, index=True)
    source_url = Column(String(512))
    created_at = Column(DateTime, default=datetime.utcnow)
