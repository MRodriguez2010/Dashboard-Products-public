from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from pydantic import BaseModel
import io
from .database import get_db
from .models import Brand, Mention, ReputationScore, CrisisEvent

router = APIRouter()

class ReportRequest(BaseModel):
    format: str = "pdf"

async def _data(db):
    latest = (await db.execute(select(func.max(ReputationScore.month)))).scalar()
    brands_q = select(Brand.name, ReputationScore.overall_score, ReputationScore.positive_pct,
                      ReputationScore.negative_pct, ReputationScore.total_mentions
    ).join(ReputationScore, Brand.id == ReputationScore.brand_id).where(ReputationScore.month == latest).order_by(desc(ReputationScore.overall_score))
    brands = (await db.execute(brands_q)).all()
    crises = (await db.execute(select(CrisisEvent, Brand.name.label("bn")).join(Brand).order_by(desc(CrisisEvent.date)).limit(10))).all()
    total = (await db.execute(select(func.count(Mention.id)))).scalar()
    return {"brands": [{"name": b.name, "score": b.overall_score, "pos": b.positive_pct, "neg": b.negative_pct, "mentions": b.total_mentions} for b in brands],
            "crises": [{"title": c.CrisisEvent.title, "brand": c.bn, "severity": c.CrisisEvent.severity, "date": c.CrisisEvent.date.strftime("%Y-%m-%d")} for c in crises],
            "total_mentions": total, "month": latest}

@router.post("/reports/generate")
async def gen(req: ReportRequest, db: AsyncSession = Depends(get_db)):
    d = await _data(db)
    if req.format == "pdf": return _pdf(d)
    elif req.format == "pptx": return _pptx(d)
    elif req.format == "xlsx": return _xlsx(d)

def _pdf(d):
    from reportlab.lib.pagesizes import letter; from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet
    buf = io.BytesIO(); doc = SimpleDocTemplate(buf, pagesize=letter); styles = getSampleStyleSheet()
    story = [Paragraph("Brand Reputation & Social Sentiment Report", styles["Title"]), Spacer(1,12),
             Paragraph(f"Period: {d['month']} | Total Mentions Analyzed: {d['total_mentions']}", styles["Normal"]), Spacer(1,20),
             Paragraph("Brand Reputation Scores", styles["Heading2"])]
    t_data = [["Brand", "Score", "Positive %", "Negative %", "Mentions"]]
    for b in d["brands"]: t_data.append([b["name"], str(b["score"]), f"{b['pos']}%", f"{b['neg']}%", str(b["mentions"])])
    t = Table(t_data, colWidths=[140, 60, 80, 80, 70])
    t.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,0),colors.HexColor("#0ea5e9")),("TEXTCOLOR",(0,0),(-1,0),colors.white),("GRID",(0,0),(-1,-1),0.5,colors.grey),("FONTSIZE",(0,0),(-1,-1),9)]))
    story.append(t); story.append(Spacer(1,20))
    story.append(Paragraph("Recent Crisis Events", styles["Heading2"]))
    c_data = [["Event", "Brand", "Severity", "Date"]]
    for c in d["crises"]: c_data.append([c["title"][:40], c["brand"], c["severity"], c["date"]])
    t2 = Table(c_data, colWidths=[180, 100, 80, 80])
    t2.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,0),colors.HexColor("#ef4444")),("TEXTCOLOR",(0,0),(-1,0),colors.white),("GRID",(0,0),(-1,-1),0.5,colors.grey),("FONTSIZE",(0,0),(-1,-1),9)]))
    story.append(t2); doc.build(story); buf.seek(0)
    return StreamingResponse(buf, media_type="application/pdf", headers={"Content-Disposition": "attachment; filename=brand_report.pdf"})

def _pptx(d):
    from pptx import Presentation; from pptx.util import Inches, Pt; from pptx.dml.color import RGBColor
    prs = Presentation(); prs.slide_width = Inches(13.333); prs.slide_height = Inches(7.5)
    sl = prs.slides.add_slide(prs.slide_layouts[6])
    tx = sl.shapes.add_textbox(Inches(1), Inches(2), Inches(11), Inches(3))
    p = tx.text_frame.paragraphs[0]; p.text = "Brand Reputation & Social Sentiment"; p.font.size = Pt(40); p.font.bold = True; p.font.color.rgb = RGBColor(0x0E, 0xA5, 0xE9)
    p2 = tx.text_frame.add_paragraph(); p2.text = f"Period: {d['month']} | {d['total_mentions']} mentions analyzed"; p2.font.size = Pt(18)
    sl2 = prs.slides.add_slide(prs.slide_layouts[6])
    rows = len(d["brands"]) + 1
    tbl = sl2.shapes.add_table(rows, 4, Inches(1), Inches(1), Inches(11), Inches(0.4*rows)).table
    for i, h in enumerate(["Brand", "Score", "Positive %", "Negative %"]): tbl.cell(0, i).text = h
    for i, b in enumerate(d["brands"]): tbl.cell(i+1,0).text=b["name"]; tbl.cell(i+1,1).text=str(b["score"]); tbl.cell(i+1,2).text=f"{b['pos']}%"; tbl.cell(i+1,3).text=f"{b['neg']}%"
    buf = io.BytesIO(); prs.save(buf); buf.seek(0)
    return StreamingResponse(buf, media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation", headers={"Content-Disposition": "attachment; filename=brand_report.pptx"})

def _xlsx(d):
    from openpyxl import Workbook; from openpyxl.styles import Font, PatternFill
    wb = Workbook(); hf = Font(bold=True, color="FFFFFF"); hfill = PatternFill(start_color="0EA5E9", end_color="0EA5E9", fill_type="solid")
    ws = wb.active; ws.title = "Brand Scores"
    for i, h in enumerate(["Brand", "Score", "Positive %", "Negative %", "Mentions"], 1): ws.cell(1, i, h).font = hf; ws.cell(1, i).fill = hfill
    for i, b in enumerate(d["brands"], 2): ws.cell(i,1,b["name"]); ws.cell(i,2,b["score"]); ws.cell(i,3,b["pos"]); ws.cell(i,4,b["neg"]); ws.cell(i,5,b["mentions"])
    ws2 = wb.create_sheet("Crises")
    for i, h in enumerate(["Event", "Brand", "Severity", "Date"], 1): ws2.cell(1, i, h).font = hf; ws2.cell(1, i).fill = hfill
    for i, c in enumerate(d["crises"], 2): ws2.cell(i,1,c["title"]); ws2.cell(i,2,c["brand"]); ws2.cell(i,3,c["severity"]); ws2.cell(i,4,c["date"])
    buf = io.BytesIO(); wb.save(buf); buf.seek(0)
    return StreamingResponse(buf, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", headers={"Content-Disposition": "attachment; filename=brand_report.xlsx"})
