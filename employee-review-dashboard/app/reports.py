"""Report generation — PDF, PowerPoint, Excel exports."""
import io
import json
from datetime import datetime
from typing import Optional

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.enums import TA_CENTER, TA_LEFT

from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN

from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side


def generate_pdf_report(data: dict) -> io.BytesIO:
    """Generate a professional PDF report from dashboard data."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.75*inch, bottomMargin=0.75*inch)
    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle("CustomTitle", parent=styles["Title"], fontSize=24,
                                  textColor=colors.HexColor("#1e293b"), spaceAfter=20)
    subtitle_style = ParagraphStyle("Subtitle", parent=styles["Normal"], fontSize=14,
                                     textColor=colors.HexColor("#64748b"), spaceAfter=30)
    heading_style = ParagraphStyle("CustomHeading", parent=styles["Heading1"], fontSize=16,
                                    textColor=colors.HexColor("#0f172a"), spaceBefore=20, spaceAfter=10)
    body_style = ParagraphStyle("CustomBody", parent=styles["Normal"], fontSize=11,
                                 textColor=colors.HexColor("#334155"), spaceAfter=8)

    story = []

    # Title page
    story.append(Spacer(1, 2*inch))
    story.append(Paragraph("Employee Sentiment Intelligence Report", title_style))
    story.append(Paragraph(f"Generated: {datetime.utcnow().strftime('%B %d, %Y')}", subtitle_style))
    if data.get("company_names"):
        story.append(Paragraph(f"Companies: {', '.join(data['company_names'])}", body_style))
    story.append(PageBreak())

    # Executive Summary
    overview = data.get("overview", {})
    story.append(Paragraph("Executive Summary", heading_style))
    story.append(Paragraph(
        f"This report analyzes <b>{overview.get('total_reviews', 0):,}</b> employee reviews across "
        f"<b>{overview.get('total_companies', 0)}</b> companies. "
        f"The overall sentiment score is <b>{overview.get('avg_sentiment', 0):.2f}</b> "
        f"with an average rating of <b>{overview.get('avg_rating', 0):.1f}/5.0</b>.",
        body_style
    ))
    story.append(Spacer(1, 10))

    # KPI table
    kpi_data = [
        ["Metric", "Value"],
        ["Total Reviews", f"{overview.get('total_reviews', 0):,}"],
        ["Average Sentiment", f"{overview.get('avg_sentiment', 0):.3f}"],
        ["Average Rating", f"{overview.get('avg_rating', 0):.1f} / 5.0"],
        ["Positive Reviews", f"{overview.get('positive_pct', 0):.1f}%"],
        ["Neutral Reviews", f"{overview.get('neutral_pct', 0):.1f}%"],
        ["Negative Reviews", f"{overview.get('negative_pct', 0):.1f}%"],
    ]
    kpi_table = Table(kpi_data, colWidths=[3*inch, 2.5*inch])
    kpi_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e293b")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 11),
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 1), (-1, -1), 10),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(kpi_table)
    story.append(Spacer(1, 20))

    # Topic Analysis
    topics = data.get("topics", [])
    if topics:
        story.append(Paragraph("Topic Analysis", heading_style))
        topic_data = [["Topic", "Mentions", "Avg Sentiment", "Positive %", "Negative %"]]
        for t in topics:
            sentiment_label = "🟢" if t["avg_sentiment"] > 0.05 else ("🔴" if t["avg_sentiment"] < -0.05 else "🟡")
            topic_data.append([
                t["topic"].replace("_", " ").title(),
                str(t["count"]),
                f"{t['avg_sentiment']:.3f} {sentiment_label}",
                f"{t.get('positive_pct', 0):.1f}%",
                f"{t.get('negative_pct', 0):.1f}%",
            ])
        topic_table = Table(topic_data, colWidths=[1.8*inch, 1*inch, 1.5*inch, 1.1*inch, 1.1*inch])
        topic_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e293b")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ]))
        story.append(topic_table)
        story.append(Spacer(1, 20))

    # Company Comparison
    companies = data.get("companies", [])
    if companies:
        story.append(Paragraph("Company Comparison", heading_style))
        comp_data = [["Company", "Avg Sentiment", "Avg Rating", "Reviews"]]
        for c in companies:
            comp_data.append([
                c["company_name"],
                f"{c['avg_sentiment']:.3f}",
                f"{c['avg_rating']:.1f}",
                str(c["review_count"]),
            ])
        comp_table = Table(comp_data, colWidths=[2.5*inch, 1.5*inch, 1.2*inch, 1.2*inch])
        comp_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e293b")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 10),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ]))
        story.append(comp_table)

    # Recommendations
    story.append(Spacer(1, 30))
    story.append(Paragraph("Recommendations", heading_style))

    recs = _generate_recommendations(data)
    for i, rec in enumerate(recs, 1):
        story.append(Paragraph(f"<b>{i}. {rec['title']}</b>", body_style))
        story.append(Paragraph(rec["detail"], body_style))
        story.append(Spacer(1, 5))

    # Footer
    story.append(Spacer(1, 40))
    footer_style = ParagraphStyle("Footer", parent=styles["Normal"], fontSize=8,
                                   textColor=colors.HexColor("#94a3b8"), alignment=TA_CENTER)
    story.append(Paragraph("Generated by Employee Sentiment Intelligence Dashboard • Confidential", footer_style))

    doc.build(story)
    buffer.seek(0)
    return buffer


def generate_pptx_report(data: dict) -> io.BytesIO:
    """Generate a PowerPoint report."""
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)

    # Color theme
    dark = RGBColor(0x1e, 0x29, 0x3b)
    accent = RGBColor(0x38, 0xbd, 0xf8)
    gray = RGBColor(0x64, 0x74, 0x8b)

    # --- Title Slide ---
    slide = prs.slides.add_slide(prs.slide_layouts[6])  # Blank
    _add_text_box(slide, "Employee Sentiment\nIntelligence Report",
                  Inches(1), Inches(2), Inches(11), Inches(2), Pt(40), dark, bold=True)
    _add_text_box(slide, f"Generated: {datetime.utcnow().strftime('%B %d, %Y')}",
                  Inches(1), Inches(4.2), Inches(6), Inches(0.6), Pt(18), gray)

    # --- Overview Slide ---
    overview = data.get("overview", {})
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    _add_text_box(slide, "Executive Summary", Inches(0.5), Inches(0.3), Inches(12), Inches(0.8), Pt(28), dark, bold=True)

    kpis = [
        ("Total Reviews", f"{overview.get('total_reviews', 0):,}"),
        ("Avg Sentiment", f"{overview.get('avg_sentiment', 0):.2f}"),
        ("Avg Rating", f"{overview.get('avg_rating', 0):.1f}/5"),
        ("Positive", f"{overview.get('positive_pct', 0):.0f}%"),
        ("Negative", f"{overview.get('negative_pct', 0):.0f}%"),
    ]
    for i, (label, value) in enumerate(kpis):
        x = Inches(0.5 + i * 2.5)
        _add_text_box(slide, value, x, Inches(1.5), Inches(2.2), Inches(1), Pt(32), accent, bold=True)
        _add_text_box(slide, label, x, Inches(2.5), Inches(2.2), Inches(0.5), Pt(14), gray)

    # --- Recommendations Slide ---
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    _add_text_box(slide, "Key Recommendations", Inches(0.5), Inches(0.3), Inches(12), Inches(0.8), Pt(28), dark, bold=True)
    recs = _generate_recommendations(data)
    rec_text = "\n\n".join([f"→ {r['title']}: {r['detail']}" for r in recs[:5]])
    _add_text_box(slide, rec_text, Inches(0.8), Inches(1.5), Inches(11), Inches(5), Pt(16), dark)

    buffer = io.BytesIO()
    prs.save(buffer)
    buffer.seek(0)
    return buffer


def generate_xlsx_report(data: dict) -> io.BytesIO:
    """Generate an Excel report with multiple sheets."""
    wb = Workbook()
    header_font = Font(bold=True, color="FFFFFF", size=11)
    header_fill = PatternFill(start_color="1E293B", end_color="1E293B", fill_type="solid")

    # --- Overview Sheet ---
    ws = wb.active
    ws.title = "Overview"
    overview = data.get("overview", {})
    overview_rows = [
        ["Metric", "Value"],
        ["Total Companies", overview.get("total_companies", 0)],
        ["Total Reviews", overview.get("total_reviews", 0)],
        ["Average Sentiment", round(overview.get("avg_sentiment", 0), 4)],
        ["Average Rating", round(overview.get("avg_rating", 0), 2)],
        ["Positive %", overview.get("positive_pct", 0)],
        ["Negative %", overview.get("negative_pct", 0)],
        ["Neutral %", overview.get("neutral_pct", 0)],
    ]
    for row in overview_rows:
        ws.append(row)
    _style_header(ws, header_font, header_fill)
    ws.column_dimensions["A"].width = 25
    ws.column_dimensions["B"].width = 20

    # --- Topics Sheet ---
    ws2 = wb.create_sheet("Topics")
    ws2.append(["Topic", "Mentions", "Avg Sentiment", "Positive %", "Negative %"])
    for t in data.get("topics", []):
        ws2.append([t["topic"].replace("_", " ").title(), t["count"],
                    round(t["avg_sentiment"], 4), t.get("positive_pct", 0), t.get("negative_pct", 0)])
    _style_header(ws2, header_font, header_fill)

    # --- Companies Sheet ---
    ws3 = wb.create_sheet("Companies")
    ws3.append(["Company", "Avg Sentiment", "Avg Rating", "Review Count"])
    for c in data.get("companies", []):
        ws3.append([c["company_name"], round(c["avg_sentiment"], 4),
                    round(c["avg_rating"], 2), c["review_count"]])
    _style_header(ws3, header_font, header_fill)

    # --- Trends Sheet ---
    ws4 = wb.create_sheet("Trends")
    ws4.append(["Period", "Avg Sentiment", "Review Count", "Avg Rating"])
    for t in data.get("trends", []):
        ws4.append([t["period"], round(t["avg_sentiment"], 4),
                    t["review_count"], round(t.get("avg_rating") or 0, 2)])
    _style_header(ws4, header_font, header_fill)

    buffer = io.BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    return buffer


def _add_text_box(slide, text, left, top, width, height, font_size, color, bold=False):
    from pptx.util import Inches, Pt
    txBox = slide.shapes.add_textbox(left, top, width, height)
    tf = txBox.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = text
    p.font.size = font_size
    p.font.color.rgb = color
    p.font.bold = bold


def _style_header(ws, font, fill):
    for cell in ws[1]:
        cell.font = font
        cell.fill = fill


def _generate_recommendations(data: dict) -> list[dict]:
    """Generate actionable recommendations based on the data."""
    recs = []
    overview = data.get("overview", {})
    topics = data.get("topics", [])

    # Sentiment-based
    avg_s = overview.get("avg_sentiment", 0)
    if avg_s < -0.1:
        recs.append({"title": "Critical Sentiment Alert", "detail": "Overall sentiment is significantly negative. Recommend immediate leadership listening sessions and anonymous pulse surveys to identify root causes."})
    elif avg_s < 0:
        recs.append({"title": "Sentiment Needs Attention", "detail": "Sentiment is slightly negative. Focus on the most-mentioned negative topics and create targeted action plans."})
    else:
        recs.append({"title": "Maintain Positive Momentum", "detail": "Overall sentiment is positive. Continue current initiatives and identify opportunities to further strengthen employee experience."})

    # Topic-based
    for t in topics:
        if t["avg_sentiment"] < -0.1 and t["count"] > 5:
            topic_name = t["topic"].replace("_", " ").title()
            recs.append({"title": f"Address {topic_name} Concerns", "detail": f"{topic_name} has negative sentiment ({t['avg_sentiment']:.2f}) across {t['count']} mentions. Investigate specific pain points and develop improvement initiatives."})

    # Negative percentage
    neg_pct = overview.get("negative_pct", 0)
    if neg_pct > 30:
        recs.append({"title": "High Negative Review Volume", "detail": f"{neg_pct:.0f}% of reviews are negative. This indicates systemic issues that need executive attention and structured improvement programs."})

    # Always add benchmarking rec
    recs.append({"title": "Competitive Benchmarking", "detail": "Regular benchmarking against industry peers helps contextualize sentiment scores. Consider quarterly comparison reports."})

    return recs[:6]
