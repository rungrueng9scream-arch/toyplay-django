"""Generate a Thai project report PDF for the ToyPlay website.

Usage:
    python docs/make_report_pdf.py

Requires reportlab (install once):
    pip install reportlab

Uses system Thai fonts (Tahoma) so Thai text renders correctly.

Outputs:
    docs/ToyPlay-Report.pdf
    <repo-root>/report_toyplay.pdf   (overwritten with the fresh report)
"""

import os
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
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
    Table,
    TableStyle,
)

# --- Thai fonts (Windows) ---
FONT_CANDIDATES = [
    (r"C:\Windows\Fonts\tahoma.ttf", r"C:\Windows\Fonts\tahomabd.ttf"),
    (r"C:\Windows\Fonts\leelawad.ttf", r"C:\Windows\Fonts\leelawadb.ttf"),
    (r"C:\Windows\Fonts\LeelawUI.ttf", r"C:\Windows\Fonts\LeelawUI.ttf"),
]

DOC_TITLE = "ToyPlay - รายงานโครงงานเว็บไซต์ร้านของเล่น"


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


BRAND = colors.HexColor("#ff5a5f")
DARK = colors.HexColor("#222222")
ACCENT = colors.HexColor("#ffb703")
LIGHT = colors.HexColor("#f7f7f9")

THAI_MONTHS = [
    "มกราคม", "กุมภาพันธ์", "มีนาคม", "เมษายน", "พฤษภาคม", "มิถุนายน",
    "กรกฎาคม", "สิงหาคม", "กันยายน", "ตุลาคม", "พฤศจิกายน", "ธันวาคม",
]


def thai_date(dt):
    return f"{dt.day} {THAI_MONTHS[dt.month - 1]} {dt.year + 543}"


def styles():
    ss = getSampleStyleSheet()
    S = {}
    S["cover_title"] = ParagraphStyle("cover_title", fontName="Thai-Bold",
                                      fontSize=24, leading=32, textColor=BRAND, alignment=TA_CENTER)
    S["cover_sub"] = ParagraphStyle("cover_sub", fontName="Thai", fontSize=13,
                                    leading=20, textColor=DARK)
    S["title"] = ParagraphStyle("title", parent=ss["Title"], fontName="Thai-Bold",
                                fontSize=20, leading=28, textColor=BRAND, alignment=TA_LEFT)
    S["subtitle"] = ParagraphStyle("subtitle", fontName="Thai", fontSize=12,
                                   leading=19, textColor=DARK, alignment=TA_LEFT)
    S["h1"] = ParagraphStyle("h1", fontName="Thai-Bold", fontSize=15, leading=22,
                             textColor=BRAND, spaceBefore=10, spaceAfter=6)
    S["h2"] = ParagraphStyle("h2", fontName="Thai-Bold", fontSize=12, leading=18,
                             textColor=DARK, spaceBefore=8, spaceAfter=4)
    S["body"] = ParagraphStyle("body", fontName="Thai", fontSize=10.5, leading=16,
                               textColor=DARK, alignment=TA_LEFT, spaceAfter=4)
    S["bullet"] = ParagraphStyle("bullet", fontName="Thai", fontSize=10.5, leading=16,
                                 textColor=DARK)
    S["small"] = ParagraphStyle("small", fontName="Thai", fontSize=9, leading=13,
                                textColor=colors.HexColor("#666666"))
    S["cell"] = ParagraphStyle("cell", fontName="Thai", fontSize=9.5, leading=13.5,
                               textColor=DARK)
    S["cellb"] = ParagraphStyle("cellb", fontName="Thai-Bold", fontSize=9.5, leading=13.5,
                                textColor=colors.white)
    S["flow"] = ParagraphStyle("flow", fontName="Thai-Bold", fontSize=9, leading=13,
                               textColor=DARK, alignment=TA_CENTER)
    S["ph"] = ParagraphStyle("ph", fontName="Thai", fontSize=9.5, leading=14,
                             textColor=colors.HexColor("#888888"), alignment=TA_CENTER)
    S["abstract"] = ParagraphStyle("abstract", fontName="Thai", fontSize=10.5, leading=17,
                                   textColor=DARK, alignment=TA_LEFT)
    return S


def bullets(items, S):
    return ListFlowable(
        [ListItem(Paragraph(t, S["bullet"]), leftIndent=12) for t in items],
        bulletType="bullet", bulletFontName="Thai", bulletFontSize=9,
        leftIndent=14, spaceBefore=2, spaceAfter=4,
    )


def numbered(items, S):
    return ListFlowable(
        [ListItem(Paragraph(t, S["bullet"]), leftIndent=12) for t in items],
        bulletType="1", bulletFormat="%s.", bulletFontName="Thai-Bold", bulletFontSize=10,
        leftIndent=16, spaceBefore=2, spaceAfter=4,
    )


def simple_table(rows, col_widths, S, header=True, small=False):
    data = []
    for r_i, row in enumerate(rows):
        cells = []
        for c in row:
            if header and r_i == 0:
                style = S["cellb"]
            else:
                style = S["cell"]
            cells.append(Paragraph(str(c), style))
        data.append(cells)
    t = Table(data, colWidths=col_widths, repeatRows=1 if header else 0)
    style = [
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 7),
        ("RIGHTPADDING", (0, 0), (-1, -1), 7),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#dddddd")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT]),
    ]
    if header:
        style += [("BACKGROUND", (0, 0), (-1, 0), BRAND)]
    t.setStyle(TableStyle(style))
    return t


def footer(canvas, doc):
    canvas.saveState()
    canvas.setStrokeGray(0.82)
    canvas.line(1.8 * cm, 1.5 * cm, A4[0] - 1.8 * cm, 1.5 * cm)
    canvas.setFont("Thai", 8)
    canvas.setFillGray(0.45)
    canvas.drawString(1.8 * cm, 1.15 * cm, DOC_TITLE)
    canvas.drawRightString(A4[0] - 1.8 * cm, 1.15 * cm, f"หน้า {doc.page}")
    canvas.restoreState()


def flow_row(steps, S):
    row = []
    widths = []
    for s in steps:
        if s == ">":
            row.append(Paragraph("&gt;", S["flow"]))
            widths.append(0.7 * cm)
        else:
            row.append(Paragraph(s, S["flow"]))
            widths.append(3.05 * cm)
    t = Table([row], colWidths=widths)
    boxes = [(0, 0), (2, 0), (4, 0), (6, 0), (8, 0)]
    style = [("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
             ("ALIGN", (0, 0), (-1, -1), "CENTER"),
             ("TOPPADDING", (0, 0), (-1, -1), 8),
             ("BOTTOMPADDING", (0, 0), (-1, -1), 8)]
    for c in boxes:
        style += [("BOX", c, c, 0.6, BRAND), ("BACKGROUND", c, c, LIGHT)]
    t.setStyle(TableStyle(style))
    return t


def placeholder_box(text, S, content_w, height=3.2 * cm):
    t = Table([[Paragraph(text, S["ph"])]], colWidths=[content_w], rowHeights=[height])
    t.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 0.8, colors.HexColor("#cccccc")),
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#fbfbfb")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    return t


def build_story(S, content_w):
    story = []

    # ================= Cover =================
    story.append(Spacer(1, 1.0 * cm))
    story.append(Paragraph("รายงานโครงงาน", S["cover_sub"]))
    story.append(Spacer(1, 0.2 * cm))
    story.append(Paragraph("ToyPlay", S["cover_title"]))
    story.append(Paragraph("เว็บแอปพลิเคชันร้านของเล่นออนไลน์", S["cover_sub"]))
    story.append(Paragraph("(E-Commerce Web Application)", S["cover_sub"]))
    story.append(Spacer(1, 0.3 * cm))
    story.append(Paragraph("พัฒนาด้วย Django Framework และ Django REST Framework", S["cover_sub"]))
    story.append(Spacer(1, 0.8 * cm))

    hero = Table([[Paragraph(
        "โครงงานนี้พัฒนาระบบร้านค้าออนไลน์ครบวงจรสำหรับร้านของเล่น ตั้งแต่การสมัครสมาชิก "
        "เลือกซื้อสินค้าตามหมวดหมู่ ตะกร้า ชำระเงิน ใช้คูปองส่วนลด ให้คะแนนรีวิว บันทึก "
        "รายการโปรด ติดตามสถานะคำสั่งซื้อ ไปจนถึงระบบจัดการหลังบ้านสำหรับพนักงานและผู้ดูแล "
        "พร้อม REST API สำหรับต่อยอด และ Deploy ขึ้นออนไลน์บน Render ได้จริง",
        ParagraphStyle("hero", fontName="Thai", fontSize=11.5, leading=19, textColor=DARK),
    )]], colWidths=[content_w])
    hero.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), LIGHT),
        ("BOX", (0, 0), (-1, -1), 0.8, BRAND),
        ("LEFTPADDING", (0, 0), (-1, -1), 14),
        ("RIGHTPADDING", (0, 0), (-1, -1), 14),
        ("TOPPADDING", (0, 0), (-1, -1), 14),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 14),
    ]))
    story.append(hero)
    story.append(Spacer(1, 0.8 * cm))

    info_rows = [
        ["รายการ", "รายละเอียด"],
        ["ชื่อโครงงาน", "ToyPlay - เว็บแอปพลิเคชันร้านของเล่น (Django Web Application)"],
        ["ประเภทโครงงาน", "เว็บแอปพลิเคชัน / E-Commerce"],
        ["เฟรมเวิร์ก", "Django 6.0.6 + Django REST Framework"],
        ["ฐานข้อมูล", "SQLite (พัฒนา) / PostgreSQL (Production บน Render)"],
        ["ผู้จัดทำ", "นาย/นางสาว ____________________"],
        ["อาจารย์ที่ปรึกษา", "____________________"],
        ["สถาบัน", "มหาวิทยาลัยราชภัฏกำแพงเพชร (KPRU)"],
        ["วันที่จัดทำ", thai_date(datetime.now())],
    ]
    story.append(simple_table(info_rows, [4.6 * cm, content_w - 4.6 * cm], S))
    story.append(PageBreak())

    # ================= Abstract =================
    story.append(Paragraph("บทคัดย่อ", S["title"]))
    story.append(Spacer(1, 0.3 * cm))
    story.append(Paragraph(
        "โครงงานนี้มีวัตถุประสงค์เพื่อพัฒนาระบบร้านของเล่นบนเว็บแอปพลิเคชันด้วยเฟรมเวิร์ก "
        "Django โดยระบบถูกออกแบบให้เป็นร้านค้าออนไลน์ที่ใช้งานได้ครบวงจร ประกอบด้วยฟีเจอร์ "
        "การสมัครสมาชิกและเข้าสู่ระบบ การแสดงสินค้าตามหมวดหมู่ การค้นหา กรอง และเรียงลำดับ "
        "สินค้า การแบ่งหน้า (Pagination) ตะกร้าสินค้า การชำระเงินพร้อมคูปองส่วนลดและการตัด "
        "สต็อกอัตโนมัติ การให้คะแนนและรีวิวสินค้า รายการโปรด (Wishlist) และการติดตามสถานะ "
        "คำสั่งซื้อแบบ timeline", S["abstract"]))
    story.append(Paragraph(
        "ระบบรองรับผู้ใช้ 3 บทบาท ได้แก่ สมาชิก (member) พนักงาน (staff) และผู้ดูแลระบบ "
        "(admin) โดยมีการกำหนดสิทธิ์การเข้าถึงตามบทบาทจริงผ่าน decorators และ Django Admin "
        "นอกจากนี้ยังมีระบบหลังบ้าน (Dashboard) สำหรับดูสถิติยอดขาย จัดการสินค้า หมวดหมู่ "
        "สมาชิก และคำสั่งซื้อ พร้อมให้บริการ REST API ผ่าน Django REST Framework โดยใช้ "
        "Token Authentication สำหรับการเชื่อมต่อจากแอปพลิเคชันอื่น", S["abstract"]))
    story.append(Paragraph(
        "ระบบได้รับการทดสอบอัตโนมัติด้วย Django TestCase ทั้งหมด 21 รายการ ครอบคลุมการสมัคร "
        "และเข้าสู่ระบบ การควบคุมสิทธิ์ การเพิ่ม/แก้ไข/ลบสินค้า การค้นหาและแบ่งหน้า หมวดหมู่ "
        "รีวิว รายการโปรด คูปอง การตัดสต็อก และการสร้างผู้ดูแลระบบจาก Environment Variables "
        "ผลการทดสอบผ่านทั้งหมด และระบบพร้อมนำขึ้นออนไลน์บนแพลตฟอร์ม Render ผ่าน HTTPS",
        S["abstract"]))
    story.append(Spacer(1, 0.3 * cm))
    story.append(Paragraph(
        "<b>คำสำคัญ:</b> Django, Django REST Framework, ร้านค้าออนไลน์, E-Commerce, "
        "ระบบหลังบ้าน, REST API", S["small"]))
    story.append(PageBreak())

    # ================= 1. บทนำ =================
    story.append(Paragraph("1. บทนำ", S["h1"]))
    story.append(Paragraph("1.1 ชื่อโครงงาน", S["h2"]))
    story.append(Paragraph(
        "ToyPlay - ระบบเว็บแอปพลิเคชันร้านของเล่น พัฒนาด้วย Django Framework", S["body"]))

    story.append(Paragraph("1.2 วัตถุประสงค์", S["h2"]))
    story.append(bullets([
        "เพื่อพัฒนาระบบเว็บแอปพลิเคชันร้านค้าออนไลน์ด้วย Django Framework ตามเกณฑ์การประเมินโครงงาน",
        "เพื่อประยุกต์ใช้ Django Model, Template, View และ URL routing ในการพัฒนาระบบจริง",
        "เพื่อฝึกออกแบบและกำหนดสิทธิ์ผู้ใช้อย่างน้อย 2 บทบาท (สมาชิก / พนักงาน / ผู้ดูแลระบบ)",
        "เพื่อฝึกการนำระบบขึ้น Hosting และให้เข้าใช้งานได้ผ่านอินเทอร์เน็ต",
        "เพื่อฝึกการทดสอบระบบอัตโนมัติ (Automated Testing) และการจัดทำรายงานโครงงาน",
    ], S))

    story.append(Paragraph("1.3 ขอบเขตของระบบ", S["h2"]))
    story.append(bullets([
        "ระบบรองรับการสมัครสมาชิก เข้าสู่ระบบ และออกจากระบบ",
        "ระบบมีผู้ใช้ 3 บทบาท: สมาชิก (member), พนักงาน (staff) และผู้ดูแลระบบ (admin)",
        "สมาชิกสามารถดูสินค้าตามหมวดหมู่ ค้นหา กรอง/เรียง ใส่ตะกร้า ใช้คูปอง และสั่งซื้อได้",
        "สมาชิกสามารถรีวิวให้คะแนน บันทึกรายการโปรด และติดตามสถานะคำสั่งซื้อของตนเองได้",
        "พนักงาน/ผู้ดูแลสามารถเพิ่ม แก้ไข ลบสินค้า จัดการหมวดหมู่ และจัดการคำสั่งซื้อได้",
        "ผู้ดูแลระบบสามารถจัดการบัญชีสมาชิกและพนักงาน รวมถึงกำหนดสิทธิ์การใช้งานได้",
        "ระบบมี REST API (Token Authentication) สำหรับเข้าถึงข้อมูลสินค้า ตะกร้า และคำสั่งซื้อ",
        "ระบบ Deploy บน Render และเข้าใช้งานได้ผ่าน HTTPS",
    ], S))

    story.append(Paragraph("1.4 ประโยชน์ที่คาดว่าจะได้รับ", S["h2"]))
    story.append(bullets([
        "ผู้ใช้ทั่วไปสามารถเลือกซื้อของเล่นผ่านเว็บได้อย่างสะดวก",
        "พนักงานและผู้ดูแลร้านสามารถจัดการสต็อกสินค้าและคำสั่งซื้อได้อย่างเป็นระบบ",
        "ร้านค้าได้ข้อมูลสถิติยอดขาย สินค้าขายดี และสินค้าใกล้หมด เพื่อช่วยในการตัดสินใจ",
        "ผู้พัฒนาได้ฝึกทักษะ Full Stack ทั้งส่วนหน้าบ้าน (Frontend) หลังบ้าน (Backend) ฐานข้อมูล และการ Deploy",
    ], S))
    story.append(PageBreak())

    # ================= 2. วิเคราะห์และออกแบบ =================
    story.append(Paragraph("2. การวิเคราะห์และออกแบบระบบ", S["h1"]))
    story.append(Paragraph("2.1 ภาพรวมและกรณีศึกษา", S["h2"]))
    story.append(Paragraph(
        "กรณีศึกษาคือร้านของเล่น ToyPlay ซึ่งมีสินค้าหลายหมวดหมู่ ลูกค้าสามารถดูรายละเอียด "
        "สินค้า ค้นหา เปรียบเทียบ และสั่งซื้อผ่านเว็บไซต์ได้ ฝ่ายร้านค้าสามารถจัดการข้อมูลสินค้า "
        "หมวดหมู่ สมาชิก และคำสั่งซื้อ ตลอดจนดูสถิติยอดขายผ่านหน้าหลังบ้าน", S["body"]))

    story.append(Paragraph("2.2 ผู้ใช้และบทบาท (User Roles)", S["h2"]))
    role_rows = [
        ["บทบาท", "รหัส", "สิทธิ์การใช้งานหลัก"],
        ["ลูกค้า / สมาชิก", "member", "ดูสินค้า, ค้นหา, ตะกร้า, ใช้คูปอง, checkout, รีวิว, รายการโปรด, ดูประวัติคำสั่งซื้อของตนเอง"],
        ["พนักงาน", "staff", "สิทธิ์สมาชิก + เข้าหน้าลังบ้าน, จัดการสินค้า/หมวดหมู่ และคำสั่งซื้อ (is_staff = True)"],
        ["ผู้ดูแลระบบ", "admin", "สิทธิ์สูงสุด รวมถึงจัดการบัญชีสมาชิก/พนักงานและกำหนดสิทธิ์ (is_superuser = True)"],
    ]
    story.append(simple_table(role_rows, [2.9 * cm, 1.9 * cm, content_w - 4.8 * cm], S))
    story.append(Spacer(1, 0.3 * cm))

    story.append(Paragraph("2.3 สถาปัตยกรรมโดยรวมของระบบ", S["h2"]))
    story.append(flow_row(
        ["เบราว์เซอร์", ">", "URL Router", ">", "View / Logic", ">", "Model / ฐานข้อมูล", ">", "Template (HTML)"],
        S))
    story.append(Spacer(1, 0.3 * cm))
    story.append(Paragraph(
        "ระบบใช้รูปแบบสถาปัตยกรรม MTV (Model-Template-View) ของ Django โดยเบราว์เซอร์ส่ง "
        "คำขอเข้าสู่ URL Router ซึ่งจะเรียก View ที่ทำหน้าที่ประมวลผล ติดต่อฐานข้อมูลผ่าน Model "
        "และแสดงผลกลับเป็นหน้า HTML ผ่าน Template ส่วน REST API จะตอบกลับเป็นข้อมูล JSON",
        S["body"]))
    story.append(PageBreak())

    # models
    story.append(Paragraph("2.4 โครงสร้างฐานข้อมูล (Data Models)", S["h2"]))
    model_rows = [
        ["โมเดล", "ความสัมพันธ์", "คำอธิบาย"],
        ["Category", "-", "หมวดหมู่สินค้า (ชื่อไม่ซ้ำ)"],
        ["Product", "FK -> Category", "สินค้า: ชื่อ, หมวดหมู่, รายละเอียด, ราคา, สต็อก, สถานะ, รูปภาพ"],
        ["Review", "FK -> Product / User", "รีวิวและคะแนน 1-5 ดาว (1 ผู้ใช้รีวิว 1 สินค้าได้ครั้งเดียว)"],
        ["Wishlist", "FK -> User / Product", "สินค้ารายการโปรดของผู้ใช้"],
        ["Coupon", "-", "คูปองส่วนลดแบบเปอร์เซ็นต์, ยอดขั้นต่ำ, จำกัดจำนวนครั้ง, วันหมดอายุ"],
        ["Cart", "OneToOne -> User", "ตะกร้าสินค้าของสมาชิก"],
        ["CartItem", "FK -> Cart / Product", "รายการสินค้าในตะกร้า และจำนวน"],
        ["Order", "FK -> User / Coupon", "คำสั่งซื้อ: สถานะ, ส่วนลด, ยอดรวม"],
        ["OrderItem", "FK -> Order / Product", "รายการสินค้าในคำสั่งซื้อ (เก็บชื่อ/ราคา ณ ตอนสั่งซื้อ)"],
        ["UserProfile", "OneToOne -> User", "โปรไฟล์สมาชิก: รูปโปรไฟล์, เบอร์โทร, ที่อยู่"],
        ["EmployeeProfile", "OneToOne -> User", "ข้อมูลพนักงาน: ตำแหน่ง, เบอร์โทร"],
    ]
    story.append(simple_table(model_rows, [3.4 * cm, 3.2 * cm, content_w - 6.6 * cm], S))
    story.append(Spacer(1, 0.3 * cm))
    story.append(Paragraph(
        "ระบบใช้ความสัมพันธ์ One-to-One (โปรไฟล์/ตะกร้ากับผู้ใช้) One-to-Many (ผู้ใช้กับคำสั่งซื้อ, "
        "คำสั่งซื้อกับรายการสินค้า) และ Many-to-One (สินค้ากับหมวดหมู่) โดยเมื่อผู้ใช้ใหม่ถูกสร้าง "
        "ระบบจะสร้าง UserProfile และ Cart ให้อัตโนมัติผ่าน signal (post_save)", S["body"]))

    story.append(Paragraph("2.5 สถานะของคำสั่งซื้อ (Order Status)", S["h2"]))
    status_rows = [
        ["สถานะ", "ความหมาย"],
        ["pending", "รอดำเนินการ (ค่าเริ่มต้นหลังสั่งซื้อ)"],
        ["confirmed", "ยืนยันคำสั่งซื้อแล้ว"],
        ["shipping", "กำลังจัดส่ง"],
        ["completed", "สำเร็จ (ได้รับสินค้าแล้ว)"],
        ["cancelled", "ยกเลิก"],
    ]
    story.append(simple_table(status_rows, [3.6 * cm, content_w - 3.6 * cm], S))
    story.append(Spacer(1, 0.2 * cm))
    story.append(Paragraph(
        "ลูกค้าสามารถติดตามสถานะแบบ timeline ได้ตามลำดับ: รอดำเนินการ &gt; ยืนยันคำสั่งซื้อ "
        "&gt; กำลังจัดส่ง &gt; สำเร็จ (หรือยกเลิก)", S["body"]))
    story.append(PageBreak())

    # ================= 3. การพัฒนาระบบ =================
    story.append(Paragraph("3. การพัฒนาระบบ", S["h1"]))
    story.append(Paragraph("3.1 เทคโนโลยีที่ใช้", S["h2"]))
    tech_rows = [
        ["ส่วนของระบบ", "เทคโนโลยี / เครื่องมือ"],
        ["ภาษาและเฟรมเวิร์ก", "Python 3, Django 6.0.6"],
        ["REST API", "Django REST Framework + Token Authentication"],
        ["ฐานข้อมูล", "SQLite (พัฒนา) / PostgreSQL (Production) ผ่าน dj-database-url"],
        ["ส่วนติดต่อผู้ใช้", "HTML, Bootstrap 5.3.3, CSS (static/css/style.css)"],
        ["จัดการ Static/Media", "WhiteNoise + Django staticfiles, Pillow (อัปโหลดรูปภาพ)"],
        ["เว็บเซิร์ฟเวอร์", "Gunicorn (WSGI)"],
        ["การ Deploy", "Render (เชื่อมกับ GitHub อัตโนมัติ) + render.yaml"],
        ["การทดสอบ", "Django TestCase (21 เทสต์ ผ่านทั้งหมด)"],
    ]
    story.append(simple_table(tech_rows, [4.4 * cm, content_w - 4.4 * cm], S))
    story.append(Spacer(1, 0.3 * cm))

    story.append(Paragraph("3.2 โครงสร้างโปรเจกต์", S["h2"]))
    proj_rows = [
        ["โฟลเดอร์ / ไฟล์", "หน้าที่"],
        ["myproject/", "ตั้งค่าโปรเจกต์: settings.py, urls.py, wsgi.py, asgi.py"],
        ["myapp/models.py", "โมเดลฐานข้อมูลทั้งหมด (Product, Order, Coupon ฯลฯ)"],
        ["myapp/views.py", "ตรรกะการทำงานฝั่งเว็บ (Storefront + Dashboard + Cart + Checkout)"],
        ["myapp/forms.py", "ฟอร์มและ validation (Register, Product, StaffUser, Profile, Category, Review)"],
        ["myapp/api_views.py", "REST API views (products, auth, cart, orders)"],
        ["myapp/serializers.py", "ตัวแปลงข้อมูล Model เป็น JSON สำหรับ API"],
        ["myapp/urls.py + api_urls.py", "เส้นทาง URL ของเว็บและ API"],
        ["myapp/templates/", "เทมเพลต HTML (home, product, cart, dashboard, profile ฯลฯ)"],
        ["myapp/migrations/", "ประวัติการเปลี่ยนแปลงฐานข้อมูล + seed ข้อมูลเริ่มต้น"],
        ["myapp/tests.py", "ชุดทดสอบอัตโนมัติ 21 รายการ"],
        ["media/", "ไฟล์รูปภาพที่ผู้ใช้อัปโหลด (สินค้า, avatar)"],
    ]
    story.append(simple_table(proj_rows, [5.2 * cm, content_w - 5.2 * cm], S))
    story.append(PageBreak())

    story.append(Paragraph("3.3 ระบบยืนยันตัวตนและสิทธิ์", S["h2"]))
    story.append(Paragraph(
        "ระบบใช้ Django Authentication สำหรับการสมัครสมาชิก (RegisterForm), เข้าสู่ระบบ และ "
        "ออกจากระบบ โดยใช้ decorator @login_required และ @user_passes_test เพื่อจำกัดการเข้าถึง "
        "หน้าหลังบ้านเฉพาะ staff/admin ซึ่งตรวจสอบผ่านฟังก์ชัน is_staff_user และ is_admin_user",
        S["body"]))

    story.append(Paragraph("3.4 การจัดการข้อมูล (CRUD) และฟอร์ม", S["h2"]))
    story.append(bullets([
        "สินค้า: เพิ่ม/แก้ไข/ลบ ผ่าน ProductForm (ModelForm) ในหน้า Dashboard",
        "หมวดหมู่: เพิ่มหมวดหมู่ใหม่ผ่าน CategoryForm",
        "สมาชิก/พนักงาน: เพิ่ม/แก้ไข/ลบ และกำหนดสิทธิ์ผ่าน StaffUserForm (เฉพาะ admin)",
        "โปรไฟล์: แก้ไขรูปโปรไฟล์ เบอร์โทร ที่อยู่ และอีเมลผ่าน ProfileForm",
        "ทุกฟอร์มมี validation เช่น ราคา/สต็อกต้องไม่ติดลบ, รหัสผ่านยาวอย่างน้อย 6 ตัวอักษร, ชื่อผู้ใช้ซ้ำไม่ได้",
    ], S))

    story.append(Paragraph("3.5 การค้นหา กรอง เรียง และแบ่งหน้า", S["h2"]))
    story.append(bullets([
        "ค้นหาสินค้าจากชื่อและรายละเอียดด้วย Q objects (พารามิเตอร์ q)",
        "กรองตามหมวดหมู่ (category) และเรียงตามราคา/ความใหม่ (sort)",
        "ค้นหาสมาชิก/สินค้าใน Dashboard ด้วยพารามิเตอร์ pq / uq",
        "ใช้ Django Paginator แบ่งหน้า (ITEMS_PER_PAGE = 6 สำหรับหน้าเว็บ, API PAGE_SIZE = 10)",
    ], S))

    story.append(Paragraph("3.6 ตะกร้า การชำระเงิน และคูปอง", S["h2"]))
    story.append(bullets([
        "เพิ่มสินค้าลงตะกร้า ปรับจำนวน และลบรายการ โดยตรวจสอบสต็อกไม่ให้สั่งเกินจำนวนที่มี",
        "ยืนยันการสั่งซื้อด้วย transaction.atomic เพื่อป้องกันข้อมูลไม่สมบูรณ์",
        "รองรับคูปองส่วนลดแบบเปอร์เซ็นต์ พร้อมเงื่อนไขยอดขั้นต่ำ วันหมดอายุ และจำนวนครั้งที่ใช้ได้",
        "ตัดสต็อกสินค้าอัตโนมัติเมื่อสั่งซื้อสำเร็จ และบันทึกยอดรวม/ส่วนลดลงในคำสั่งซื้อ",
        "เก็บชื่อและราคาสินค้า ณ ตอนสั่งซื้อไว้ใน OrderItem เพื่อรักษาประวัติแม้ราคาสินค้าเปลี่ยนภายหลัง",
    ], S))

    story.append(Paragraph("3.7 รีวิวและรายการโปรด", S["h2"]))
    story.append(Paragraph(
        "สมาชิกที่เข้าสู่ระบบสามารถให้คะแนนรีวิวสินค้า 1-5 ดาว พร้อมความคิดเห็น โดย 1 ผู้ใช้ "
        "สามารถรีวิวสินค้าเดิมได้เพียงครั้งเดียวและแก้ไขได้ (update_or_create) ส่วนรายการโปรด "
        "รองรับการกดหัวใจ เพิ่ม/ลบสินค้าที่ชื่นชอบ และแสดงในหน้าของผู้ใช้", S["body"]))
    story.append(PageBreak())

    # REST API
    story.append(Paragraph("3.8 REST API (ส่วนเสริม)", S["h2"]))
    story.append(Paragraph(
        "ระบบให้บริการ REST API ผ่าน Django REST Framework โดยใช้ Token Authentication "
        "สำหรับไคลเอนต์ภายนอก และรองรับ Session Authentication สำหรับผู้ใช้ที่ล็อกอินในเว็บ "
        "การแก้ไขข้อมูลสินค้าจำกัดเฉพาะ staff/admin", S["body"]))
    api_rows = [
        ["Endpoint", "Method", "คำอธิบาย", "สิทธิ์"],
        ["/api/products/", "GET, POST", "ดู/เพิ่มรายการสินค้า", "อ่าน: ทุกคน, เขียน: staff"],
        ["/api/products/&lt;id&gt;/", "GET, PUT, PATCH, DELETE", "ดู/แก้ไข/ลบสินค้า", "เขียน: staff"],
        ["/api/auth/register/", "POST", "สมัครสมาชิกผ่าน API (คืนค่า token)", "ทุกคน"],
        ["/api/auth/login/", "POST", "ขอ token สำหรับเข้าสู่ระบบ", "ทุกคน"],
        ["/api/auth/me/", "GET", "ข้อมูลผู้ใช้ปัจจุบัน", "ล็อกอิน"],
        ["/api/cart/", "GET, POST", "ดู/เพิ่มสินค้าในตะกร้า", "ล็อกอิน"],
        ["/api/cart/items/&lt;id&gt;/", "DELETE", "ลบรายการในตะกร้า", "ล็อกอิน"],
        ["/api/orders/", "GET, POST", "ดูคำสั่งซื้อ / สร้างคำสั่งซื้อจากตะกร้า", "ล็อกอิน"],
        ["/api/orders/&lt;id&gt;/", "GET", "ดูรายละเอียดคำสั่งซื้อ", "ล็อกอิน (เจ้าของ)"],
    ]
    story.append(simple_table(api_rows, [4.0 * cm, 3.4 * cm, 5.6 * cm, content_w - 13.0 * cm], S))
    story.append(Spacer(1, 0.3 * cm))

    story.append(Paragraph("3.9 Dashboard และสถิติหลังบ้าน", S["h2"]))
    story.append(bullets([
        "ยอดขายรวม (ไม่รวมคำสั่งซื้อที่ยกเลิก), จำนวนคำสั่งซื้อทั้งหมด และคำสั่งซื้อรอดำเนินการ",
        "จำนวนสมาชิกทั้งหมด จำนวนสินค้าทั้งหมด และจำนวนสินค้าใกล้หมด (สต็อก <= 5)",
        "สินค้าขายดี 5 อันดับ (Top Products) จากยอดขายสะสม และรายการคำสั่งซื้อล่าสุด",
        "หน้าจัดการคำสั่งซื้อ: ค้นหา/กรองตามสถานะ และอัปเดตสถานะคำสั่งซื้อ",
    ], S))

    story.append(Paragraph("3.10 Django Admin", S["h2"]))
    story.append(Paragraph(
        "เปิดใช้งาน Django Admin ที่ /admin/ สำหรับจัดการข้อมูลทุกตาราง (สินค้า หมวดหมู่ รีวิว "
        "รายการโปรด คูปอง คำสั่งซื้อ และผู้ใช้) พร้อมค้นหาและตัวกรอง โดยผู้ดูแลระบบจะถูกสร้าง "
        "หรืออัปเดตอัตโนมัติจาก Environment Variables (DJANGO_SUPERUSER_USERNAME / "
        "DJANGO_SUPERUSER_PASSWORD) ทุกครั้งที่รัน migrate", S["body"]))
    story.append(PageBreak())

    # ================= 4. ผลการพัฒนา =================
    story.append(Paragraph("4. ผลการพัฒนาและภาพรวมหน้าจอ", S["h1"]))
    story.append(Paragraph(
        "ระบบสามารถรันได้ทั้งในเครื่อง (Local) และบน Render โดยเข้าใช้งานได้ผ่าน HTTPS "
        "ต่อไปนี้เป็นภาพรวมของหน้าจอสำคัญในระบบ (สามารถแทรกภาพหน้าจอจริงได้ในกรอบด้านล่าง)",
        S["body"]))
    screen_rows = [
        ["หน้าจอ", "รายละเอียด"],
        ["หน้าแรก (Home)", "hero banner, หมวดหมู่สินค้า, สินค้าแนะนำพร้อมคะแนนรีวิว"],
        ["หน้าสินค้า (Products)", "ค้นหา กรองตามหมวดหมู่ เรียงลำดับ และแบ่งหน้า"],
        ["รายละเอียดสินค้า", "รูปภาพ ราคา สต็อก เรตติ้ง รีวิว สินค้าที่เกี่ยวข้อง และปุ่มรายการโปรด"],
        ["ตะกร้า / ชำระเงิน", "ปรับจำนวน ใช้คูปอง และยืนยันคำสั่งซื้อ"],
        ["โปรไฟล์สมาชิก", "อัปโหลดรูปโปรไฟล์ แก้ไขที่อยู่ และดูประวัติคำสั่งซื้อ + ติดตามสถานะ"],
        ["Dashboard หลังบ้าน", "สถิติยอดขาย สินค้าขายดี สินค้าใกล้หมด และจัดการสินค้า/สมาชิก"],
        ["จัดการคำสั่งซื้อ", "ค้นหา กรองตามสถานะ และอัปเดตสถานะคำสั่งซื้อ"],
        ["REST API", "ทดสอบ request/response และสถานะ HTTP ผ่าน Postman"],
    ]
    story.append(simple_table(screen_rows, [4.4 * cm, content_w - 4.4 * cm], S))
    story.append(Spacer(1, 0.4 * cm))
    story.append(Paragraph("ตัวอย่างภาพหน้าจอ (แทรกภาพจริง)", S["h2"]))
    story.append(placeholder_box("[ภาพหน้าจอ 1: หน้าหลัก ToyPlay]", S, content_w))
    story.append(Spacer(1, 0.25 * cm))
    story.append(placeholder_box("[ภาพหน้าจอ 2: หน้าสินค้าและ Dashboard จัดการสินค้า]", S, content_w))
    story.append(Spacer(1, 0.25 * cm))
    story.append(placeholder_box("[ภาพหน้าจอ 3: REST API /api/products/]", S, content_w))
    story.append(PageBreak())

    # ================= 5. การทดสอบและสรุปผล =================
    story.append(Paragraph("5. การทดสอบและสรุปผล", S["h1"]))
    story.append(Paragraph("5.1 ชุดการทดสอบอัตโนมัติ", S["h2"]))
    story.append(Paragraph(
        "ระบบใช้ Django TestCase ในการทดสอบอัตโนมัติทั้งหมด 21 รายการ โดยรันคำสั่ง "
        "python manage.py test และผลการทดสอบผ่านทั้งหมด", S["body"]))
    test_rows = [
        ["กลุ่มการทดสอบ", "จำนวน", "ขอบเขตที่ทดสอบ", "ผล"],
        ["AuthRoleTests", "2", "สมัคร/เข้าสู่ระบบ และควบคุมสิทธิ์เข้า Dashboard", "ผ่าน"],
        ["ProductCrudTests", "3", "เพิ่ม/แก้ไข/ลบสินค้า", "ผ่าน"],
        ["SearchPaginationTests", "3", "ค้นหา แบ่งหน้า และแสดงสถิติ", "ผ่าน"],
        ["CategoryFilterTests", "3", "กรอง/เรียงตามหมวดหมู่ และเพิ่มหมวดหมู่", "ผ่าน"],
        ["ReviewWishlistTests", "4", "รีวิว (เพิ่ม/แก้ไข) และรายการโปรด", "ผ่าน"],
        ["CheckoutCouponStockTests", "3", "ตัดสต็อก ใช้คูปอง และกันสั่งเกินสต็อก", "ผ่าน"],
        ["SuperuserSyncTests", "3", "สร้าง/อัปเดตแอดมินจาก Environment Variables", "ผ่าน"],
        ["รวม", "21", "ครอบคลุมทุกฟีเจอร์หลักของระบบ", "ผ่านทั้งหมด"],
    ]
    story.append(simple_table(test_rows, [4.6 * cm, 1.5 * cm, content_w - 8.5 * cm, 2.4 * cm], S))
    story.append(Spacer(1, 0.3 * cm))

    story.append(Paragraph("5.2 ผลการทดสอบเพิ่มเติม", S["h2"]))
    story.append(bullets([
        "python manage.py check: ไม่พบข้อผิดพลาด",
        "ทดสอบสิทธิ์: สมาชิกทั่วไปไม่สามารถเข้าถึง Dashboard ได้ (ถูก redirect)",
        "ทดสอบ API: สมาชิกทั่วไปที่พยายามเพิ่มสินค้าผ่าน API จะถูกปฏิเสธ (ไม่มีสิทธิ์)",
        "ทดสอบบน Render: เข้าใช้งานได้จริงผ่าน HTTPS",
    ], S))

    story.append(Paragraph("5.3 ข้อจำกัด", S["h2"]))
    story.append(bullets([
        "ข้อมูลบนแพลนฟรีของ Render อาจไม่คงอยู่เมื่อ redeploy หากไม่ใช้ฐานข้อมูลภายนอกถาวร",
        "ไฟล์ media (รูปภาพ) บนแพลนฟรีเป็นแบบชั่วคราว (ephemeral) ไม่ถาวร",
        "ยังไม่มีระบบชำระเงินออนไลน์จริง (Payment Gateway) และยังไม่รองรับหลายภาษา",
    ], S))

    story.append(Paragraph("5.4 แนวทางพัฒนาต่อ", S["h2"]))
    story.append(bullets([
        "เชื่อมต่อ PostgreSQL แบบถาวรและใช้ Cloud Storage สำหรับไฟล์ media",
        "เพิ่มระบบชำระเงินออนไลน์ (เช่น PromptPay / บัตรเครดิต)",
        "เพิ่มระบบแจ้งเตือนอีเมล และรายงานสถิติเชิงลึก",
        "เพิ่มเอกสาร API อัตโนมัติ (Swagger/OpenAPI) และระบบ CI/CD",
    ], S))

    story.append(Paragraph("5.5 สรุป", S["h2"]))
    story.append(Paragraph(
        "ระบบ ToyPlay ตอบโจทย์เกณฑ์ขั้นต่ำของโครงงานครบถ้วน ทั้งการจัดการข้อมูล CRUD การค้นหา "
        "การแบ่งหน้า การอัปโหลดรูปภาพ ระบบสมาชิกและสิทธิ์ผู้ใช้หลายบทบาท และการ Deploy บน "
        "Hosting อีกทั้งยังพัฒนาต่อยอดด้วยระบบหลังบ้านพร้อมสถิติ คูปองส่วนลด การติดตามสถานะ "
        "คำสั่งซื้อ REST API และชุดทดสอบอัตโนมัติ 21 รายการ เพื่อเพิ่มความน่าเชื่อถือและรองรับคะแนนพิเศษ",
        S["body"]))
    story.append(PageBreak())

    # ================= 6. ภาคผนวก =================
    story.append(Paragraph("6. ภาคผนวก", S["h1"]))
    story.append(Paragraph("A. URL ของระบบ", S["h2"]))
    story.append(bullets([
        "Production URL: https://toyplay-django.onrender.com/",
        "Health Check: https://toyplay-django.onrender.com/health/",
        "GitHub Repository: https://github.com/rungrueng9scream-arch/toyplay-django",
    ], S))

    story.append(Paragraph("B. บัญชีทดสอบ", S["h2"]))
    acc_rows = [
        ["บทบาท", "ชื่อผู้ใช้ (Username)", "รหัสผ่าน (Password)"],
        ["ผู้ดูแลระบบ (admin)", "boss", "1"],
        ["พนักงาน (staff)", "staff / admin (สร้างผ่าน Dashboard)", "กำหนดเอง"],
        ["สมาชิก (member)", "สมัครใหม่ได้ที่หน้า /register/", "อย่างน้อย 6 ตัวอักษร"],
    ]
    story.append(simple_table(acc_rows, [4.4 * cm, content_w - 8.4 * cm, 4.0 * cm], S))
    story.append(Spacer(1, 0.25 * cm))
    story.append(Paragraph(
        "คูปองทดลองใช้: WELCOME10 (ลด 10%) และ TOY20 (ลด 20% ขั้นต่ำ 1,000 บาท)", S["body"]))

    story.append(Paragraph("C. การรันในเครื่อง (Local)", S["h2"]))
    story.append(numbered([
        "python -m venv .venv  แล้ว activate",
        "pip install -r requirements.txt",
        "python manage.py migrate",
        "python manage.py runserver  แล้วเปิด http://127.0.0.1:8000",
        "python manage.py test  เพื่อรันชุดทดสอบอัตโนมัติ",
    ], S))

    story.append(Paragraph("D. Environment Variables (Production)", S["h2"]))
    env_rows = [
        ["ตัวแปร", "ค่า / คำอธิบาย"],
        ["SECRET_KEY", "คีย์ลับของ Django (สุ่มเป็นสตริงยาว)"],
        ["DEBUG", "False (ปิดโหมด debug บน Production)"],
        ["ALLOWED_HOSTS", "โดเมนของแอป เช่น your-app.onrender.com"],
        ["DATABASE_URL", "Internal Database URL ของ PostgreSQL จาก Render"],
        ["DATABASE_SSL_REQUIRE", "True เมื่อใช้ PostgreSQL บน Render"],
        ["DJANGO_SUPERUSER_USERNAME", "ชื่อผู้ใช้แอดมิน (สร้าง/อัปเดตอัตโนมัติ)"],
        ["DJANGO_SUPERUSER_PASSWORD", "รหัสผ่านแอดมิน"],
        ["DJANGO_SUPERUSER_EMAIL", "อีเมลแอดมิน (ไม่บังคับ)"],
    ]
    story.append(simple_table(env_rows, [6.0 * cm, content_w - 6.0 * cm], S))
    story.append(Spacer(1, 0.3 * cm))
    story.append(Paragraph(
        "Build Command: pip install -r requirements.txt &amp;&amp; python manage.py collectstatic "
        "--noinput &amp;&amp; python manage.py migrate", S["small"]))
    story.append(Paragraph(
        "Start Command: gunicorn myproject.wsgi:application", S["small"]))
    story.append(Spacer(1, 0.4 * cm))
    story.append(Paragraph(
        "จัดทำโดย นักศึกษา KPRU  -  " + thai_date(datetime.now()), S["small"]))

    return story


def build():
    register_fonts()
    S = styles()
    content_w = A4[0] - 3.6 * cm

    here = os.path.dirname(os.path.abspath(__file__))
    repo_root = os.path.dirname(here)
    targets = [
        os.path.join(here, "ToyPlay-Report.pdf"),
        os.path.join(repo_root, "report_toyplay.pdf"),
    ]

    for out_path in targets:
        # Rebuild the story for each target: reportlab consumes flowables on build.
        story = build_story(S, content_w)
        doc = SimpleDocTemplate(
            out_path, pagesize=A4,
            leftMargin=1.8 * cm, rightMargin=1.8 * cm,
            topMargin=1.8 * cm, bottomMargin=2.0 * cm,
            title="ToyPlay - รายงานโครงงานเว็บไซต์ร้านของเล่น", author="นักศึกษา KPRU",
        )
        doc.build(story, onFirstPage=footer, onLaterPages=footer)
    return targets


if __name__ == "__main__":
    paths = build()
    print("PDF report created:")
    for p in paths:
        print("  -", p)
