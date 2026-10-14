"""Generate a Thai presentation PDF describing the ToyPlay website.

Usage:
    python docs/make_presentation_pdf.py

Requires reportlab (install once):
    pip install reportlab

Uses system Thai fonts (Tahoma) so Thai text renders correctly.
Output: docs/ToyPlay-Web-Presentation.pdf
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
    (r"C:\Windows\Fonts\leelawad.ttf", r"C:\Windows\Fonts\leelawdb.ttf"),
    (r"C:\Windows\Fonts\LeelawUI.ttf", r"C:\Windows\Fonts\LeelawUI.ttf"),
]


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
    S["title"] = ParagraphStyle("title", parent=ss["Title"], fontName="Thai-Bold",
                                fontSize=30, leading=38, textColor=BRAND, alignment=TA_LEFT)
    S["subtitle"] = ParagraphStyle("subtitle", fontName="Thai", fontSize=14,
                                   leading=22, textColor=DARK, alignment=TA_LEFT)
    S["h1"] = ParagraphStyle("h1", fontName="Thai-Bold", fontSize=17, leading=24,
                             textColor=BRAND, spaceBefore=10, spaceAfter=8)
    S["h2"] = ParagraphStyle("h2", fontName="Thai-Bold", fontSize=12.5, leading=18,
                             textColor=DARK, spaceBefore=8, spaceAfter=4)
    S["body"] = ParagraphStyle("body", fontName="Thai", fontSize=10.5, leading=16,
                               textColor=DARK, alignment=TA_LEFT, spaceAfter=4)
    S["bullet"] = ParagraphStyle("bullet", fontName="Thai", fontSize=10.5, leading=16,
                                 textColor=DARK)
    S["small"] = ParagraphStyle("small", fontName="Thai", fontSize=9, leading=13,
                                textColor=colors.HexColor("#666666"))
    S["cell"] = ParagraphStyle("cell", fontName="Thai", fontSize=10, leading=14,
                               textColor=DARK)
    S["cellb"] = ParagraphStyle("cellb", fontName="Thai-Bold", fontSize=10, leading=14,
                                textColor=colors.white)
    S["flow"] = ParagraphStyle("flow", fontName="Thai-Bold", fontSize=9.5, leading=13,
                               textColor=DARK, alignment=TA_CENTER)
    return S


def bullets(items, S):
    return ListFlowable(
        [ListItem(Paragraph(t, S["bullet"]), leftIndent=12) for t in items],
        bulletType="bullet", bulletFontName="Thai", bulletFontSize=9,
        leftIndent=14, spaceBefore=2, spaceAfter=4,
    )


def simple_table(rows, col_widths, S, header=True):
    data = []
    for r_i, row in enumerate(rows):
        cells = []
        for c in row:
            style = S["cellb"] if (header and r_i == 0) else S["cell"]
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
    canvas.drawString(1.8 * cm, 1.15 * cm, "ToyPlay - เอกสารนำเสนอโครงงานเว็บไซต์ร้านของเล่น")
    canvas.drawRightString(A4[0] - 1.8 * cm, 1.15 * cm, f"หน้า {doc.page}")
    canvas.restoreState()


def flow_row(steps, S):
    row = []
    widths = []
    for i, s in enumerate(steps):
        if s == ">":
            row.append(Paragraph("&gt;", S["flow"]))
            widths.append(0.7 * cm)
        else:
            row.append(Paragraph(s, S["flow"]))
            widths.append(3.05 * cm)
    t = Table([row], colWidths=widths)
    t.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("BOX", (0, 0), (0, 0), 0.6, BRAND),
        ("BOX", (2, 0), (2, 0), 0.6, BRAND),
        ("BOX", (4, 0), (4, 0), 0.6, BRAND),
        ("BOX", (6, 0), (6, 0), 0.6, BRAND),
        ("BOX", (8, 0), (8, 0), 0.6, BRAND),
        ("BACKGROUND", (0, 0), (0, 0), LIGHT),
        ("BACKGROUND", (2, 0), (2, 0), LIGHT),
        ("BACKGROUND", (4, 0), (4, 0), LIGHT),
        ("BACKGROUND", (6, 0), (6, 0), LIGHT),
        ("BACKGROUND", (8, 0), (8, 0), LIGHT),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
    ]))
    return t


def build():
    register_fonts()
    S = styles()
    out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            "ToyPlay-Web-Presentation.pdf")
    doc = SimpleDocTemplate(
        out_path, pagesize=A4,
        leftMargin=1.8 * cm, rightMargin=1.8 * cm,
        topMargin=1.8 * cm, bottomMargin=2.0 * cm,
        title="ToyPlay - เอกสารนำเสนอเว็บไซต์", author="นักศึกษา KPRU",
    )
    story = []
    content_w = A4[0] - 3.6 * cm

    # ---------- Cover ----------
    story.append(Spacer(1, 1.2 * cm))
    story.append(Paragraph("ToyPlay", S["title"]))
    story.append(Paragraph("เว็บไซต์ร้านของเล่นออนไลน์ (Django Web Application)", S["subtitle"]))
    story.append(Spacer(1, 0.4 * cm))

    hero = Table([[Paragraph(
        "ระบบร้านค้าออนไลน์ครบวงจรสำหรับร้านของเล่น<br/>"
        "ตั้งแต่เลือกซื้อสินค้า ตะกร้า ชำระเงิน รีวิว ไปจนถึงระบบจัดการหลังบ้านสำหรับพนักงาน<br/>"
        "พัฒนาด้วย Django + Django REST Framework และพร้อม Deploy บน Render",
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
    story.append(Spacer(1, 0.7 * cm))

    info_rows = [
        ["รายการ", "รายละเอียด"],
        ["ชื่อโครงงาน", "ToyPlay - เว็บไซต์ร้านของเล่น"],
        ["เทคโนโลยีหลัก", "Django 6.0, Django REST Framework, Bootstrap 5, PostgreSQL/SQLite"],
        ["รูปแบบระบบ", "Web Application + REST API"],
        ["บัญชีผู้ดูแลระบบ (Demo)", "username: boss   |   password: 1"],
        ["คูปองทดลองใช้", "WELCOME10 (ลด 10%)   |   TOY20 (ลด 20% ขั้นต่ำ 1,000 บาท)"],
        ["จัดทำโดย", "นักศึกษา KPRU"],
        ["วันที่จัดทำ", thai_date(datetime.now())],
    ]
    story.append(simple_table(info_rows, [4.6 * cm, content_w - 4.6 * cm], S))
    story.append(Spacer(1, 0.5 * cm))
    story.append(Paragraph(
        "หมายเหตุ: บัญชีและคูปองข้างต้นเป็นข้อมูลสาธิตสำหรับการนำเสนอเท่านั้น", S["small"]))
    story.append(PageBreak())

    # ---------- 1. Overview ----------
    story.append(Paragraph("1. ภาพรวมโครงงาน (Overview)", S["h1"]))
    story.append(Paragraph(
        "ToyPlay เป็นเว็บแอปพลิเคชันร้านขายของเล่นออนไลน์ พัฒนาด้วยภาษา Python และเฟรมเวิร์ก "
        "Django ผู้ใช้สามารถสมัครสมาชิก เลือกดูสินค้าตามหมวดหมู่ ค้นหา ใส่ตะกร้า ใช้คูปองส่วนลด "
        "สั่งซื้อ และติดตามสถานะคำสั่งซื้อได้ ส่วนพนักงานและผู้ดูแลระบบสามารถจัดการสินค้า "
        "หมวดหมู่ สมาชิก และคำสั่งซื้อผ่านหน้าหลังบ้าน (Dashboard) พร้อมดูสถิติยอดขาย "
        "ระบบยังมี REST API สำหรับต่อยอดกับแอปพลิเคชันอื่นได้อีกด้วย", S["body"]))
    story.append(Spacer(1, 0.2 * cm))
    story.append(Paragraph("สถาปัตยกรรมโดยรวมของระบบ", S["h2"]))
    story.append(flow_row(
        ["เบราว์เซอร์", ">", "URL Router", ">", "View / Logic", ">", "Model / ฐานข้อมูล", ">", "Template (HTML)"],
        S))
    story.append(Spacer(1, 0.5 * cm))
    story.append(Paragraph("เทคโนโลยีที่ใช้", S["h2"]))
    tech_rows = [
        ["ส่วนของระบบ", "เทคโนโลยี / เครื่องมือ"],
        ["ภาษาและเฟรมเวิร์ก", "Python 3, Django 6.0.6"],
        ["REST API", "Django REST Framework + Token Authentication"],
        ["ฐานข้อมูล", "SQLite (พัฒนา) / PostgreSQL (Production) ผ่าน dj-database-url"],
        ["ส่วนติดต่อผู้ใช้", "HTML, Bootstrap 5.3.3, CSS (static/css/style.css), ฟอนต์ Nunito"],
        ["จัดการไฟล์ Static/Media", "WhiteNoise + Django staticfiles, Pillow"],
        ["เว็บเซิร์ฟเวอร์", "Gunicorn (WSGI)"],
        ["การ Deploy", "Render (เชื่อมกับ GitHub อัตโนมัติ)"],
        ["การทดสอบ", "Django TestCase (21 เทสต์ ผ่านทั้งหมด)"],
    ]
    story.append(simple_table(tech_rows, [5.0 * cm, content_w - 5.0 * cm], S))
    story.append(PageBreak())

    # ---------- 2. Customer features ----------
    story.append(Paragraph("2. ฟีเจอร์ฝั่งลูกค้า (Storefront)", S["h1"]))
    story.append(bullets([
        "<b>หน้าแรก (Home)</b> - โชว์หมวดหมู่สินค้าและสินค้าแนะนำ พร้อมคะแนนรีวิว",
        "<b>หน้าสินค้า (Products)</b> - ค้นหาชื่อ/รายละเอียด, กรองตามหมวดหมู่, เรียงตามราคาหรือความใหม่, แบ่งหน้า",
        "<b>หน้าสินค้าละเอียด (Product Detail)</b> - รูปภาพ, รายละเอียด, เรตติ้ง, สินค้าที่เกี่ยวข้อง",
        "<b>ตะกร้าสินค้า (Cart)</b> - เพิ่ม/ปรับจำนวน/ลบ พร้อมตรวจสอบสต็อกไม่ให้สั่งเกิน",
        "<b>ชำระเงิน (Checkout)</b> - ใช้คูปองส่วนลด, ตัดสต็อกอัตโนมัติ, ป้องกันข้อมูลพังด้วย transaction",
        "<b>รีวิวและให้ดาว</b> - ให้คะแนน 1-5 ดาว พร้อมความคิดเห็น (1 คนรีวิวได้ 1 ครั้ง แก้ไขได้)",
        "<b>รายการโปรด (Wishlist)</b> - กดหัวใจบันทึกสินค้าที่ชอบไว้ดูภายหลัง",
        "<b>โปรไฟล์สมาชิก</b> - อัปโหลดรูปโปรไฟล์, เบอร์โทร, ที่อยู่, ประวัติการสั่งซื้อ",
        "<b>ติดตามสถานะคำสั่งซื้อ</b> - แสดงขั้นตอนแบบ timeline: รอดำเนินการ > ยืนยัน > กำลังจัดส่ง > สำเร็จ",
        "<b>ระบบสมาชิก</b> - สมัครสมาชิก, เข้าสู่ระบบ, ออกจากระบบ",
    ], S))

    story.append(Paragraph("3. ฟีเจอร์ฝั่งหลังบ้าน (Staff / Admin)", S["h1"]))
    story.append(bullets([
        "<b>Dashboard สถิติ</b> - ยอดขายรวม, จำนวนคำสั่งซื้อ, รอดำเนินการ, จำนวนสินค้า/ผู้ใช้, สินค้าใกล้หมด",
        "<b>สินค้าขายดี (Top Products)</b> และรายการคำสั่งซื้อล่าสุด",
        "<b>จัดการสินค้า</b> - เพิ่ม/แก้ไข/ลบ พร้อมอัปโหลดรูปและกำหนดหมวดหมู่",
        "<b>จัดการหมวดหมู่</b> - เพิ่มหมวดหมู่สินค้าได้จากหน้า Dashboard",
        "<b>จัดการสมาชิกและพนักงาน</b> - เพิ่ม/แก้ไข/ลบ และกำหนดสิทธิ์การใช้งาน",
        "<b>จัดการคำสั่งซื้อ</b> - ค้นหา/กรองตามสถานะ และอัปเดตสถานะคำสั่งซื้อ",
        "<b>Django Admin</b> - หน้าจัดการผู้ดูแลระบบที่ /admin/ สำหรับจัดการข้อมูลทุกตาราง",
    ], S))
    story.append(PageBreak())

    # ---------- 4. Roles ----------
    story.append(Paragraph("4. บทบาทผู้ใช้งาน (User Roles)", S["h1"]))
    role_rows = [
        ["บทบาท", "สิทธิ์การใช้งาน"],
        ["ลูกค้า / สมาชิก (member)", "เลือกซื้อสินค้า, ตะกร้า, รีวิว, รายการโปรด, จัดการโปรไฟล์"],
        ["พนักงาน (staff)", "เข้าหน้าหลังบ้านได้ จัดการสินค้า/คำสั่งซื้อ (is_staff = True)"],
        ["ผู้ดูแลระบบ (admin)", "สิทธิ์สูงสุด จัดการทุกอย่างรวมถึงสมาชิกและสิทธิ์ (is_superuser = True)"],
    ]
    story.append(simple_table(role_rows, [6.0 * cm, content_w - 6.0 * cm], S))
    story.append(Spacer(1, 0.4 * cm))
    story.append(Paragraph(
        "บัญชีผู้ดูแลระบบจะถูกสร้าง/อัปเดตอัตโนมัติจาก Environment Variables "
        "(DJANGO_SUPERUSER_USERNAME / DJANGO_SUPERUSER_PASSWORD) ทุกครั้งที่รัน migrate", S["body"]))
    story.append(Spacer(1, 0.4 * cm))

    # ---------- 5. Coupons ----------
    story.append(Paragraph("5. คูปองส่วนลดทดลองใช้", S["h1"]))
    coupon_rows = [
        ["รหัสคูปอง", "ส่วนลด", "ยอดขั้นต่ำ", "หมายเหตุ"],
        ["WELCOME10", "10%", "ไม่มี", "ใช้ได้ทั่วไป"],
        ["TOY20", "20%", "1,000 บาท", "จำกัดจำนวนครั้ง"],
    ]
    story.append(simple_table(coupon_rows, [3.2 * cm, 2.4 * cm, 3.0 * cm, content_w - 8.6 * cm], S))
    story.append(Spacer(1, 0.6 * cm))

    # ---------- 6. Database models ----------
    story.append(Paragraph("6. โครงสร้างฐานข้อมูล (Data Models)", S["h1"]))
    model_rows = [
        ["โมเดล", "คำอธิบาย"],
        ["Category", "หมวดหมู่สินค้า"],
        ["Product", "สินค้า (ชื่อ, หมวดหมู่, รายละเอียด, ราคา, สต็อก, สถานะ, รูปภาพ)"],
        ["Review", "รีวิวและคะแนน 1-5 ดาว (1 ผู้ใช้ / 1 สินค้า)"],
        ["Wishlist", "สินค้ารายการโปรดของผู้ใช้"],
        ["Coupon", "คูปองส่วนลดแบบเปอร์เซ็นต์"],
        ["Cart / CartItem", "ตะกร้าสินค้าและรายการในตะกร้า"],
        ["Order / OrderItem", "คำสั่งซื้อและรายการสินค้าในคำสั่งซื้อ"],
        ["UserProfile", "โปรไฟล์สมาชิก (รูป, เบอร์โทร, ที่อยู่)"],
        ["EmployeeProfile", "ข้อมูลเพิ่มเติมของพนักงาน"],
    ]
    story.append(simple_table(model_rows, [4.6 * cm, content_w - 4.6 * cm], S))
    story.append(Spacer(1, 0.4 * cm))
    story.append(Paragraph(
        "สถานะคำสั่งซื้อ: รอดำเนินการ > ยืนยันคำสั่งซื้อ > กำลังจัดส่ง > สำเร็จ (หรือ ยกเลิก)", S["body"]))
    story.append(PageBreak())

    # ---------- 7. URLs ----------
    story.append(Paragraph("7. เส้นทางหลักของเว็บไซต์ (URL Routes)", S["h1"]))
    url_rows = [
        ["URL", "หน้าที่ / การทำงาน"],
        ["/", "หน้าแรก แสดงหมวดหมู่และสินค้าแนะนำ"],
        ["/product/", "รายการสินค้า ค้นหา/กรอง/เรียง/แบ่งหน้า"],
        ["/product/&lt;id&gt;/", "รายละเอียดสินค้า + สินค้าที่เกี่ยวข้อง"],
        ["/wishlist/", "รายการโปรดของผู้ใช้"],
        ["/cart/  และ  /checkout/", "ตะกร้าสินค้า และการสั่งซื้อ"],
        ["/profile/", "โปรไฟล์สมาชิก + ประวัติคำสั่งซื้อ"],
        ["/login/  /register/  /logout/", "เข้าสู่ระบบ / สมัครสมาชิก / ออกจากระบบ"],
        ["/dashboard/", "หน้าหลังบ้าน (สถิติ + จัดการสินค้า/สมาชิก)"],
        ["/dashboard/orders/", "จัดการคำสั่งซื้อ (staff/admin)"],
        ["/admin/", "Django Admin (ผู้ดูแลระบบ)"],
        ["/api/", "REST API (ดูหัวข้อถัดไป)"],
    ]
    story.append(simple_table(url_rows, [6.2 * cm, content_w - 6.2 * cm], S))
    story.append(Spacer(1, 0.6 * cm))

    # ---------- 8. REST API ----------
    story.append(Paragraph("8. REST API (ส่วนเสริม)", S["h1"]))
    story.append(Paragraph(
        "ใช้ Token Authentication สำหรับยืนยันตัวตน และรองรับ Session สำหรับผู้ใช้ที่ล็อกอินในเว็บ", S["body"]))
    api_rows = [
        ["Endpoint", "Method", "คำอธิบาย"],
        ["/api/products/", "GET, POST, PUT, DELETE", "จัดการสินค้า (แก้ไขได้เฉพาะ staff)"],
        ["/api/auth/register/", "POST", "สมัครสมาชิกผ่าน API (คืนค่า token)"],
        ["/api/auth/login/", "POST", "ขอ token สำหรับเข้าสู่ระบบ"],
        ["/api/auth/me/", "GET", "ข้อมูลผู้ใช้ปัจจุบัน"],
        ["/api/cart/", "GET, POST", "ดู/เพิ่มสินค้าในตะกร้า"],
        ["/api/cart/items/&lt;id&gt;/", "DELETE", "ลบรายการในตะกร้า"],
        ["/api/orders/", "GET, POST", "ดูรายการคำสั่งซื้อ / สร้างคำสั่งซื้อจากตะกร้า"],
    ]
    story.append(simple_table(api_rows, [5.6 * cm, 4.4 * cm, content_w - 10.0 * cm], S))
    story.append(PageBreak())

    # ---------- 9. Deploy ----------
    story.append(Paragraph("9. การนำขึ้นออนไลน์ (Deploy บน Render)", S["h1"]))
    story.append(bullets([
        "เชื่อมต่อ Repository GitHub กับ Render และตั้งค่าเป็น Web Service (Python)",
        "Build Command: <b>pip install -r requirements.txt &amp;&amp; python manage.py collectstatic --noinput &amp;&amp; python manage.py migrate</b>",
        "Start Command: <b>gunicorn myproject.wsgi:application</b>",
        "ทุกครั้งที่ push ขึ้น branch main ระบบจะ Deploy อัตโนมัติ (หรือกด Manual Deploy)",
    ], S))
    story.append(Paragraph("Environment Variables ที่ต้องตั้งบน Render", S["h2"]))
    env_rows = [
        ["ตัวแปร", "ค่า / คำอธิบาย"],
        ["SECRET_KEY", "คีย์ลับของ Django (สุ่มเป็นสตริงยาว)"],
        ["DEBUG", "False (ปิดโหมด debug บน Production)"],
        ["ALLOWED_HOSTS", "โดเมนของแอป เช่น your-app.onrender.com"],
        ["DATABASE_URL", "Internal Database URL ของ PostgreSQL จาก Render"],
        ["DJANGO_SUPERUSER_USERNAME", "ชื่อผู้ใช้แอดมิน (เช่น boss) - ใช้สร้าง/อัปเดตอัตโนมัติ"],
        ["DJANGO_SUPERUSER_PASSWORD", "รหัสผ่านแอดมิน (เช่น 1)"],
    ]
    story.append(simple_table(env_rows, [6.2 * cm, content_w - 6.2 * cm], S))

    story.append(Paragraph("การรันในเครื่อง (Local)", S["h2"]))
    story.append(bullets([
        "python -m venv .venv  แล้ว activate",
        "pip install -r requirements.txt",
        "python manage.py migrate",
        "python manage.py runserver  แล้วเปิด http://127.0.0.1:8000",
    ], S))
    story.append(Paragraph("การทดสอบ", S["h2"]))
    story.append(Paragraph(
        "รันคำสั่ง <b>python manage.py test</b> เพื่อทดสอบระบบ - มีทั้งหมด 21 เทสต์ ครอบคลุม "
        "การสมัคร/ล็อกอิน, สิทธิ์การเข้าถึง, CRUD สินค้า, ค้นหา/แบ่งหน้า, หมวดหมู่, รีวิว, "
        "รายการโปรด, คูปอง, การตัดสต็อก และการสร้างแอดมินจาก environment", S["body"]))
    story.append(Spacer(1, 0.4 * cm))

    # ---------- 10. Summary ----------
    story.append(Paragraph("10. จุดเด่นและสรุป", S["h1"]))
    story.append(bullets([
        "ระบบร้านค้าออนไลน์ครบวงจร ใช้งานได้จริงทั้งฝั่งลูกค้าและผู้ดูแล",
        "มีระบบหลังบ้านพร้อมสถิติช่วยตัดสินใจ และจัดการข้อมูลครบทุกส่วน",
        "มี REST API สำหรับต่อยอดเป็นแอปมือถือหรือบริการอื่น",
        "ตรวจสต็อกและตัดสต็อกอัตโนมัติ ป้องกันการสั่งซื้อเกินจำนวน",
        "โค้ดมีเทสต์อัตโนมัติ 21 รายการ และพร้อม Deploy บน Render",
    ], S))
    story.append(Spacer(1, 0.3 * cm))
    story.append(Paragraph(
        "จัดทำโดย นักศึกษา KPRU  -  " + thai_date(datetime.now()), S["small"]))

    doc.build(story, onFirstPage=footer, onLaterPages=footer)
    return out_path


if __name__ == "__main__":
    path = build()
    print("PDF created:", path)
