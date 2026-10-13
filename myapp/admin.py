from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin
from .models import Product, EmployeeProfile

# โค้ดเดิมของคุณ (คงไว้ตามเดิม เพิ่มเติมการค้นหาและตัวกรองให้ใช้งานง่ายขึ้น)
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ["id", "name", "price", "stock", "is_active"]
    search_fields = ["name"]
    list_filter = ["is_active"]

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