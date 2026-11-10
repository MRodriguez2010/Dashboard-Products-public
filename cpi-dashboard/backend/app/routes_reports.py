"""Report generation for CPI Dashboard."""
import io
import statistics
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models import Category, Competitor, Product, PricePoint
from app.schemas import ReportRequest

router = APIRouter(tags=["reports"])


async def _gather_report_data(db):
    """Gather all data needed for reports."""
    cats = (await db.execute(select(Category))).scalars().all()
    comps = (await db.execute(select(Competitor))).scalars().all()
    products = (await db.execute(select(Product))).scalars().all()
    prices = (await db.execute(select(PricePoint).order_by(PricePoint.recorded_at.desc()))).scalars().all()
    
    all_prices = [p.price for p in prices if p.price > 0]
    
    comp_map = {}
    for c in comps:
        c_prices = [p.price for p in prices if p.competitor_id == c.id and p.price > 0]
        if c_prices:
            comp_map[c.name] = {
                "avg": round(statistics.mean(c_prices), 2),
                "min": round(min(c_prices), 2),
                "max": round(max(c_prices), 2),
                "tier": c.tier,
                "share": c.market_share_pct,
            }
    
    return {
        "categories": len(cats),
        "competitors": len(comps),
        "products": len(products),
        "price_points": len(prices),
        "avg_price": round(statistics.mean(all_prices), 2) if all_prices else 0,
        "median_price": round(statistics.median(all_prices), 2) if all_prices else 0,
        "comp_map": comp_map,
    }


def _generate_pdf(data):
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib import colors
    from reportlab.lib.units import inch

    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=letter, topMargin=0.75*inch, bottomMargin=0.75*inch)
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("CustomTitle", parent=styles["Title"], fontSize=22, textColor=colors.HexColor("#1e40af"))
    elements = []

    elements.append(Paragraph("Competitive Pricing Intelligence Report", title_style))
    elements.append(Spacer(1, 20))
    elements.append(Paragraph(f"Market Coverage: {data['categories']} categories, {data['competitors']} competitors, {data['products']} products", styles["Normal"]))
    elements.append(Paragraph(f"Average Market Price: ${data['avg_price']} | Median: ${data['median_price']}", styles["Normal"]))
    elements.append(Spacer(1, 20))

    elements.append(Paragraph("Competitor Price Comparison", styles["Heading2"]))
    table_data = [["Competitor", "Tier", "Avg Price", "Min", "Max", "Market Share"]]
    for name, info in sorted(data["comp_map"].items(), key=lambda x: x[1]["avg"], reverse=True):
        table_data.append([name, info["tier"], f"${info['avg']}", f"${info['min']}", f"${info['max']}", f"{info['share']}%"])
    
    if len(table_data) > 1:
        t = Table(table_data, colWidths=[120, 70, 70, 60, 60, 70])
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e40af")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), 9),
            ("FONTSIZE", (0, 1), (-1, -1), 8),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
            ("ALIGN", (2, 0), (-1, -1), "RIGHT"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ]))
        elements.append(t)

    elements.append(Spacer(1, 20))
    elements.append(Paragraph("Recommendations", styles["Heading2"]))
    recs = [
        "Monitor competitor pricing weekly for early trend detection.",
        "Consider tiered pricing to capture budget and premium segments.",
        "Track market events (acquisitions, funding) for pricing disruption signals.",
        "Set automated alerts for ±5% price changes from key competitors.",
    ]
    for r in recs:
        elements.append(Paragraph(f"• {r}", styles["Normal"]))
        elements.append(Spacer(1, 4))

    doc.build(elements)
    buf.seek(0)
    return buf


def _generate_pptx(data):
    from pptx import Presentation
    from pptx.util import Inches, Pt
    from pptx.dml.color import RGBColor

    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)

    # Title slide
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    txBox = slide.shapes.add_textbox(Inches(1), Inches(2), Inches(11), Inches(3))
    tf = txBox.text_frame
    p = tf.paragraphs[0]
    p.text = "Competitive Pricing Intelligence"
    p.font.size = Pt(40)
    p.font.bold = True
    p.font.color.rgb = RGBColor(0x1e, 0x40, 0xaf)
    p2 = tf.add_paragraph()
    p2.text = f"{data['competitors']} competitors | {data['products']} products | {data['categories']} categories"
    p2.font.size = Pt(18)
    p2.font.color.rgb = RGBColor(0x64, 0x74, 0x8b)

    # Overview slide
    slide2 = prs.slides.add_slide(prs.slide_layouts[6])
    txBox2 = slide2.shapes.add_textbox(Inches(1), Inches(0.5), Inches(11), Inches(1))
    tf2 = txBox2.text_frame
    tf2.paragraphs[0].text = "Market Overview"
    tf2.paragraphs[0].font.size = Pt(28)
    tf2.paragraphs[0].font.bold = True

    metrics = [
        f"Average Market Price: ${data['avg_price']}",
        f"Median Market Price: ${data['median_price']}",
        f"Total Price Data Points: {data['price_points']}",
    ]
    txBox3 = slide2.shapes.add_textbox(Inches(1), Inches(2), Inches(11), Inches(4))
    tf3 = txBox3.text_frame
    for m in metrics:
        p = tf3.add_paragraph()
        p.text = m
        p.font.size = Pt(20)
        p.space_after = Pt(12)

    # Competitor slide
    slide3 = prs.slides.add_slide(prs.slide_layouts[6])
    txBox4 = slide3.shapes.add_textbox(Inches(1), Inches(0.5), Inches(11), Inches(1))
    tf4 = txBox4.text_frame
    tf4.paragraphs[0].text = "Competitor Pricing"
    tf4.paragraphs[0].font.size = Pt(28)
    tf4.paragraphs[0].font.bold = True

    y = 2.0
    for name, info in sorted(data["comp_map"].items(), key=lambda x: x[1]["avg"], reverse=True)[:10]:
        txb = slide3.shapes.add_textbox(Inches(1), Inches(y), Inches(11), Inches(0.5))
        txb.text_frame.paragraphs[0].text = f"{name} ({info['tier']}) — Avg: ${info['avg']} | Range: ${info['min']}-${info['max']} | Share: {info['share']}%"
        txb.text_frame.paragraphs[0].font.size = Pt(14)
        y += 0.45

    buf = io.BytesIO()
    prs.save(buf)
    buf.seek(0)
    return buf


def _generate_xlsx(data):
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

    wb = Workbook()
    ws = wb.active
    ws.title = "Competitor Pricing"

    header_font = Font(bold=True, color="FFFFFF", size=11)
    header_fill = PatternFill(start_color="1E40AF", end_color="1E40AF", fill_type="solid")
    thin_border = Border(
        left=Side(style="thin", color="E2E8F0"),
        right=Side(style="thin", color="E2E8F0"),
        top=Side(style="thin", color="E2E8F0"),
        bottom=Side(style="thin", color="E2E8F0"),
    )

    headers = ["Competitor", "Tier", "Avg Price", "Min Price", "Max Price", "Market Share %"]
    for col, h in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col, value=h)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = Alignment(horizontal="center")
        cell.border = thin_border

    row = 2
    for name, info in sorted(data["comp_map"].items(), key=lambda x: x[1]["avg"], reverse=True):
        ws.cell(row=row, column=1, value=name).border = thin_border
        ws.cell(row=row, column=2, value=info["tier"]).border = thin_border
        ws.cell(row=row, column=3, value=info["avg"]).border = thin_border
        ws.cell(row=row, column=4, value=info["min"]).border = thin_border
        ws.cell(row=row, column=5, value=info["max"]).border = thin_border
        ws.cell(row=row, column=6, value=info["share"]).border = thin_border
        row += 1

    for col in range(1, 7):
        ws.column_dimensions[chr(64 + col)].width = 18

    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return buf


@router.post("/reports/generate")
async def generate_report(req: ReportRequest, db: AsyncSession = Depends(get_db)):
    data = await _gather_report_data(db)
    
    if req.format == "pdf":
        buf = _generate_pdf(data)
        return StreamingResponse(buf, media_type="application/pdf",
            headers={"Content-Disposition": "attachment; filename=cpi-report.pdf"})
    elif req.format == "pptx":
        buf = _generate_pptx(data)
        return StreamingResponse(buf, media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
            headers={"Content-Disposition": "attachment; filename=cpi-report.pptx"})
    elif req.format == "xlsx":
        buf = _generate_xlsx(data)
        return StreamingResponse(buf, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": "attachment; filename=cpi-report.xlsx"})
    else:
        return {"error": "Unsupported format. Use pdf, pptx, or xlsx."}
