from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import user_passes_test, login_required
from django.contrib.auth import logout, login
from django.contrib.auth.models import User
from django.contrib import messages
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q

from .models import Product, UserProfile, Cart, CartItem, Order, OrderItem
from .forms import (
    RegisterForm,
    ProductForm,
    StaffUserForm,
    ProfileForm,
)

ITEMS_PER_PAGE = 6


# --- helpers ---
def is_staff_user(user):
    return user.is_authenticated and (user.is_staff or user.is_superuser)


# --- storefront pages ---

def home(request):
    featured_products = Product.objects.filter(is_active=True).order_by('-id')[:6]
    return render(request, 'home.html', {'featured_products': featured_products})


def product(request):
    qs = Product.objects.filter(is_active=True).order_by('-id')
    q = request.GET.get('q', '').strip()
    if q:
        qs = qs.filter(Q(name__icontains=q))
    paginator = Paginator(qs, ITEMS_PER_PAGE)
    page_number = request.GET.get('page')
    try:
        page_obj = paginator.get_page(page_number)
    except (PageNotAnInteger, EmptyPage):
        page_obj = paginator.get_page(1)
    return render(request, 'product.html', {
        'products': page_obj,
        'page_obj': page_obj,
        'q': q,
    })


def contact(request):
    return render(request, 'contact.html')


def health_check(request):
    from django.http import JsonResponse
    return JsonResponse({"status": "ok"})


def logout_view(request):
    logout(request)
    return redirect('home')


# --- registration ---
def register_view(request):
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f"ยินดีต้อนรับ {user.username}! สมัครสมาชิกสำเร็จแล้ว")
            return redirect('home')
    else:
        form = RegisterForm()
    return render(request, 'register.html', {'form': form})


# --- dashboard ---
@user_passes_test(is_staff_user, login_url='login')
def dashboard(request):
    product_q = request.GET.get('pq', '').strip()
    user_q = request.GET.get('uq', '').strip()

    products = Product.objects.all().order_by('-id')
    if product_q:
        products = products.filter(Q(name__icontains=product_q))

    users = User.objects.all().order_by('-id')
    if user_q:
        users = users.filter(Q(username__icontains=user_q) | Q(email__icontains=user_q))

    product_paginator = Paginator(products, ITEMS_PER_PAGE)
    user_paginator = Paginator(users, ITEMS_PER_PAGE)

    product_page = product_paginator.get_page(request.GET.get('ppage'))
    user_page = user_paginator.get_page(request.GET.get('upage'))

    return render(request, 'dashboard.html', {
        'products': product_page,
        'product_page': product_page,
        'users': user_page,
        'user_page': user_page,
        'product_q': product_q,
        'user_q': user_q,
    })


# --- product CRUD ---
@user_passes_test(is_staff_user, login_url='login')
def add_product(request):
    if request.method == "POST":
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            product = form.save()
            messages.success(request, f"เพิ่มสินค้า {product.name} เรียบร้อยแล้ว")
            return redirect('dashboard')
        # If invalid, fall through and re-render dashboard-like page is complex;
        # store errors in messages and redirect.
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(request, f"{field}: {error}")
    return redirect('dashboard')


@user_passes_test(is_staff_user, login_url='login')
def edit_product(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == "POST":
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            form.save()
            messages.success(request, f"แก้ไขสินค้า {product.name} เรียบร้อยแล้ว")
            return redirect('dashboard')
    else:
        form = ProductForm(instance=product)
    return render(request, 'product_form.html', {
        'form': form,
        'product': product,
        'title': 'แก้ไขสินค้า',
    })


@user_passes_test(is_staff_user, login_url='login')
def order_list(request):
    qs = Order.objects.select_related("user").prefetch_related("items").order_by("-created_at")

    q = request.GET.get("q", "").strip()
    status_filter = request.GET.get("status", "").strip()

    if q:
        qs = qs.filter(Q(user__username__icontains=q) | Q(id__icontains=q))
    if status_filter:
        qs = qs.filter(status=status_filter)

    paginator = Paginator(qs, ITEMS_PER_PAGE)
    page_obj = paginator.get_page(request.GET.get("page"))

    return render(request, "order_list.html", {
        "orders": page_obj,
        "page_obj": page_obj,
        "q": q,
        "status_filter": status_filter,
        "statuses": Order.STATUS_CHOICES,
    })


@user_passes_test(is_staff_user, login_url='login')
def update_order_status(request, pk):
    order = get_object_or_404(Order, pk=pk)
    if request.method == "POST":
        new_status = request.POST.get("status", "").strip()
        valid_statuses = {key for key, _ in Order.STATUS_CHOICES}
        if new_status in valid_statuses:
            order.status = new_status
            order.save(update_fields=["status"])
            messages.success(request, f"อัปเดตคำสั่งซื้อ #{order.id} เป็น \"{order.get_status_display()}\" แล้ว")
        else:
            messages.error(request, "สถานะไม่ถูกต้อง")
    return redirect("order_list")


@user_passes_test(is_staff_user, login_url='login')
def delete_product(request, pk):
    product = get_object_or_404(Product, pk=pk)
    name = product.name
    product.delete()
    messages.success(request, f"ลบสินค้า {name} เรียบร้อยแล้ว")
    return redirect('dashboard')


# --- user CRUD (staff only) ---
@user_passes_test(is_staff_user, login_url='login')
def add_user(request):
    if request.method == "POST":
        form = StaffUserForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            user = User.objects.create_user(
                username=data['username'],
                email=data['email'],
                password=data['password'] if data['password'] else None,
            ) if False else None
            # create_user requires password; handle missing password by setting unusable
            user = User(username=data['username'], email=data['email'])
            if data['password']:
                user.set_password(data['password'])
            else:
                user.set_unusable_password()
            if data['role'] == 'staff':
                user.is_staff = True
            elif data['role'] == 'admin':
                user.is_staff = True
                user.is_superuser = True
            user.save()
            messages.success(request, f"สร้างบัญชี {user.username} เรียบร้อยแล้ว!")
            return redirect('dashboard')
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(request, f"{field}: {error}")
    return redirect('dashboard')


@user_passes_test(is_staff_user, login_url='login')
def edit_user(request, pk):
    user = get_object_or_404(User, pk=pk)
    if request.method == "POST":
        form = StaffUserForm(request.POST, instance=user)
        if form.is_valid():
            data = form.cleaned_data
            user.username = data['username']
            user.email = data['email']
            if data['password']:
                user.set_password(data['password'])
            if data['role'] == 'staff':
                user.is_staff = True
                user.is_superuser = False
            elif data['role'] == 'admin':
                user.is_staff = True
                user.is_superuser = True
            else:
                user.is_staff = False
                user.is_superuser = False
            user.save()
            messages.success(request, f"แก้ไขบัญชี {user.username} เรียบร้อยแล้ว")
            return redirect('dashboard')
    else:
        initial_role = 'admin' if user.is_superuser else ('staff' if user.is_staff else 'member')
        form = StaffUserForm(instance=user, initial={'role': initial_role})
    return render(request, 'user_form.html', {
        'form': form,
        'edited_user': user,
        'title': 'แก้ไขสมาชิก/พนักงาน',
    })


@user_passes_test(is_staff_user, login_url='login')
def delete_user(request, pk):
    if request.user.id != pk:
        user = get_object_or_404(User, pk=pk)
        username = user.username
        user.delete()
        messages.success(request, f"ลบบัญชี {username} เรียบร้อยแล้ว")
    else:
        messages.error(request, "คุณไม่สามารถลบบัญชีที่กำลังล็อกอินอยู่ได้!")
    return redirect('dashboard')


# --- user profile ---
@login_required
def profile_view(request):
    profile, created = UserProfile.objects.get_or_create(user=request.user)

    if request.method == "POST":
        form = ProfileForm(request.POST, request.FILES, instance=profile, user=request.user)
        if form.is_valid():
            profile = form.save(commit=False)
            profile.user = request.user
            profile.save()
            request.user.email = form.cleaned_data.get('email', request.user.email)
            request.user.save()
            messages.success(request, "บันทึกข้อมูลโปรไฟล์เรียบร้อยแล้ว")
            return redirect('profile')
    else:
        form = ProfileForm(instance=profile, user=request.user)

    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'profile.html', {
        'profile': profile,
        'form': form,
        'orders': orders,
    })


# --- cart ---
def get_or_create_cart(user):
    cart, created = Cart.objects.get_or_create(user=user)
    return cart


@login_required
def cart_view(request):
    cart = get_or_create_cart(request.user)
    return render(request, 'cart.html', {'cart': cart})


@login_required
def cart_add(request, pk):
    product = get_object_or_404(Product, pk=pk)
    cart = get_or_create_cart(request.user)

    item, created = CartItem.objects.get_or_create(cart=cart, product=product)
    if not created:
        item.quantity += 1
    item.save()

    messages.success(request, f"เพิ่ม \"{product.name}\" ลงตะกร้าแล้ว")
    return redirect('product')


@login_required
def cart_update(request, pk):
    cart = get_or_create_cart(request.user)
    item = get_object_or_404(CartItem, pk=pk, cart=cart)

    if request.method == "POST":
        try:
            quantity = int(request.POST.get('quantity', 1))
        except ValueError:
            quantity = 1

        if quantity <= 0:
            item.delete()
        else:
            item.quantity = quantity
            item.save()

    return redirect('cart')


@login_required
def cart_remove(request, pk):
    cart = get_or_create_cart(request.user)
    item = get_object_or_404(CartItem, pk=pk, cart=cart)
    item.delete()
    messages.success(request, "ลบสินค้าออกจากตะกร้าแล้ว")
    return redirect('cart')


@login_required
def checkout(request):
    cart = get_or_create_cart(request.user)
    items = cart.items.all()

    if not items.exists():
        messages.error(request, "ตะกร้าของคุณว่างเปล่า กรุณาเลือกสินค้าก่อน")
        return redirect('cart')

    order = Order.objects.create(user=request.user, total_price=cart.total_price())
    for item in items:
        OrderItem.objects.create(
            order=order,
            product=item.product,
            product_name=item.product.name,
            price=item.product.price,
            quantity=item.quantity
        )

    items.delete()
    messages.success(request, f"สั่งซื้อสำเร็จ! หมายเลขคำสั่งซื้อ #{order.id}")
    return redirect('profile')
