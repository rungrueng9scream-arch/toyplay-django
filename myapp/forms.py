from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError

from .models import Product, UserProfile, Category, Review


class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=False, label="อีเมล")

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")
        labels = {
            "username": "ชื่อผู้ใช้",
            "password1": "รหัสผ่าน",
            "password2": "ยืนยันรหัสผ่าน",
        }
        widgets = {
            "username": forms.TextInput(attrs={"class": "form-control", "placeholder": "ตั้งชื่อผู้ใช้ของคุณ"}),
            "email": forms.EmailInput(attrs={"class": "form-control", "placeholder": "เช่น example@email.com"}),
            "password1": forms.PasswordInput(attrs={"class": "form-control", "placeholder": "ตั้งรหัสผ่าน"}),
            "password2": forms.PasswordInput(attrs={"class": "form-control", "placeholder": "กรอกรหัสผ่านอีกครั้ง"}),
        }

    def clean_username(self):
        username = self.cleaned_data.get("username")
        if User.objects.filter(username=username).exists():
            raise ValidationError("ชื่อผู้ใช้นี้ถูกใช้งานไปแล้ว กรุณาใช้ชื่อใหม่")
        return username

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise ValidationError("รหัสผ่านทั้งสองช่องไม่ตรงกัน")
        if password1 and len(password1) < 6:
            raise ValidationError("รหัสผ่านต้องมีความยาวอย่างน้อย 6 ตัวอักษร")
        return password2


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ("name", "category", "description", "price", "stock", "is_active", "image")
        labels = {
            "name": "ชื่อสินค้า",
            "category": "หมวดหมู่",
            "description": "รายละเอียดสินค้า",
            "price": "ราคา",
            "stock": "จำนวนในคลัง",
            "is_active": "เปิดใช้งานสินค้า",
            "image": "รูปภาพสินค้า",
        }
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "category": forms.Select(attrs={"class": "form-select"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "price": forms.NumberInput(attrs={"class": "form-control", "step": "0.01", "min": "0"}),
            "stock": forms.NumberInput(attrs={"class": "form-control", "min": "0"}),
            "is_active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "image": forms.ClearableFileInput(attrs={"class": "form-control", "accept": "image/*"}),
        }

    def clean_price(self):
        price = self.cleaned_data.get("price")
        if price is not None and price < 0:
            raise ValidationError("ราคาต้องไม่ติดลบ")
        return price

    def clean_stock(self):
        stock = self.cleaned_data.get("stock")
        if stock is not None and stock < 0:
            raise ValidationError("จำนวนในคลังต้องไม่ติดลบ")
        return stock


class StaffUserForm(forms.Form):
    username = forms.CharField(
        max_length=150,
        label="ชื่อผู้ใช้",
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "เช่น somchai_d"}),
    )
    email = forms.EmailField(
        required=False,
        label="อีเมล",
        widget=forms.EmailInput(attrs={"class": "form-control", "placeholder": "เช่น somchai@email.com"}),
    )
    password = forms.CharField(
        required=False,
        widget=forms.PasswordInput(attrs={"class": "form-control", "placeholder": "รหัสผ่านเข้าใช้งาน"}),
        label="รหัสผ่าน (ว่างถ้าไม่เปลี่ยน)",
        help_text="อย่างน้อย 6 ตัวอักษร",
    )
    role = forms.ChoiceField(
        choices=[("member", "ลูกค้า / สมาชิกทั่วไป"), ("staff", "พนักงานหลังร้าน"), ("admin", "ผู้ดูแลระบบ (Admin)")],
        label="ระดับสิทธิ์การใช้งาน",
        widget=forms.Select(attrs={"class": "form-select"}),
    )

    def __init__(self, *args, **kwargs):
        self.instance = kwargs.pop("instance", None)
        super().__init__(*args, **kwargs)
        if self.instance is not None:
            self.fields["username"].initial = self.instance.username
            self.fields["email"].initial = self.instance.email
            self.fields["username"].disabled = False

    def clean_username(self):
        username = self.cleaned_data.get("username")
        qs = User.objects.filter(username=username)
        if self.instance is not None:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise ValidationError("ชื่อผู้ใช้นี้ถูกใช้งานไปแล้ว")
        return username

    def clean_password(self):
        password = self.cleaned_data.get("password")
        if password and len(password) < 6:
            raise ValidationError("รหัสผ่านต้องมีความยาวอย่างน้อย 6 ตัวอักษร")
        return password


class ProfileForm(forms.ModelForm):
    email = forms.EmailField(required=False, label="อีเมล")

    class Meta:
        model = UserProfile
        fields = ("phone", "address", "avatar")
        labels = {
            "phone": "เบอร์โทรศัพท์",
            "address": "ที่อยู่จัดส่ง",
            "avatar": "รูปโปรไฟล์",
        }
        widgets = {
            "phone": forms.TextInput(attrs={"class": "form-control"}),
            "address": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "avatar": forms.ClearableFileInput(attrs={"class": "form-control", "accept": "image/*"}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)
        if self.user is not None:
            self.fields["email"].initial = self.user.email


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ("name",)
        labels = {"name": "ชื่อหมวดหมู่"}
        widgets = {"name": forms.TextInput(attrs={"class": "form-control", "placeholder": "เช่น ตุ๊กตาและสัตว์นุ่ม"})}


class ReviewForm(forms.ModelForm):
    rating = forms.ChoiceField(
        choices=[(i, f"{'★' * i} ({i} ดาว)") for i in range(5, 0, -1)],
        label="ให้คะแนน",
        widget=forms.Select(attrs={"class": "form-select"}),
    )

    class Meta:
        model = Review
        fields = ("rating", "comment")
        labels = {"comment": "ความคิดเห็น"}
        widgets = {
            "comment": forms.Textarea(attrs={"class": "form-control", "rows": 3, "placeholder": "แบ่งปันประสบการณ์ของคุณ..."}),
        }
