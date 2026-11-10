"""Dashboard analytics routes — aggregations, trends, comparisons."""
import json
from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, case, text, extract
from app.database import get_db
from app.models import Company, Review, Event
from app.schemas import SentimentOverview, SentimentTrend, TopicBreakdown, CompanyComparison
from app.config import SENTIMENT_POSITIVE_THRESHOLD, SENTIMENT_NEGATIVE_THRESHOLD

router = APIRouter()


def _build_filters(company_ids=None, sources=None, date_from=None, date_to=None):
    """Build SQLAlchemy filter conditions."""
    conditions = []
    if company_ids:
        conditions.append(Review.company_id.in_(company_ids))
    if sources:
        conditions.append(Review.source.in_(sources))
    if date_from:
        conditions.append(Review.review_date >= date_from)
    if date_to:
        conditions.append(Review.review_date <= date_to)
    return conditions


@router.get("/dashboard/overview", response_model=SentimentOverview)
async def dashboard_overview(
    company_ids: Optional[str] = Query(None, description="Comma-separated company IDs"),
    sources: Optional[str] = Query(None, description="Comma-separated sources"),
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    db: AsyncSession = Depends(get_db),
):
    """Get top-level KPIs for the dashboard."""
    cids = [int(x) for x in company_ids.split(",")] if company_ids else None
    src_list = sources.split(",") if sources else None
    filters = _build_filters(cids, src_list, date_from, date_to)

    # Total companies
    co_query = select(func.count(func.distinct(Review.company_id)))
    if filters:
        co_query = co_query.where(and_(*filters))
    total_companies = (await db.execute(co_query)).scalar() or 0

    # Review stats
    stats_query = select(
        func.count(Review.id),
        func.avg(Review.overall_sentiment),
        func.avg(Review.rating),
        func.sum(case((Review.overall_sentiment > SENTIMENT_POSITIVE_THRESHOLD, 1), else_=0)),
        func.sum(case((Review.overall_sentiment < SENTIMENT_NEGATIVE_THRESHOLD, 1), else_=0)),
        func.sum(case((and_(
            Review.overall_sentiment >= SENTIMENT_NEGATIVE_THRESHOLD,
            Review.overall_sentiment <= SENTIMENT_POSITIVE_THRESHOLD
        ), 1), else_=0)),
    )
    if filters:
        stats_query = stats_query.where(and_(*filters))
    row = (await db.execute(stats_query)).first()

    total_reviews = row[0] or 0
    avg_sentiment = round(row[1] or 0, 4)
    avg_rating = round(row[2] or 0, 2)
    pos = row[3] or 0
    neg = row[4] or 0
    neu = row[5] or 0

    total = pos + neg + neu if (pos + neg + neu) > 0 else 1
    positive_pct = round(pos / total * 100, 1)
    negative_pct = round(neg / total * 100, 1)
    neutral_pct = round(neu / total * 100, 1)

    # Trending topics
    topics_result = await _get_topic_breakdown(db, filters, limit=8)

    return SentimentOverview(
        total_companies=total_companies,
        total_reviews=total_reviews,
        avg_sentiment=avg_sentiment,
        positive_pct=positive_pct,
        negative_pct=negative_pct,
        neutral_pct=neutral_pct,
        avg_rating=avg_rating,
        trending_topics=topics_result,
    )


@router.get("/dashboard/trends", response_model=list[SentimentTrend])
async def sentiment_trends(
    company_ids: Optional[str] = Query(None),
    sources: Optional[str] = Query(None),
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    granularity: str = Query("monthly", regex="^(daily|weekly|monthly)$"),
    db: AsyncSession = Depends(get_db),
):
    """Get sentiment over time."""
    cids = [int(x) for x in company_ids.split(",")] if company_ids else None
    src_list = sources.split(",") if sources else None
    filters = _build_filters(cids, src_list, date_from, date_to)

    if granularity == "daily":
        date_trunc = func.date(Review.review_date)
    elif granularity == "weekly":
        # SQLite: group by year-week
        date_trunc = func.strftime("%Y-W%W", Review.review_date)
    else:
        date_trunc = func.strftime("%Y-%m", Review.review_date)

    query = (
        select(
            date_trunc.label("period"),
            func.avg(Review.overall_sentiment).label("avg_sentiment"),
            func.count(Review.id).label("review_count"),
            func.avg(Review.rating).label("avg_rating"),
        )
        .group_by("period")
        .order_by("period")
    )
    if filters:
        query = query.where(and_(*filters))

    result = await db.execute(query)
    return [
        SentimentTrend(
            period=str(row[0]),
            avg_sentiment=round(row[1], 4),
            review_count=row[2],
            avg_rating=round(row[3], 2) if row[3] else None,
        )
        for row in result.all()
    ]


@router.get("/dashboard/topics", response_model=list[TopicBreakdown])
async def topic_breakdown(
    company_ids: Optional[str] = Query(None),
    sources: Optional[str] = Query(None),
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    db: AsyncSession = Depends(get_db),
):
    """Get sentiment broken down by topic."""
    cids = [int(x) for x in company_ids.split(",")] if company_ids else None
    src_list = sources.split(",") if sources else None
    filters = _build_filters(cids, src_list, date_from, date_to)

    topics_result = await _get_topic_breakdown(db, filters)
    return [
        TopicBreakdown(
            topic=t["topic"], count=t["count"],
            avg_sentiment=t["avg_sentiment"],
            positive_pct=t.get("positive_pct", 0),
            negative_pct=t.get("negative_pct", 0),
        )
        for t in topics_result
    ]


@router.get("/dashboard/companies", response_model=list[CompanyComparison])
async def company_comparison(
    company_ids: Optional[str] = Query(None),
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    db: AsyncSession = Depends(get_db),
):
    """Compare companies by sentiment."""
    cids = [int(x) for x in company_ids.split(",")] if company_ids else None
    filters = _build_filters(cids, None, date_from, date_to)

    query = (
        select(
            Company.name,
            func.avg(Review.overall_sentiment).label("avg_sentiment"),
            func.avg(Review.rating).label("avg_rating"),
            func.count(Review.id).label("review_count"),
        )
        .join(Review)
        .group_by(Company.id)
        .order_by(func.avg(Review.overall_sentiment).desc())
    )
    if filters:
        query = query.where(and_(*filters))

    result = await db.execute(query)
    return [
        CompanyComparison(
            company_name=row[0],
            avg_sentiment=round(row[1], 4),
            avg_rating=round(row[2], 2) if row[2] else 0,
            review_count=row[3],
            trend="stable",  # TODO: compute from recent vs historical
        )
        for row in result.all()
    ]


@router.get("/dashboard/events")
async def get_events(
    company_id: Optional[int] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    db: AsyncSession = Depends(get_db),
):
    """Get events for timeline overlay."""
    query = select(Event).order_by(Event.event_date.desc())
    conditions = []
    if company_id:
        conditions.append((Event.company_id == company_id) | (Event.company_id.is_(None)))
    if date_from:
        conditions.append(Event.event_date >= date_from)
    if date_to:
        conditions.append(Event.event_date <= date_to)
    if conditions:
        query = query.where(and_(*conditions))

    result = await db.execute(query)
    events = result.scalars().all()
    return [
        {
            "id": e.id, "company_id": e.company_id, "event_type": e.event_type,
            "title": e.title, "description": e.description,
            "event_date": e.event_date.isoformat() if e.event_date else None,
            "source_url": e.source_url,
        }
        for e in events
    ]


async def _get_topic_breakdown(db: AsyncSession, filters: list, limit: int = 20) -> list[dict]:
    """Extract topic stats from reviews. Since topics are JSON in a text field,
    we need to pull reviews and aggregate in Python."""
    query = select(Review.topics, Review.overall_sentiment)
    if filters:
        query = query.where(and_(*filters))

    result = await db.execute(query)
    rows = result.all()

    topic_stats: dict = {}
    for topics_json, sentiment in rows:
        if not topics_json:
            continue
        try:
            topics = json.loads(topics_json)
        except (json.JSONDecodeError, TypeError):
            continue

        for topic in topics:
            if topic not in topic_stats:
                topic_stats[topic] = {"count": 0, "total_sentiment": 0, "positive": 0, "negative": 0}
            topic_stats[topic]["count"] += 1
            topic_stats[topic]["total_sentiment"] += sentiment or 0
            if sentiment and sentiment > SENTIMENT_POSITIVE_THRESHOLD:
                topic_stats[topic]["positive"] += 1
            elif sentiment and sentiment < SENTIMENT_NEGATIVE_THRESHOLD:
                topic_stats[topic]["negative"] += 1

    results = []
    for topic, stats in sorted(topic_stats.items(), key=lambda x: x[1]["count"], reverse=True)[:limit]:
        count = stats["count"]
        results.append({
            "topic": topic,
            "count": count,
            "avg_sentiment": round(stats["total_sentiment"] / count, 4) if count else 0,
            "positive_pct": round(stats["positive"] / count * 100, 1) if count else 0,
            "negative_pct": round(stats["negative"] / count * 100, 1) if count else 0,
        })

    return results
