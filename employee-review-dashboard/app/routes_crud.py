"""API routes for companies and reviews."""
import json
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, case, text
from app.database import get_db
from app.models import Company, Review
from app.schemas import CompanyCreate, CompanyResponse, ReviewCreate, ReviewResponse
from app.sentiment import analyze_review

router = APIRouter()


# ──── Companies ────

@router.get("/companies", response_model=list[CompanyResponse])
async def list_companies(db: AsyncSession = Depends(get_db)):
    """List all companies with review stats."""
    result = await db.execute(
        select(
            Company,
            func.count(Review.id).label("review_count"),
            func.avg(Review.overall_sentiment).label("avg_sentiment"),
            func.avg(Review.rating).label("avg_rating"),
        )
        .outerjoin(Review)
        .group_by(Company.id)
        .order_by(Company.name)
    )
    rows = result.all()
    return [
        CompanyResponse(
            id=row[0].id, name=row[0].name, industry=row[0].industry,
            size=row[0].size, logo_url=row[0].logo_url, website=row[0].website,
            review_count=row[1], avg_sentiment=round(row[2], 4) if row[2] else None,
            avg_rating=round(row[3], 2) if row[3] else None,
        )
        for row in rows
    ]


@router.post("/companies", response_model=CompanyResponse)
async def create_company(data: CompanyCreate, db: AsyncSession = Depends(get_db)):
    company = Company(**data.model_dump())
    db.add(company)
    await db.commit()
    await db.refresh(company)
    return CompanyResponse(id=company.id, name=company.name, industry=company.industry,
                           size=company.size, logo_url=company.logo_url, website=company.website)


@router.get("/companies/{company_id}", response_model=CompanyResponse)
async def get_company(company_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(
            Company,
            func.count(Review.id).label("review_count"),
            func.avg(Review.overall_sentiment).label("avg_sentiment"),
            func.avg(Review.rating).label("avg_rating"),
        )
        .outerjoin(Review)
        .where(Company.id == company_id)
        .group_by(Company.id)
    )
    row = result.first()
    if not row:
        raise HTTPException(status_code=404, detail="Company not found")
    return CompanyResponse(
        id=row[0].id, name=row[0].name, industry=row[0].industry,
        size=row[0].size, logo_url=row[0].logo_url, website=row[0].website,
        review_count=row[1], avg_sentiment=round(row[2], 4) if row[2] else None,
        avg_rating=round(row[3], 2) if row[3] else None,
    )


# ──── Reviews ────

@router.post("/reviews", response_model=ReviewResponse)
async def create_review(data: ReviewCreate, db: AsyncSession = Depends(get_db)):
    """Create a review and auto-compute sentiment."""
    # Verify company exists
    company = await db.get(Company, data.company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    # Analyze sentiment
    analysis = analyze_review(
        title=data.title or "",
        pros=data.pros or "",
        cons=data.cons or "",
        review_text=data.review_text or "",
    )

    review = Review(
        **data.model_dump(),
        overall_sentiment=analysis["overall_sentiment"],
        pros_sentiment=analysis["pros_sentiment"],
        cons_sentiment=analysis["cons_sentiment"],
        topics=json.dumps(analysis["topics"]),
    )
    if not review.review_date:
        review.review_date = datetime.utcnow()

    db.add(review)
    await db.commit()
    await db.refresh(review)
    return review


@router.post("/reviews/bulk", response_model=dict)
async def bulk_create_reviews(reviews: list[ReviewCreate], db: AsyncSession = Depends(get_db)):
    """Bulk import reviews with auto-sentiment."""
    created = 0
    for data in reviews:
        analysis = analyze_review(
            title=data.title or "", pros=data.pros or "",
            cons=data.cons or "", review_text=data.review_text or "",
        )
        review = Review(
            **data.model_dump(),
            overall_sentiment=analysis["overall_sentiment"],
            pros_sentiment=analysis["pros_sentiment"],
            cons_sentiment=analysis["cons_sentiment"],
            topics=json.dumps(analysis["topics"]),
        )
        if not review.review_date:
            review.review_date = datetime.utcnow()
        db.add(review)
        created += 1

    await db.commit()
    return {"created": created}


@router.get("/reviews", response_model=list[ReviewResponse])
async def list_reviews(
    company_id: Optional[int] = None,
    source: Optional[str] = None,
    limit: int = Query(100, le=1000),
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
):
    query = select(Review).order_by(Review.review_date.desc())
    if company_id:
        query = query.where(Review.company_id == company_id)
    if source:
        query = query.where(Review.source == source)
    query = query.limit(limit).offset(offset)
    result = await db.execute(query)
    return result.scalars().all()
