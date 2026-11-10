"""Report generation routes."""
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.schemas import ReportRequest
from app.routes_dashboard import dashboard_overview, sentiment_trends, topic_breakdown, company_comparison
from app.reports import generate_pdf_report, generate_pptx_report, generate_xlsx_report

router = APIRouter()


async def _gather_report_data(req: ReportRequest, db: AsyncSession) -> dict:
    """Gather all data needed for report generation."""
    cids_str = ",".join(str(x) for x in req.company_ids) if req.company_ids else None

    overview = await dashboard_overview(
        company_ids=cids_str, sources=None,
        date_from=req.date_from, date_to=req.date_to, db=db,
    )
    trends = await sentiment_trends(
        company_ids=cids_str, sources=None,
        date_from=req.date_from, date_to=req.date_to,
        granularity="monthly", db=db,
    )
    topics = await topic_breakdown(
        company_ids=cids_str, sources=None,
        date_from=req.date_from, date_to=req.date_to, db=db,
    )
    companies = await company_comparison(
        company_ids=cids_str,
        date_from=req.date_from, date_to=req.date_to, db=db,
    )

    return {
        "overview": overview.model_dump(),
        "trends": [t.model_dump() for t in trends],
        "topics": [t.model_dump() for t in topics],
        "companies": [c.model_dump() for c in companies],
        "company_names": [c.company_name for c in companies],
    }


@router.post("/reports/generate")
async def generate_report(req: ReportRequest, db: AsyncSession = Depends(get_db)):
    """Generate a downloadable report."""
    data = await _gather_report_data(req, db)

    if req.format == "pdf":
        buffer = generate_pdf_report(data)
        return StreamingResponse(
            buffer, media_type="application/pdf",
            headers={"Content-Disposition": "attachment; filename=esa-report.pdf"},
        )
    elif req.format == "pptx":
        buffer = generate_pptx_report(data)
        return StreamingResponse(
            buffer, media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
            headers={"Content-Disposition": "attachment; filename=esa-report.pptx"},
        )
    elif req.format == "xlsx":
        buffer = generate_xlsx_report(data)
        return StreamingResponse(
            buffer, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": "attachment; filename=esa-report.xlsx"},
        )
    else:
        return {"error": f"Unsupported format: {req.format}"}
