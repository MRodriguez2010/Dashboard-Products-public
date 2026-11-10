from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, case
from .database import get_db
from .models import Plan, Subscriber, Activity, RevenueMetric, ChurnReason

router = APIRouter()


@router.get("/dashboard/overview")
async def overview(db: AsyncSession = Depends(get_db)):
    total = (await db.execute(select(func.count(Subscriber.id)))).scalar()
    active = (await db.execute(select(func.count(Subscriber.id)).where(Subscriber.is_churned == False))).scalar()
    churned = total - active
    total_mrr = (await db.execute(select(func.sum(Subscriber.mrr)).where(Subscriber.is_churned == False))).scalar()
    avg_health = (await db.execute(select(func.avg(Subscriber.health_score)).where(Subscriber.is_churned == False))).scalar()
    avg_ltv = (await db.execute(select(func.avg(Subscriber.lifetime_value)))).scalar()
    high_risk = (await db.execute(select(func.count(Subscriber.id)).where(Subscriber.churn_risk > 0.5, Subscriber.is_churned == False))).scalar()
    at_risk_mrr = (await db.execute(select(func.sum(Subscriber.mrr)).where(Subscriber.churn_risk > 0.5, Subscriber.is_churned == False))).scalar()
    return {
        "total_subscribers": total, "active_subscribers": active,
        "churned_subscribers": churned, "churn_rate": round(churned / total * 100, 1) if total else 0,
        "total_mrr": round(total_mrr or 0, 2), "avg_health_score": round(avg_health or 0, 1),
        "avg_ltv": round(avg_ltv or 0, 2), "high_risk_count": high_risk,
        "at_risk_mrr": round(at_risk_mrr or 0, 2),
    }


@router.get("/dashboard/revenue-trends")
async def revenue_trends(db: AsyncSession = Depends(get_db)):
    q = select(RevenueMetric).order_by(RevenueMetric.month)
    rows = (await db.execute(q)).scalars().all()
    return [
        {"month": r.month, "mrr": r.mrr, "new_mrr": r.new_mrr, "churned_mrr": r.churned_mrr,
         "expansion_mrr": r.expansion_mrr, "net_mrr": r.net_mrr,
         "active_subscribers": r.active_subscribers, "churn_rate": r.churn_rate,
         "revenue_churn_rate": r.revenue_churn_rate}
        for r in rows
    ]


@router.get("/dashboard/churn-reasons")
async def churn_reasons(db: AsyncSession = Depends(get_db)):
    q = select(ChurnReason).order_by(desc(ChurnReason.count))
    rows = (await db.execute(q)).scalars().all()
    return [{"reason": r.reason, "count": r.count, "revenue_lost": r.revenue_lost, "category": r.category} for r in rows]


@router.get("/dashboard/plan-breakdown")
async def plan_breakdown(db: AsyncSession = Depends(get_db)):
    q = select(
        Plan.name, Plan.price_monthly, Plan.tier,
        func.count(Subscriber.id).label("total"),
        func.sum(case((Subscriber.is_churned == True, 1), else_=0)).label("churned"),
        func.avg(Subscriber.health_score).label("avg_health"),
        func.avg(Subscriber.churn_risk).label("avg_risk"),
        func.sum(case((Subscriber.is_churned == False, Subscriber.mrr), else_=0)).label("mrr"),
    ).join(Subscriber, Plan.id == Subscriber.plan_id).group_by(Plan.id).order_by(Plan.price_monthly)
    rows = (await db.execute(q)).all()
    return [
        {"plan": r.name, "price": r.price_monthly, "tier": r.tier, "total": r.total,
         "churned": r.churned, "churn_rate": round(r.churned / r.total * 100, 1) if r.total else 0,
         "avg_health": round(r.avg_health, 1), "avg_risk": round(r.avg_risk, 3),
         "mrr": round(r.mrr, 2)}
        for r in rows
    ]


@router.get("/dashboard/at-risk")
async def at_risk_subscribers(limit: int = 20, db: AsyncSession = Depends(get_db)):
    q = select(
        Subscriber.email, Subscriber.company, Subscriber.mrr,
        Subscriber.churn_risk, Subscriber.health_score, Subscriber.usage_score,
        Subscriber.last_login_days, Subscriber.feature_adoption, Plan.name.label("plan")
    ).join(Plan).where(
        Subscriber.is_churned == False, Subscriber.churn_risk > 0.3
    ).order_by(desc(Subscriber.churn_risk)).limit(limit)
    rows = (await db.execute(q)).all()
    return [
        {"email": r.email, "company": r.company, "mrr": r.mrr, "plan": r.plan,
         "churn_risk": round(r.churn_risk, 3), "health_score": round(r.health_score, 1),
         "usage_score": round(r.usage_score, 1), "last_login_days": r.last_login_days,
         "feature_adoption": round(r.feature_adoption, 1)}
        for r in rows
    ]


@router.get("/dashboard/cohort")
async def cohort_analysis(db: AsyncSession = Depends(get_db)):
    """Monthly signup cohort retention."""
    q = select(
        func.strftime("%Y-%m", Subscriber.signup_date).label("cohort"),
        func.count(Subscriber.id).label("total"),
        func.sum(case((Subscriber.is_churned == True, 1), else_=0)).label("churned"),
    ).group_by("cohort").order_by("cohort")
    rows = (await db.execute(q)).all()
    return [
        {"cohort": r.cohort, "total": r.total, "churned": r.churned,
         "retained": r.total - r.churned,
         "retention_rate": round((r.total - r.churned) / r.total * 100, 1) if r.total else 0}
        for r in rows
    ]


@router.get("/dashboard/health-distribution")
async def health_distribution(db: AsyncSession = Depends(get_db)):
    buckets = [(0, 20, "Critical"), (20, 40, "Poor"), (40, 60, "Fair"), (60, 80, "Good"), (80, 101, "Excellent")]
    result = []
    for lo, hi, label in buckets:
        count = (await db.execute(
            select(func.count(Subscriber.id)).where(
                Subscriber.is_churned == False,
                Subscriber.health_score >= lo, Subscriber.health_score < hi)
        )).scalar()
        result.append({"label": label, "range": f"{lo}-{hi-1}", "count": count})
    return result


@router.get("/dashboard/engagement-trends")
async def engagement_trends(db: AsyncSession = Depends(get_db)):
    q = select(
        Activity.month,
        func.avg(Activity.engagement_score).label("engagement"),
        func.avg(Activity.logins).label("logins"),
        func.avg(Activity.api_calls).label("api_calls"),
        func.avg(Activity.features_used).label("features"),
    ).group_by(Activity.month).order_by(Activity.month)
    rows = (await db.execute(q)).all()
    return [
        {"month": r.month, "engagement": round(r.engagement, 1),
         "logins": round(r.logins, 1), "api_calls": round(r.api_calls, 0),
         "features": round(r.features, 1)}
        for r in rows
    ]


@router.get("/plans")
async def list_plans(db: AsyncSession = Depends(get_db)):
    rows = (await db.execute(select(Plan))).scalars().all()
    return [{"id": p.id, "name": p.name, "price": p.price_monthly, "tier": p.tier} for p in rows]
