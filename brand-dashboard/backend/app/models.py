from sqlalchemy import Column, Integer, String, Float, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base

class Brand(Base):
    __tablename__ = "brands"
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    industry = Column(String(100), default="")
    logo_emoji = Column(String(10), default="🏢")
    mentions = relationship("Mention", back_populates="brand")

class Platform(Base):
    __tablename__ = "platforms"
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    icon = Column(String(10), default="🌐")

class Mention(Base):
    __tablename__ = "mentions"
    id = Column(Integer, primary_key=True)
    brand_id = Column(Integer, ForeignKey("brands.id"), nullable=False)
    platform_id = Column(Integer, ForeignKey("platforms.id"), nullable=False)
    content = Column(Text, default="")
    sentiment = Column(String(20), nullable=False)  # positive, negative, neutral
    sentiment_score = Column(Float, default=0)  # -1 to 1
    reach = Column(Integer, default=0)
    engagement = Column(Integer, default=0)
    date = Column(DateTime, nullable=False)
    topic = Column(String(100), default="")
    brand = relationship("Brand", back_populates="mentions")

class ReputationScore(Base):
    __tablename__ = "reputation_scores"
    id = Column(Integer, primary_key=True)
    brand_id = Column(Integer, ForeignKey("brands.id"), nullable=False)
    month = Column(String(7), nullable=False)
    overall_score = Column(Float, default=0)  # 0-100
    positive_pct = Column(Float, default=0)
    negative_pct = Column(Float, default=0)
    neutral_pct = Column(Float, default=0)
    total_mentions = Column(Integer, default=0)
    total_reach = Column(Integer, default=0)
    avg_engagement = Column(Float, default=0)

class CrisisEvent(Base):
    __tablename__ = "crisis_events"
    id = Column(Integer, primary_key=True)
    brand_id = Column(Integer, ForeignKey("brands.id"), nullable=False)
    title = Column(String(200), nullable=False)
    severity = Column(String(20), nullable=False)  # low, medium, high, critical
    date = Column(DateTime, nullable=False)
    description = Column(Text, default="")
    resolution_status = Column(String(50), default="monitoring")
    sentiment_impact = Column(Float, default=0)

class Influencer(Base):
    __tablename__ = "influencers"
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    platform = Column(String(50), nullable=False)
    followers = Column(Integer, default=0)
    sentiment_toward_brand = Column(String(20), default="neutral")
    influence_score = Column(Float, default=0)
    brand_id = Column(Integer, ForeignKey("brands.id"), nullable=False)
