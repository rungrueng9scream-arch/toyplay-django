from django.db import models
from django.contrib.auth.models import User

class Product(models.Model):
    name = models.CharField(max_length=100, verbose_name="ชื่อสินค้า")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="ราคา")
    stock = models.IntegerField(default=0, verbose_name="จำนวนในคลัง")
    is_active = models.BooleanField(default=True, verbose_name="เปิดใช้งานสินค้า")
    image = models.ImageField(upload_to='products/', blank=True, null=True, verbose_name="รูปภาพสินค้า")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="วันที่เพิ่ม")

    def __str__(self):
        return self.name


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
        ('completed', 'สำเร็จ'),
        ('cancelled', 'ยกเลิก'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders', verbose_name="ผู้สั่งซื้อ")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="วันที่สั่งซื้อ")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name="สถานะ")
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="ยอดรวม")

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