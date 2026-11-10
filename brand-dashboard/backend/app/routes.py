from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from .database import get_db
from .models import Brand, Platform, Mention, ReputationScore, CrisisEvent, Influencer

router = APIRouter()

@router.get("/dashboard/overview")
async def overview(db: AsyncSession = Depends(get_db)):
    brands = (await db.execute(select(func.count(Brand.id)))).scalar()
    mentions = (await db.execute(select(func.count(Mention.id)))).scalar()
    avg_sent = (await db.execute(select(func.avg(Mention.sentiment_score)))).scalar()
    pos = (await db.execute(select(func.count(Mention.id)).where(Mention.sentiment == "positive"))).scalar()
    neg = (await db.execute(select(func.count(Mention.id)).where(Mention.sentiment == "negative"))).scalar()
    total_reach = (await db.execute(select(func.sum(Mention.reach)))).scalar()
    total_engage = (await db.execute(select(func.sum(Mention.engagement)))).scalar()
    crises = (await db.execute(select(func.count(CrisisEvent.id)))).scalar()
    return {
        "total_brands": brands, "total_mentions": mentions,
        "avg_sentiment": round(avg_sent or 0, 3),
        "positive_pct": round(pos / mentions * 100, 1) if mentions else 0,
        "negative_pct": round(neg / mentions * 100, 1) if mentions else 0,
        "total_reach": total_reach or 0, "total_engagement": total_engage or 0,
        "active_crises": crises,
    }

@router.get("/dashboard/brand-scores")
async def brand_scores(db: AsyncSession = Depends(get_db)):
    latest = (await db.execute(select(func.max(ReputationScore.month)))).scalar()
    q = select(Brand.name, Brand.logo_emoji, Brand.industry, ReputationScore).join(
        ReputationScore, Brand.id == ReputationScore.brand_id
    ).where(ReputationScore.month == latest).order_by(desc(ReputationScore.overall_score))
    rows = (await db.execute(q)).all()
    return [{"brand": r.name, "emoji": r.logo_emoji, "industry": r.industry,
             "score": r.ReputationScore.overall_score, "positive_pct": r.ReputationScore.positive_pct,
             "negative_pct": r.ReputationScore.negative_pct, "mentions": r.ReputationScore.total_mentions,
             "reach": r.ReputationScore.total_reach, "engagement": r.ReputationScore.avg_engagement}
            for r in rows]

@router.get("/dashboard/sentiment-trends")
async def sentiment_trends(brand_id: int = Query(None), db: AsyncSession = Depends(get_db)):
    q = select(ReputationScore.month,
               func.avg(ReputationScore.overall_score).label("score"),
               func.avg(ReputationScore.positive_pct).label("pos"),
               func.avg(ReputationScore.negative_pct).label("neg"),
               func.sum(ReputationScore.total_mentions).label("mentions"))
    if brand_id:
        q = q.where(ReputationScore.brand_id == brand_id)
    q = q.group_by(ReputationScore.month).order_by(ReputationScore.month)
    rows = (await db.execute(q)).all()
    return [{"month": r.month, "score": round(r.score, 1), "positive_pct": round(r.pos, 1),
             "negative_pct": round(r.neg, 1), "mentions": r.mentions} for r in rows]

@router.get("/dashboard/platform-breakdown")
async def platform_breakdown(db: AsyncSession = Depends(get_db)):
    q = select(Platform.name, Platform.icon,
               func.count(Mention.id).label("count"),
               func.avg(Mention.sentiment_score).label("sentiment"),
               func.sum(Mention.reach).label("reach")
    ).join(Mention, Platform.id == Mention.platform_id).group_by(Platform.id).order_by(desc("count"))
    rows = (await db.execute(q)).all()
    return [{"platform": r.name, "icon": r.icon, "count": r.count,
             "sentiment": round(r.sentiment, 3), "reach": r.reach} for r in rows]

@router.get("/dashboard/topics")
async def topic_analysis(db: AsyncSession = Depends(get_db)):
    q = select(Mention.topic,
               func.count(Mention.id).label("count"),
               func.avg(Mention.sentiment_score).label("sentiment"),
               func.sum(Mention.engagement).label("engagement")
    ).group_by(Mention.topic).order_by(desc("count"))
    rows = (await db.execute(q)).all()
    return [{"topic": r.topic, "count": r.count, "sentiment": round(r.sentiment, 3),
             "engagement": r.engagement} for r in rows]

@router.get("/dashboard/crises")
async def crises(db: AsyncSession = Depends(get_db)):
    q = select(CrisisEvent, Brand.name.label("brand_name")).join(
        Brand, CrisisEvent.brand_id == Brand.id
    ).order_by(desc(CrisisEvent.date)).limit(15)
    rows = (await db.execute(q)).all()
    return [{"title": r.CrisisEvent.title, "brand": r.brand_name,
             "severity": r.CrisisEvent.severity, "date": r.CrisisEvent.date.strftime("%Y-%m-%d"),
             "description": r.CrisisEvent.description, "status": r.CrisisEvent.resolution_status,
             "impact": r.CrisisEvent.sentiment_impact} for r in rows]

@router.get("/dashboard/influencers")
async def influencers(brand_id: int = Query(None), db: AsyncSession = Depends(get_db)):
    q = select(Influencer, Brand.name.label("brand_name")).join(Brand, Influencer.brand_id == Brand.id)
    if brand_id:
        q = q.where(Influencer.brand_id == brand_id)
    q = q.order_by(desc(Influencer.influence_score)).limit(20)
    rows = (await db.execute(q)).all()
    return [{"name": r.Influencer.name, "platform": r.Influencer.platform,
             "followers": r.Influencer.followers, "sentiment": r.Influencer.sentiment_toward_brand,
             "score": r.Influencer.influence_score, "brand": r.brand_name} for r in rows]

@router.get("/dashboard/recent-mentions")
async def recent_mentions(db: AsyncSession = Depends(get_db)):
    q = select(Mention, Brand.name.label("brand_name"), Platform.name.label("platform_name")).join(
        Brand, Mention.brand_id == Brand.id).join(Platform, Mention.platform_id == Platform.id
    ).order_by(desc(Mention.date)).limit(20)
    rows = (await db.execute(q)).all()
    return [{"content": r.Mention.content, "brand": r.brand_name, "platform": r.platform_name,
             "sentiment": r.Mention.sentiment, "score": r.Mention.sentiment_score,
             "reach": r.Mention.reach, "engagement": r.Mention.engagement,
             "date": r.Mention.date.strftime("%Y-%m-%d"), "topic": r.Mention.topic} for r in rows]

@router.get("/brands")
async def list_brands(db: AsyncSession = Depends(get_db)):
    rows = (await db.execute(select(Brand))).scalars().all()
    return [{"id": b.id, "name": b.name, "emoji": b.logo_emoji} for b in rows]
