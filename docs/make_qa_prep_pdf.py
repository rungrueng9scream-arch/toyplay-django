"""Render the ToyPlay Q&A preparation markdown to a Thai PDF.

Usage:
    python docs/make_qa_prep_pdf.py

Requires reportlab (install once):
    pip install reportlab

Reads:  docs/ToyPlay-QA-Prep.md
Writes: docs/ToyPlay-QA-Prep.pdf
Uses system Thai fonts (Tahoma) so Thai text renders correctly.
"""

import os
import re

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    ListFlowable,
    ListItem,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
)

FONT_CANDIDATES = [
    (r"C:\Windows\Fonts\tahoma.ttf", r"C:\Windows\Fonts\tahomabd.ttf"),
    (r"C:\Windows\Fonts\leelawad.ttf", r"C:\Windows\Fonts\leelawadb.ttf"),
    (r"C:\Windows\Fonts\LeelawUI.ttf", r"C:\Windows\Fonts\LeelawUI.ttf"),
]

BRAND = colors.HexColor("#ff5a5f")
DARK = colors.HexColor("#222222")
LIGHT = colors.HexColor("#f7f7f9")

DOC_TITLE = "ToyPlay - คู่มือเตรียมตอบคำถามอาจารย์"


def register_fonts():
    for regular, bold in FONT_CANDIDATES:
        if os.path.exists(regular) and os.path.exists(bold):
            pdfmetrics.registerFont(TTFont("Thai", regular))
            pdfmetrics.registerFont(TTFont("Thai-Bold", bold))
            pdfmetrics.registerFontFamily(
                "Thai", normal="Thai", bold="Thai-Bold",
                italic="Thai", boldItalic="Thai-Bold",
            )
            return
    raise RuntimeError("ไม่พบฟอนต์ไทยในระบบ (Tahoma/Leelawadee)")


def styles():
    return {
        "title": ParagraphStyle("title", fontName="Thai-Bold", fontSize=20, leading=28,
                                textColor=BRAND, spaceAfter=6),
        "h1": ParagraphStyle("h1", fontName="Thai-Bold", fontSize=15, leading=21,
                             textColor=BRAND, spaceBefore=12, spaceAfter=6),
        "h2": ParagraphStyle("h2", fontName="Thai-Bold", fontSize=12.5, leading=18,
                             textColor=DARK, spaceBefore=8, spaceAfter=4),
        "body": ParagraphStyle("body", fontName="Thai", fontSize=10.5, leading=16,
                               textColor=DARK, alignment=TA_LEFT, spaceAfter=4),
        "bullet": ParagraphStyle("bullet", fontName="Thai", fontSize=10.5, leading=16,
                                 textColor=DARK),
        "sub": ParagraphStyle("sub", fontName="Thai", fontSize=10.5, leading=16,
                              textColor=colors.HexColor("#333333"), leftIndent=14, spaceAfter=3),
    }


def inline(text):
    text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    return text


def build_story(lines, S, content_w):
    story = []
    bullet_buf = []

    def flush_bullets():
        if bullet_buf:
            story.append(ListFlowable(
                [ListItem(Paragraph(t, S["bullet"]), leftIndent=12) for t in bullet_buf],
                bulletType="bullet", bulletFontName="Thai", bulletFontSize=8,
                leftIndent=14, spaceBefore=1, spaceAfter=4,
            ))
            bullet_buf.clear()

    for raw in lines:
        line = raw.rstrip("\n")
        stripped = line.strip()

        if not stripped:
            flush_bullets()
            story.append(Spacer(1, 0.18 * cm))
            continue

        if stripped.startswith("## "):
            flush_bullets()
            story.append(Paragraph(inline(stripped[3:]), S["h2"]))
        elif stripped.startswith("# "):
            flush_bullets()
            story.append(Paragraph(inline(stripped[2:]), S["title"]))
        elif stripped.startswith("- "):
            bullet_buf.append(inline(stripped[2:]))
        else:
            flush_bullets()
            story.append(Paragraph(inline(stripped), S["body"]))

    flush_bullets()
    return story


def footer(canvas, doc):
    canvas.saveState()
    canvas.setStrokeGray(0.82)
    canvas.line(1.8 * cm, 1.5 * cm, A4[0] - 1.8 * cm, 1.5 * cm)
    canvas.setFont("Thai", 8)
    canvas.setFillGray(0.45)
    canvas.drawString(1.8 * cm, 1.15 * cm, DOC_TITLE)
    canvas.drawRightString(A4[0] - 1.8 * cm, 1.15 * cm, f"หน้า {doc.page}")
    canvas.restoreState()


def build():
    register_fonts()
    S = styles()
    here = os.path.dirname(os.path.abspath(__file__))
    md_path = os.path.join(here, "ToyPlay-QA-Prep.md")
    out_path = os.path.join(here, "ToyPlay-QA-Prep.pdf")

    with open(md_path, encoding="utf-8") as f:
        lines = f.readlines()

    content_w = A4[0] - 3.6 * cm
    story = build_story(lines, S, content_w)

    doc = SimpleDocTemplate(
        out_path, pagesize=A4,
        leftMargin=1.8 * cm, rightMargin=1.8 * cm,
        topMargin=1.8 * cm, bottomMargin=2.0 * cm,
        title="ToyPlay - คู่มือเตรียมตอบคำถาม", author="นักศึกษา KPRU",
    )
    doc.build(story, onFirstPage=footer, onLaterPages=footer)
    return out_path


if __name__ == "__main__":
    path = build()
    print("QA prep PDF created:", path)
