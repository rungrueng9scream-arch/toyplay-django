from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin
from .models import (
    Product,
    EmployeeProfile,
    Category,
    Review,
    Wishlist,
    Coupon,
    Order,
    OrderItem,
)

# โค้ดเดิมของคุณ (คงไว้ตามเดิม เพิ่มเติมการค้นหาและตัวกรองให้ใช้งานง่ายขึ้น)
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ["id", "name", "category", "price", "stock", "is_active"]
    search_fields = ["name"]
    list_filter = ["is_active", "category"]


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ["id", "name"]
    search_fields = ["name"]


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ["id", "product", "user", "rating", "created_at"]
    list_filter = ["rating"]
    search_fields = ["product__name", "user__username"]


@admin.register(Wishlist)
class WishlistAdmin(admin.ModelAdmin):
    list_display = ["id", "user", "product", "created_at"]


@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ["id", "code", "discount_percent", "min_order_amount", "active", "used_count", "valid_until"]
    list_filter = ["active"]
    search_fields = ["code"]


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ["id", "user", "status", "total_price", "discount_amount", "coupon", "created_at"]
    list_filter = ["status"]
    search_fields = ["user__username"]
    inlines = [OrderItemInline]

# ส่วนที่เพิ่มใหม่: ดึงข้อมูลพนักงานไปแสดงพ่วงในหน้าจัดการสมาชิก (User)
class EmployeeProfileInline(admin.StackedInline):
    model = EmployeeProfile
    can_delete = False
    verbose_name_plural = 'ข้อมูลพนักงานเพิ่มเติม'

# ปรับแต่งหน้าจัดการสมาชิก/พนักงาน ให้ดูง่ายในหน้าแรก
class CustomUserAdmin(UserAdmin):
    inlines = (EmployeeProfileInline,)
    list_display = ["id", "username", "email", "is_staff", "is_active"]
    list_filter = ["is_staff", "is_superuser", "is_active"]

# ยกเลิกการลงทะเบียน User แบบเก่าของ Django แล้วใส่แบบที่เราปรับแต่งเข้าไปแทน
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)