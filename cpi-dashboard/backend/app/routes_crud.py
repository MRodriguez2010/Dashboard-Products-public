"""CRUD routes for CPI Dashboard."""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models import Category, Competitor, Product

router = APIRouter(tags=["crud"])


@router.get("/categories")
async def list_categories(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Category).order_by(Category.name))
    return [{"id": c.id, "name": c.name, "description": c.description} for c in result.scalars().all()]


@router.get("/competitors")
async def list_competitors(category_id: int = None, db: AsyncSession = Depends(get_db)):
    q = select(Competitor)
    if category_id:
        q = q.where(Competitor.category_id == category_id)
    q = q.order_by(Competitor.name)
    result = await db.execute(q)
    return [{"id": c.id, "name": c.name, "website": c.website, "category_id": c.category_id,
             "tier": c.tier, "market_share_pct": c.market_share_pct} for c in result.scalars().all()]


@router.get("/products")
async def list_products(competitor_id: int = None, category_id: int = None, db: AsyncSession = Depends(get_db)):
    q = select(Product)
    if competitor_id:
        q = q.where(Product.competitor_id == competitor_id)
    if category_id:
        q = q.where(Product.category_id == category_id)
    q = q.order_by(Product.name)
    result = await db.execute(q)
    import json
    return [{"id": p.id, "name": p.name, "competitor_id": p.competitor_id, "category_id": p.category_id,
             "sku": p.sku, "features": json.loads(p.features) if p.features else []} for p in result.scalars().all()]
