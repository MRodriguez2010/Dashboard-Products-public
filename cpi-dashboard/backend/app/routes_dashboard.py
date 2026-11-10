"""Dashboard analytics routes for CPI Dashboard."""
import statistics
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, distinct
from app.database import get_db
from app.models import Category, Competitor, Product, PricePoint, PriceAlert, MarketEvent

router = APIRouter(tags=["dashboard"])


@router.get("/dashboard/overview")
async def dashboard_overview(category_id: int = None, db: AsyncSession = Depends(get_db)):
    """Overall pricing intelligence summary."""
    pq = select(PricePoint)
    if category_id:
        pq = pq.join(Product, PricePoint.product_id == Product.id).where(Product.category_id == category_id)
    
    result = await db.execute(pq)
    prices = [p.price for p in result.scalars().all() if p.price > 0]
    
    # Counts
    prod_q = select(func.count(distinct(Product.id)))
    comp_q = select(func.count(distinct(Competitor.id)))
    cat_q = select(func.count(distinct(Category.id)))
    alert_q = select(func.count(PriceAlert.id))
    
    if category_id:
        prod_q = prod_q.where(Product.category_id == category_id)
        comp_q = comp_q.where(Competitor.category_id == category_id)
    
    total_products = (await db.execute(prod_q)).scalar() or 0
    total_competitors = (await db.execute(comp_q)).scalar() or 0
    total_categories = (await db.execute(cat_q)).scalar() or 0
    recent_alerts = (await db.execute(alert_q)).scalar() or 0
    
    if not prices:
        return {"total_products": 0, "total_competitors": 0, "total_categories": 0,
                "total_price_points": 0, "avg_price": 0, "median_price": 0,
                "min_price": 0, "max_price": 0, "recent_alerts": 0, "price_spread": 0}
    
    return {
        "total_products": total_products,
        "total_competitors": total_competitors,
        "total_categories": total_categories,
        "total_price_points": len(prices),
        "avg_price": round(statistics.mean(prices), 2),
        "median_price": round(statistics.median(prices), 2),
        "min_price": round(min(prices), 2),
        "max_price": round(max(prices), 2),
        "recent_alerts": recent_alerts,
        "price_spread": round(max(prices) - min(prices), 2),
    }


@router.get("/dashboard/competitors")
async def competitor_pricing(category_id: int = None, db: AsyncSession = Depends(get_db)):
    """Pricing breakdown by competitor."""
    q = select(Competitor)
    if category_id:
        q = q.where(Competitor.category_id == category_id)
    q = q.order_by(Competitor.market_share_pct.desc())
    
    comps = (await db.execute(q)).scalars().all()
    result = []
    
    for c in comps:
        pp_q = select(PricePoint.price).where(PricePoint.competitor_id == c.id)
        pp_result = await db.execute(pp_q)
        prices = [p for (p,) in pp_result.all() if p > 0]
        
        prod_count = (await db.execute(
            select(func.count(Product.id)).where(Product.competitor_id == c.id)
        )).scalar() or 0
        
        if prices:
            result.append({
                "competitor_name": c.name,
                "competitor_id": c.id,
                "tier": c.tier,
                "product_count": prod_count,
                "avg_price": round(statistics.mean(prices), 2),
                "min_price": round(min(prices), 2),
                "max_price": round(max(prices), 2),
                "market_share_pct": c.market_share_pct,
            })
    return result


@router.get("/dashboard/trends")
async def price_trends(category_id: int = None, competitor_id: int = None, db: AsyncSession = Depends(get_db)):
    """Monthly price trends."""
    q = select(PricePoint)
    if category_id:
        q = q.join(Product, PricePoint.product_id == Product.id).where(Product.category_id == category_id)
    if competitor_id:
        q = q.where(PricePoint.competitor_id == competitor_id)
    q = q.order_by(PricePoint.recorded_at)
    
    result = await db.execute(q)
    points = result.scalars().all()
    
    # Group by month
    monthly = {}
    for p in points:
        if p.price <= 0:
            continue
        key = p.recorded_at.strftime("%Y-%m")
        if key not in monthly:
            monthly[key] = []
        monthly[key].append(p.price)
    
    trends = []
    for period in sorted(monthly.keys()):
        prices = monthly[period]
        trends.append({
            "period": period,
            "avg_price": round(statistics.mean(prices), 2),
            "min_price": round(min(prices), 2),
            "max_price": round(max(prices), 2),
            "data_points": len(prices),
        })
    return trends


@router.get("/dashboard/categories")
async def category_breakdown(db: AsyncSession = Depends(get_db)):
    """Pricing breakdown by category."""
    cats = (await db.execute(select(Category).order_by(Category.name))).scalars().all()
    result = []
    
    for cat in cats:
        prices_q = select(PricePoint.price).join(
            Product, PricePoint.product_id == Product.id
        ).where(Product.category_id == cat.id)
        prices = [p for (p,) in (await db.execute(prices_q)).all() if p > 0]
        
        prod_count = (await db.execute(
            select(func.count(Product.id)).where(Product.category_id == cat.id)
        )).scalar() or 0
        
        comp_count = (await db.execute(
            select(func.count(distinct(Competitor.id))).where(Competitor.category_id == cat.id)
        )).scalar() or 0
        
        if prices:
            result.append({
                "category_name": cat.name,
                "category_id": cat.id,
                "product_count": prod_count,
                "avg_price": round(statistics.mean(prices), 2),
                "price_range": round(max(prices) - min(prices), 2),
                "competitor_count": comp_count,
            })
    return result


@router.get("/dashboard/distribution")
async def price_distribution(category_id: int = None, db: AsyncSession = Depends(get_db)):
    """Price distribution in buckets."""
    q = select(PricePoint.price)
    if category_id:
        q = q.join(Product, PricePoint.product_id == Product.id).where(Product.category_id == category_id)
    
    prices = [p for (p,) in (await db.execute(q)).all() if p > 0]
    if not prices:
        return []
    
    # Latest price per product only
    latest_q = select(PricePoint.product_id, func.max(PricePoint.recorded_at).label("latest"))
    if category_id:
        latest_q = latest_q.join(Product, PricePoint.product_id == Product.id).where(Product.category_id == category_id)
    latest_q = latest_q.group_by(PricePoint.product_id)
    
    buckets = [
        ("$0-10", 0, 10), ("$10-25", 10, 25), ("$25-50", 25, 50),
        ("$50-100", 50, 100), ("$100-200", 100, 200), ("$200-500", 200, 500), ("$500+", 500, 99999),
    ]
    
    total = len(prices)
    result = []
    for label, lo, hi in buckets:
        count = sum(1 for p in prices if lo <= p < hi)
        result.append({"bucket": label, "count": count, "percentage": round(count / total * 100, 1) if total else 0})
    return result


@router.get("/dashboard/alerts")
async def recent_alerts(limit: int = 20, db: AsyncSession = Depends(get_db)):
    """Recent price change alerts."""
    q = select(PriceAlert).order_by(PriceAlert.created_at.desc()).limit(limit)
    alerts = (await db.execute(q)).scalars().all()
    
    # Get competitor names
    comp_ids = list(set(a.competitor_id for a in alerts))
    comps = {}
    if comp_ids:
        comp_result = await db.execute(select(Competitor).where(Competitor.id.in_(comp_ids)))
        comps = {c.id: c.name for c in comp_result.scalars().all()}
    
    return [{
        "id": a.id,
        "product_id": a.product_id,
        "competitor_id": a.competitor_id,
        "competitor_name": comps.get(a.competitor_id, "Unknown"),
        "alert_type": a.alert_type,
        "old_price": a.old_price,
        "new_price": a.new_price,
        "change_pct": a.change_pct,
        "message": a.message,
        "created_at": a.created_at.isoformat(),
    } for a in alerts]


@router.get("/dashboard/events")
async def market_events(db: AsyncSession = Depends(get_db)):
    """Recent market events."""
    q = select(MarketEvent).order_by(MarketEvent.event_date.desc())
    events = (await db.execute(q)).scalars().all()
    return [{
        "id": e.id,
        "title": e.title,
        "description": e.description,
        "event_type": e.event_type,
        "category_id": e.category_id,
        "event_date": e.event_date.isoformat(),
    } for e in events]


@router.get("/dashboard/heatmap")
async def competitor_category_heatmap(db: AsyncSession = Depends(get_db)):
    """Competitor × Category avg price heatmap data."""
    cats = (await db.execute(select(Category).order_by(Category.name))).scalars().all()
    comps = (await db.execute(select(Competitor).order_by(Competitor.name))).scalars().all()
    
    # Build heatmap: for each competitor in each category, get latest avg price
    data = []
    for comp in comps:
        for cat in cats:
            if comp.category_id != cat.id:
                continue
            prices_q = select(PricePoint.price).where(PricePoint.competitor_id == comp.id)
            prices = [p for (p,) in (await db.execute(prices_q)).all() if p > 0]
            if prices:
                data.append({
                    "competitor": comp.name,
                    "category": cat.name,
                    "avg_price": round(statistics.mean(prices), 2),
                    "tier": comp.tier,
                })
    return data
