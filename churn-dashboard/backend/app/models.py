from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base


class Plan(Base):
    __tablename__ = "plans"
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    price_monthly = Column(Float, nullable=False)
    tier = Column(String(50), nullable=False)  # free, starter, pro, enterprise
    subscribers = relationship("Subscriber", back_populates="plan")


class Subscriber(Base):
    __tablename__ = "subscribers"
    id = Column(Integer, primary_key=True)
    email = Column(String(200), nullable=False)
    company = Column(String(200), default="")
    plan_id = Column(Integer, ForeignKey("plans.id"), nullable=False)
    signup_date = Column(DateTime, nullable=False)
    churn_date = Column(DateTime, nullable=True)
    is_churned = Column(Boolean, default=False)
    mrr = Column(Float, default=0)
    lifetime_value = Column(Float, default=0)
    usage_score = Column(Float, default=0)  # 0-100
    health_score = Column(Float, default=0)  # 0-100
    churn_risk = Column(Float, default=0)  # 0-1 probability
    last_login_days = Column(Integer, default=0)
    support_tickets = Column(Integer, default=0)
    feature_adoption = Column(Float, default=0)  # 0-100%
    nps_score = Column(Integer, nullable=True)  # -100 to 100
    plan = relationship("Plan", back_populates="subscribers")
    activities = relationship("Activity", back_populates="subscriber")


class Activity(Base):
    __tablename__ = "activities"
    id = Column(Integer, primary_key=True)
    subscriber_id = Column(Integer, ForeignKey("subscribers.id"), nullable=False)
    month = Column(String(7), nullable=False)
    logins = Column(Integer, default=0)
    api_calls = Column(Integer, default=0)
    features_used = Column(Integer, default=0)
    support_tickets = Column(Integer, default=0)
    engagement_score = Column(Float, default=0)
    subscriber = relationship("Subscriber", back_populates="activities")


class RevenueMetric(Base):
    __tablename__ = "revenue_metrics"
    id = Column(Integer, primary_key=True)
    month = Column(String(7), nullable=False)
    mrr = Column(Float, default=0)
    new_mrr = Column(Float, default=0)
    churned_mrr = Column(Float, default=0)
    expansion_mrr = Column(Float, default=0)
    net_mrr = Column(Float, default=0)
    active_subscribers = Column(Integer, default=0)
    new_subscribers = Column(Integer, default=0)
    churned_subscribers = Column(Integer, default=0)
    churn_rate = Column(Float, default=0)
    revenue_churn_rate = Column(Float, default=0)


class ChurnReason(Base):
    __tablename__ = "churn_reasons"
    id = Column(Integer, primary_key=True)
    reason = Column(String(200), nullable=False)
    count = Column(Integer, default=0)
    revenue_lost = Column(Float, default=0)
    category = Column(String(100), default="")
