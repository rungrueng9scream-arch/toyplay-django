from django.db import migrations


CATEGORIES = [
    "หุ่นยนต์และรถบังคับ",
    "ตุ๊กตาและสัตว์นุ่ม",
    "ตัวต่อและบล็อก",
    "บอร์ดเกมและจิ๊กซอว์",
    "ของเล่นกลางแจ้ง",
]

# จับคู่ keyword ในชื่อสินค้า -> หมวดหมู่
PRODUCT_CATEGORY_MAP = [
    ("robot", "หุ่นยนต์และรถบังคับ"),
    ("บังคับ", "หุ่นยนต์และรถบังคับ"),
    ("หุ่นยนต์", "หุ่นยนต์และรถบังคับ"),
    ("ตุ๊กตา", "ตุ๊กตาและสัตว์นุ่ม"),
    ("หมี", "ตุ๊กตาและสัตว์นุ่ม"),
    ("lego", "ตัวต่อและบล็อก"),
    ("ตัวต่อ", "ตัวต่อและบล็อก"),
    ("บล็อก", "ตัวต่อและบล็อก"),
    ("เกมบอร์ด", "บอร์ดเกมและจิ๊กซอว์"),
    ("จิ๊กซอว์", "บอร์ดเกมและจิ๊กซอว์"),
    ("ปืน", "ของเล่นกลางแจ้ง"),
    ("บอล", "ของเล่นกลางแจ้ง"),
    ("ดิโนเสาร์", "ของเล่นกลางแจ้ง"),
    ("รถตู้", "ของเล่นกลางแจ้ง"),
]

COUPONS = [
    ("WELCOME10", 10, "0.00", 0),
    ("TOY20", 20, "1000.00", 100),
]


def seed(apps, schema_editor):
    Category = apps.get_model("myapp", "Category")
    Product = apps.get_model("myapp", "Product")
    Coupon = apps.get_model("myapp", "Coupon")

    cats = {}
    for name in CATEGORIES:
        cat, _ = Category.objects.get_or_create(name=name)
        cats[name] = cat

    for product in Product.objects.all():
        if product.category_id:
            continue
        lowered = product.name.lower()
        for keyword, cat_name in PRODUCT_CATEGORY_MAP:
            if keyword in lowered:
                product.category = cats[cat_name]
                product.save(update_fields=["category"])
                break

    for code, percent, min_amount, limit in COUPONS:
        Coupon.objects.get_or_create(
            code=code,
            defaults={
                "discount_percent": percent,
                "min_order_amount": min_amount,
                "usage_limit": limit,
                "active": True,
            },
        )


class Migration(migrations.Migration):

    dependencies = [
        ("myapp", "0007_category_coupon_order_discount_amount_and_more"),
    ]

    operations = [
        migrations.RunPython(seed, migrations.RunPython.noop),
    ]
