from decimal import Decimal

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name="ชื่อหมวดหมู่")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="วันที่สร้าง")

    class Meta:
        verbose_name = "หมวดหมู่สินค้า"
        verbose_name_plural = "จัดการหมวดหมู่สินค้า"
        ordering = ["name"]

    def __str__(self):
        return self.name

from django.db.models.signals import post_save
from django.dispatch import receiver

class Product(models.Model):
    name = models.CharField(max_length=100, verbose_name="ชื่อสินค้า")
    category = models.ForeignKey(
        Category, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="products", verbose_name="หมวดหมู่",
    )
    description = models.TextField(blank=True, verbose_name="รายละเอียดสินค้า")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="ราคา")
    stock = models.IntegerField(default=0, verbose_name="จำนวนในคลัง")
    is_active = models.BooleanField(default=True, verbose_name="เปิดใช้งานสินค้า")
    image = models.ImageField(upload_to='products/', blank=True, null=True, verbose_name="รูปภาพสินค้า")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="วันที่เพิ่ม")

    @property
    def is_in_stock(self):
        return self.stock > 0

    @property
    def is_low_stock(self):
        return 0 < self.stock <= 5

    def __str__(self):
        return self.name


class Review(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="reviews")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="reviews")
    rating = models.PositiveSmallIntegerField(
        default=5, validators=[MinValueValidator(1), MaxValueValidator(5)],
        verbose_name="คะแนน (1-5 ดาว)",
    )
    comment = models.TextField(blank=True, verbose_name="ความคิดเห็น")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="วันที่รีวิว")

    class Meta:
        verbose_name = "รีวิวสินค้า"
        verbose_name_plural = "จัดการรีวิวสินค้า"
        ordering = ["-created_at"]
        unique_together = ("product", "user")

    def __str__(self):
        return f"{self.product.name} - {self.user.username} ({self.rating}★)"


class Wishlist(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="wishlist")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="wishlisted_by")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "รายการโปรด"
        verbose_name_plural = "รายการโปรด"
        ordering = ["-created_at"]
        unique_together = ("user", "product")

    def __str__(self):
        return f"{self.user.username} ♥ {self.product.name}"


class Coupon(models.Model):
    code = models.CharField(max_length=30, unique=True, verbose_name="รหัสคูปอง")
    discount_percent = models.PositiveSmallIntegerField(
        default=10, validators=[MinValueValidator(1), MaxValueValidator(100)],
        verbose_name="ส่วนลด (%)",
    )
    min_order_amount = models.DecimalField(
        max_digits=10, decimal_places=2, default=0, verbose_name="ยอดขั้นต่ำ",
    )
    active = models.BooleanField(default=True, verbose_name="เปิดใช้งาน")
    valid_until = models.DateTimeField(null=True, blank=True, verbose_name="ใช้ได้ถึง")
    usage_limit = models.PositiveIntegerField(default=0, verbose_name="จำกัดจำนวนครั้ง (0 = ไม่จำกัด)")
    used_count = models.PositiveIntegerField(default=0, verbose_name="ใช้ไปแล้ว")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "คูปองส่วนลด"
        verbose_name_plural = "จัดการคูปองส่วนลด"
        ordering = ["-created_at"]

    def is_valid(self):
        if not self.active:
            return False
        if self.valid_until and self.valid_until < timezone.now():
            return False
        if self.usage_limit and self.used_count >= self.usage_limit:
            return False
        return True

    def discount_on(self, amount):
        amount = Decimal(amount)
        return (amount * Decimal(self.discount_percent) / Decimal(100)).quantize(Decimal("0.01"))

    def __str__(self):
        return f"{self.code} (-{self.discount_percent}%)"


class EmployeeProfile(models.Model):
    ROLE_CHOICES = [
        ('staff', 'พนักงานทั่วไป'),
        ('manager', 'ผู้จัดการร้าน'),
    ]
    # ผูกกับ User หลักของ Django (ที่ใช้ล็อกอิน)
    user = models.OneToOneField(User, on_delete=models.CASCADE, verbose_name="บัญชีผู้ใช้")
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='staff', verbose_name="ตำแหน่ง")
    phone = models.CharField(max_length=15, blank=True, verbose_name="เบอร์โทรศัพท์")

    class Meta:
        verbose_name = "ข้อมูลพนักงาน"
        verbose_name_plural = "จัดการพนักงาน"

    def __str__(self):
        return f"{self.user.username} - {self.get_role_display()}"


# --- โปรไฟล์สมาชิกทั่วไป (รูปภาพ, เบอร์โทร, ที่อยู่) ---
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile', verbose_name="บัญชีผู้ใช้")
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True, verbose_name="รูปโปรไฟล์")
    phone = models.CharField(max_length=15, blank=True, verbose_name="เบอร์โทรศัพท์")
    address = models.TextField(blank=True, verbose_name="ที่อยู่จัดส่ง")

    def __str__(self):
        return f"โปรไฟล์ของ {self.user.username}"


# --- ระบบตะกร้าสินค้า ---
class Cart(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='cart', verbose_name="เจ้าของตะกร้า")
    created_at = models.DateTimeField(auto_now_add=True)

    def total_price(self):
        return sum(item.subtotal() for item in self.items.all())

    def total_items(self):
        return sum(item.quantity for item in self.items.all())

    def __str__(self):
        return f"ตะกร้าของ {self.user.username}"


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    def subtotal(self):
        return self.product.price * self.quantity

    def __str__(self):
        return f"{self.product.name} x {self.quantity}"


# --- ระบบประวัติการสั่งซื้อ ---
class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'รอดำเนินการ'),
        ('confirmed', 'ยืนยันคำสั่งซื้อ'),
        ('shipping', 'กำลังจัดส่ง'),
        ('completed', 'สำเร็จ'),
        ('cancelled', 'ยกเลิก'),
    ]
    # ลำดับขั้นตอนการจัดส่ง (ใช้วาด timeline ให้ลูกค้าติดตามสถานะ)
    TRACKING_STATUSES = ['pending', 'confirmed', 'shipping', 'completed']

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders', verbose_name="ผู้สั่งซื้อ")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="วันที่สั่งซื้อ")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name="สถานะ")
    coupon = models.ForeignKey(
        Coupon, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='orders', verbose_name="คูปอง",
    )
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="ส่วนลด")
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="ยอดรวม")

    @property
    def subtotal(self):
        return self.total_price + self.discount_amount

    @property
    def tracking_index(self):
        try:
            return self.TRACKING_STATUSES.index(self.status)
        except ValueError:
            return -1

    def __str__(self):
        return f"คำสั่งซื้อ #{self.id} - {self.user.username}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True)
    product_name = models.CharField(max_length=100, verbose_name="ชื่อสินค้า (ตอนสั่งซื้อ)")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="ราคาต่อชิ้น (ตอนสั่งซื้อ)")
    quantity = models.PositiveIntegerField(default=1)

    def subtotal(self):
        return self.price * self.quantity

    def __str__(self):
        return f"{self.product_name} x {self.quantity}"


# Ensure every user has a profile/cart so template access (e.g. avatar) never
# raises RelatedObjectDoesNotExist and new accounts are usable immediately.
@receiver(post_save, sender=User)
def ensure_user_profile_and_cart(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.get_or_create(user=instance)
        Cart.objects.get_or_create(user=instance)