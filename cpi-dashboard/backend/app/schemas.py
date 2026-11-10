"""Pydantic schemas for the CPI Dashboard API."""
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class CategoryResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None

class CompetitorResponse(BaseModel):
    id: int
    name: str
    website: Optional[str] = None
    category_id: int
    tier: Optional[str] = None
    market_share_pct: float = 0

class ProductResponse(BaseModel):
    id: int
    competitor_id: int
    name: str
    sku: Optional[str] = None
    category_id: int
    features: Optional[list] = None

class PricePointResponse(BaseModel):
    id: int
    product_id: int
    competitor_id: int
    price: float
    original_price: Optional[float] = None
    currency: str = "USD"
    price_type: Optional[str] = None
    recorded_at: datetime

class PriceAlertResponse(BaseModel):
    id: int
    product_id: int
    competitor_id: int
    alert_type: Optional[str] = None
    old_price: Optional[float] = None
    new_price: Optional[float] = None
    change_pct: Optional[float] = None
    message: Optional[str] = None
    created_at: datetime

# Dashboard aggregation schemas
class PricingOverview(BaseModel):
    total_products: int
    total_competitors: int
    total_categories: int
    total_price_points: int
    avg_price: float
    median_price: float
    min_price: float
    max_price: float
    recent_alerts: int
    price_spread: float

class CompetitorPricing(BaseModel):
    competitor_name: str
    competitor_id: int
    tier: Optional[str] = None
    product_count: int
    avg_price: float
    min_price: float
    max_price: float
    market_share_pct: float

class PriceTrend(BaseModel):
    period: str
    avg_price: float
    min_price: float
    max_price: float
    data_points: int

class CategoryBreakdown(BaseModel):
    category_name: str
    category_id: int
    product_count: int
    avg_price: float
    price_range: float
    competitor_count: int

class PriceDistribution(BaseModel):
    bucket: str
    count: int
    percentage: float

class ReportRequest(BaseModel):
    format: str = "pdf"
    category_ids: Optional[List[int]] = None
    competitor_ids: Optional[List[int]] = None
    include_sections: Optional[List[str]] = None
