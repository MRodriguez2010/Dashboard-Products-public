"""Create an editable PowerPoint using the same analysis as the browser."""
from datetime import datetime, timezone
from io import BytesIO
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.opc.constants import RELATIONSHIP_TYPE as RT
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN
from pptx.util import Inches, Pt
from .model import finding

INK, MUTED, PAPER, BLUE, PEER, RULE = "19313C", "4B646D", "F8F9F5", "236953", "C48347", "D7DFD9"


def box(slide, x, y, w, h, color):
    shape = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(x), Inches(y), Inches(w), Inches(h))
    shape.fill.solid()
    shape.fill.fore_color.rgb = RGBColor.from_string(color)
    shape.line.fill.background()
    return shape


def label(slide, x, y, w, h, text, size=16, color=INK, bold=False, align=None):
    frame = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h)).text_frame
    frame.word_wrap = True
    frame.margin_left = frame.margin_right = frame.margin_top = frame.margin_bottom = 0
    p = frame.paragraphs[0]
    p.text = text
    if align is not None:
        p.alignment = align
    p.font.name = "Aptos"
    p.font.size = Pt(size)
    p.font.bold = bold
    p.font.color.rgb = RGBColor.from_string(color)


def new_page(deck, r, title, number):
    slide = deck.slides.add_slide(deck.slide_layouts[6])
    slide.background.fill.solid()
    slide.background.fill.fore_color.rgb = RGBColor.from_string(PAPER)
    label(slide, .62, .37, 8.7, .32, "REVELIO    /    EMPLOYEE SENTIMENT ANALYSIS", 13, BLUE, True)
    label(slide, 9.04, .37, 3.66, .32, "SYNTHETIC DEMONSTRATION", 11, MUTED, True, PP_ALIGN.RIGHT)
    label(slide, .62, .98, 12.0, .8, title, 37, INK, True)
    label(slide, .65, 1.86, 11.95, .46, f"{r['company']}   /   {r['start']} – {r['end']}   /   Peers: {', '.join(r['peers'])}", 16, MUTED)
    box(slide, .64, 6.80, 12.03, .018, RULE)
    label(slide, .64, 6.98, 11, .29, f"{r['tier']} report   ·   Fictional organizations and response counts", 11, MUTED)
    label(slide, 12.0, 6.96, .68, .3, str(number), 12, MUTED, align=PP_ALIGN.RIGHT)
    return slide


def make_deck(r):
    deck = Presentation()
    # The default PowerPoint template includes a stock thumbnail and printer profile.
    package = deck.part.package
    for rel in list(package.iter_rels()):
        if rel.reltype == RT.THUMBNAIL:
            package.drop_rel(rel.rId)
    for rel in list(deck.part.rels.values()):
        if rel.reltype == RT.PRINTER_SETTINGS:
            deck.part.drop_rel(rel.rId)
    deck.slide_width, deck.slide_height = Inches(13.333), Inches(7.5)
    deck.core_properties.title = "Employee Sentiment Analysis"
    deck.core_properties.author = "Revelio portfolio demo"
    deck.core_properties.subject = "Synthetic employee survey results"
    deck.core_properties.comments = ""
    deck.core_properties.last_modified_by = "Revelio portfolio demo"
    deck.core_properties.created = deck.core_properties.modified = datetime.now(timezone.utc)
    slide = new_page(deck, r, finding(r), 1)
    label(slide, .65, 2.58, 3.0, .3, "FAVORABLE RESPONSES", 12, MUTED, True)
    label(slide, 3.65, 2.58, 3.65, .3, f"■  {r['company']}", 13, BLUE, True)
    label(slide, 7.35, 2.58, 2.7, .3, "■  Pooled peers", 13, PEER, True)
    label(slide, 10.85, 2.58, 1.8, .3, "GAP (PP)", 12, MUTED, True, PP_ALIGN.RIGHT)
    for i, t in enumerate(r["topics"]):
        y = 3.12 + i * .80
        label(slide, .65, y+.04, 2.82, .55, t["topic"], 17, INK, True)
        for j, (key, color) in enumerate([("focus", BLUE), ("peers", PEER)]):
            pct = t[key]["pct"]
            top = y + j*.25
            box(slide, 3.65, top, 5.9 * pct/100, .14, color)
            label(slide, 3.78 + 5.9 * pct/100, top-.045, 1.05, .25, f"{pct:.1f}%", 12, MUTED)
        label(slide, 10.90, y+.01, 1.76, .4, f"{t['gap']:+.1f}", 22, INK, True, PP_ALIGN.RIGHT)
    label(slide, .65, 6.43, 12, .26, "Each bar uses favorable answers divided by valid answers. Peer counts are pooled before division.", 12, MUTED)
    if r["tier"] == "Full":
        slide = new_page(deck, r, "How the overall result changed", 2)
        headers = ["Quarter", r["company"], "Pooled peers", "Focus answers"]
        xs = [.67, 3.64, 6.51, 9.45]
        for x, h in zip(xs, headers):
            label(slide, x, 2.75, 2.83, .4, h, 15, MUTED, True)
        for i, row in enumerate(r["trend"]):
            y = 3.45 + .86*i
            box(slide, .66, y-.15, 12, .018, RULE)
            vals = [row["quarter"], f"{row['focus']['pct']:.1f}%", f"{row['peers']['pct']:.1f}%", str(row["focus"]["responses"])]
            for x, value in zip(xs, vals):
                label(slide, x, y, 2.82, .5, value, 22, INK, True)
    slide = new_page(deck, r, "How to read this comparison", len(deck.slides)+1)
    notes = [
        ("Response base", f"{r['focus']['responses']:,} answers for {r['company']} and {r['pool']['responses']:,} for the peer group. A person may answer several questions."),
        ("Favorable share", "Divide favorable answers by valid answers. The peer percentage weights each company by its number of answers."),
        ("Percentage-point gap", "Subtract the pooled peer share from the focus share before rounding. The headline selects the largest absolute topic gap."),
        ("Interpretation", "The fixture is fictional. Differences describe the selected counts and cannot establish causes or statistical significance."),
    ]
    for i, (heading, detail) in enumerate(notes):
        y = 2.7 + .91*i
        label(slide, .66, y, 2.82, .45, heading, 17, BLUE, True)
        label(slide, 3.63, y, 8.8, .75, detail, 17)
    output = BytesIO()
    deck.save(output)
    return output.getvalue()
