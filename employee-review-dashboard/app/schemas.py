"""Pydantic schemas for API requests/responses."""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


# --- Company ---
class CompanyCreate(BaseModel):
    name: str
    industry: Optional[str] = None
    size: Optional[str] = None
    logo_url: Optional[str] = None
    website: Optional[str] = None


class CompanyResponse(BaseModel):
    id: int
    name: str
    industry: Optional[str]
    size: Optional[str]
    logo_url: Optional[str]
    website: Optional[str]
    review_count: Optional[int] = 0
    avg_sentiment: Optional[float] = None
    avg_rating: Optional[float] = None

    model_config = {"from_attributes": True}


# --- Review ---
class ReviewCreate(BaseModel):
    company_id: int
    source: str = "manual"
    title: Optional[str] = None
    pros: Optional[str] = None
    cons: Optional[str] = None
    review_text: Optional[str] = None
    rating: Optional[float] = Field(None, ge=1, le=5)
    reviewer_role: Optional[str] = None
    reviewer_location: Optional[str] = None
    is_current_employee: Optional[str] = "unknown"
    review_date: Optional[datetime] = None


class ReviewResponse(BaseModel):
    id: int
    company_id: int
    source: str
    title: Optional[str]
    pros: Optional[str]
    cons: Optional[str]
    review_text: Optional[str]
    rating: Optional[float]
    reviewer_role: Optional[str]
    reviewer_location: Optional[str]
    is_current_employee: Optional[str]
    review_date: Optional[datetime]
    overall_sentiment: Optional[float]
    pros_sentiment: Optional[float]
    cons_sentiment: Optional[float]
    topics: Optional[str]

    model_config = {"from_attributes": True}


# --- Dashboard aggregates ---
class SentimentOverview(BaseModel):
    """Top-level KPIs for the dashboard."""
    total_companies: int
    total_reviews: int
    avg_sentiment: float
    positive_pct: float
    negative_pct: float
    neutral_pct: float
    avg_rating: float
    trending_topics: list[dict]  # [{topic, count, avg_sentiment}]


class SentimentTrend(BaseModel):
    """Time-series data point."""
    period: str  # date string
    avg_sentiment: float
    review_count: int
    avg_rating: Optional[float] = None


class TopicBreakdown(BaseModel):
    topic: str
    count: int
    avg_sentiment: float
    positive_pct: float
    negative_pct: float


class CompanyComparison(BaseModel):
    company_name: str
    avg_sentiment: float
    avg_rating: float
    review_count: int
    trend: str  # "up", "down", "stable"


class DashboardFilters(BaseModel):
    company_ids: Optional[list[int]] = None
    sources: Optional[list[str]] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    topics: Optional[list[str]] = None


# --- Report ---
class ReportRequest(BaseModel):
    company_ids: Optional[list[int]] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    format: str = "pdf"  # pdf, pptx, xlsx
    include_sections: list[str] = ["overview", "trends", "topics", "companies", "recommendations"]
