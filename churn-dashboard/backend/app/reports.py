from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, case
from pydantic import BaseModel
import io
from .database import get_db
from .models import Plan, Subscriber, RevenueMetric, ChurnReason

router = APIRouter()

class ReportRequest(BaseModel):
    format: str = "pdf"

async def _get_data(db: AsyncSession):
    total = (await db.execute(select(func.count(Subscriber.id)))).scalar()
    active = (await db.execute(select(func.count(Subscriber.id)).where(Subscriber.is_churned == False))).scalar()
    mrr = (await db.execute(select(func.sum(Subscriber.mrr)).where(Subscriber.is_churned == False))).scalar()
    
    plans = (await db.execute(
        select(Plan.name, func.count(Subscriber.id).label("cnt"),
               func.sum(case((Subscriber.is_churned == True, 1), else_=0)).label("churned"))
        .join(Subscriber).group_by(Plan.id)
    )).all()
    
    reasons = (await db.execute(select(ChurnReason).order_by(desc(ChurnReason.count)).limit(8))).scalars().all()
    
    revenue = (await db.execute(select(RevenueMetric).order_by(RevenueMetric.month))).scalars().all()
    
    return {"total": total, "active": active, "churned": total - active, "mrr": round(mrr or 0, 2),
            "plans": [{"name": p.name, "count": p.cnt, "churned": p.churned} for p in plans],
            "reasons": [{"reason": r.reason, "count": r.count, "lost": r.revenue_lost} for r in reasons],
            "revenue": [{"month": r.month, "mrr": r.mrr, "churn_rate": r.churn_rate} for r in revenue]}

@router.post("/reports/generate")
async def generate_report(req: ReportRequest, db: AsyncSession = Depends(get_db)):
    data = await _get_data(db)
    if req.format == "pdf": return _pdf(data)
    elif req.format == "pptx": return _pptx(data)
    elif req.format == "xlsx": return _xlsx(data)
    return {"error": "Unsupported"}

def _pdf(data):
    from reportlab.lib.pagesizes import letter
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=letter)
    styles = getSampleStyleSheet()
    story = [
        Paragraph("Subscription Churn & Revenue Leak Report", styles["Title"]),
        Spacer(1, 12),
        Paragraph(f"Total Subscribers: {data['total']} | Active: {data['active']} | Churned: {data['churned']} | MRR: ${data['mrr']:,.0f}", styles["Normal"]),
        Spacer(1, 20),
        Paragraph("Plan Breakdown", styles["Heading2"]),
    ]
    t_data = [["Plan", "Total", "Churned", "Churn %"]]
    for p in data["plans"]:
        rate = round(p["churned"] / p["count"] * 100, 1) if p["count"] else 0
        t_data.append([p["name"], str(p["count"]), str(p["churned"]), f"{rate}%"])
    t = Table(t_data, colWidths=[150, 80, 80, 80])
    t.setStyle(TableStyle([("BACKGROUND", (0,0), (-1,0), colors.HexColor("#7c3aed")), ("TEXTCOLOR", (0,0), (-1,0), colors.white), ("GRID", (0,0), (-1,-1), 0.5, colors.grey)]))
    story.append(t)
    story.append(Spacer(1, 20))
    story.append(Paragraph("Top Churn Reasons", styles["Heading2"]))
    r_data = [["Reason", "Count", "Revenue Lost"]]
    for r in data["reasons"]:
        r_data.append([r["reason"], str(r["count"]), f"${r['lost']:,.0f}"])
    t2 = Table(r_data, colWidths=[200, 80, 120])
    t2.setStyle(TableStyle([("BACKGROUND", (0,0), (-1,0), colors.HexColor("#dc2626")), ("TEXTCOLOR", (0,0), (-1,0), colors.white), ("GRID", (0,0), (-1,-1), 0.5, colors.grey)]))
    story.append(t2)
    doc.build(story)
    buf.seek(0)
    return StreamingResponse(buf, media_type="application/pdf", headers={"Content-Disposition": "attachment; filename=churn_report.pdf"})

def _pptx(data):
    from pptx import Presentation
    from pptx.util import Inches, Pt
    from pptx.dml.color import RGBColor
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    tx = slide.shapes.add_textbox(Inches(1), Inches(2), Inches(11), Inches(3))
    p = tx.text_frame.paragraphs[0]
    p.text = "Subscription Churn & Revenue Leak"
    p.font.size = Pt(40); p.font.bold = True; p.font.color.rgb = RGBColor(0x7C, 0x3A, 0xED)
    p2 = tx.text_frame.add_paragraph()
    p2.text = f"Active: {data['active']} | Churned: {data['churned']} | MRR: ${data['mrr']:,.0f}"
    p2.font.size = Pt(18)
    
    slide2 = prs.slides.add_slide(prs.slide_layouts[6])
    rows = len(data["reasons"]) + 1
    tbl = slide2.shapes.add_table(rows, 3, Inches(1), Inches(1.5), Inches(10), Inches(0.4*rows)).table
    for i, h in enumerate(["Reason", "Count", "Revenue Lost"]): tbl.cell(0, i).text = h
    for i, r in enumerate(data["reasons"]): 
        tbl.cell(i+1, 0).text = r["reason"]; tbl.cell(i+1, 1).text = str(r["count"]); tbl.cell(i+1, 2).text = f"${r['lost']:,.0f}"
    
    buf = io.BytesIO(); prs.save(buf); buf.seek(0)
    return StreamingResponse(buf, media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation", headers={"Content-Disposition": "attachment; filename=churn_report.pptx"})

def _xlsx(data):
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill
    wb = Workbook()
    hf = Font(bold=True, color="FFFFFF"); hfill = PatternFill(start_color="7C3AED", end_color="7C3AED", fill_type="solid")
    ws = wb.active; ws.title = "Overview"
    for i, h in enumerate(["Metric", "Value"], 1): ws.cell(1, i, h).font = hf; ws.cell(1, i).fill = hfill
    for i, (k, v) in enumerate([("Total Subscribers", data["total"]), ("Active", data["active"]), ("Churned", data["churned"]), ("MRR", data["mrr"])], 2):
        ws.cell(i, 1, k); ws.cell(i, 2, v)
    
    ws2 = wb.create_sheet("Plans")
    for i, h in enumerate(["Plan", "Total", "Churned"], 1): ws2.cell(1, i, h).font = hf; ws2.cell(1, i).fill = hfill
    for i, p in enumerate(data["plans"], 2): ws2.cell(i, 1, p["name"]); ws2.cell(i, 2, p["count"]); ws2.cell(i, 3, p["churned"])
    
    ws3 = wb.create_sheet("Revenue Trend")
    for i, h in enumerate(["Month", "MRR", "Churn Rate %"], 1): ws3.cell(1, i, h).font = hf; ws3.cell(1, i).fill = hfill
    for i, r in enumerate(data["revenue"], 2): ws3.cell(i, 1, r["month"]); ws3.cell(i, 2, r["mrr"]); ws3.cell(i, 3, r["churn_rate"])
    
    buf = io.BytesIO(); wb.save(buf); buf.seek(0)
    return StreamingResponse(buf, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", headers={"Content-Disposition": "attachment; filename=churn_report.xlsx"})
