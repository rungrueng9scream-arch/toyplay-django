from decimal import Decimal

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import user_passes_test, login_required
from django.contrib.auth import logout, login
from django.contrib.auth.models import User
from django.contrib import messages
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db import transaction
from django.db.models import Avg, Count, Q, Sum

from .models import (
    Product,
    UserProfile,
    Cart,
    CartItem,
    Order,
    OrderItem,
    Category,
    Review,
    Wishlist,
    Coupon,
)
from .forms import (
    RegisterForm,
    ProductForm,
    StaffUserForm,
    ProfileForm,
    CategoryForm,
    ReviewForm,
)

ITEMS_PER_PAGE = 6


# --- helpers ---
def is_staff_user(user):
    return user.is_authenticated and (user.is_staff or user.is_superuser)


def is_admin_user(user):
    """Only true superusers (admins) may manage accounts."""
    return user.is_authenticated and user.is_superuser


# --- storefront pages ---

def home(request):
    featured_products = (
        Product.objects.filter(is_active=True)
        .annotate(avg_rating=Avg("reviews__rating"), review_count=Count("reviews"))
        .order_by('-id')[:6]
    )
    categories = Category.objects.annotate(product_count=Count("products")).order_by("name")
    return render(request, 'home.html', {
        'featured_products': featured_products,
        'categories': categories,
    })


def product(request):
    qs = Product.objects.filter(is_active=True).select_related("category")
    q = request.GET.get('q', '').strip()
    category_id = request.GET.get('category', '').strip()
    sort = request.GET.get('sort', '').strip()

    if q:
        qs = qs.filter(Q(name__icontains=q) | Q(description__icontains=q))
    if category_id.isdigit():
        qs = qs.filter(category_id=int(category_id))

    if sort == 'price_asc':
        qs = qs.order_by('price')
    elif sort == 'price_desc':
        qs = qs.order_by('-price')
    elif sort == 'oldest':
        qs = qs.order_by('id')
    else:
        sort = sort or 'newest'
        qs = qs.order_by('-id')

    qs = qs.annotate(avg_rating=Avg("reviews__rating"), review_count=Count("reviews"))

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
        'categories': Category.objects.all(),
        'selected_category': category_id,
        'sort': sort,
    })


def product_detail(request, pk):
    product_obj = get_object_or_404(
        Product.objects.select_related("category"), pk=pk
    )
    reviews = product_obj.reviews.select_related("user")
    avg_rating = reviews.aggregate(avg=Avg("rating"))["avg"]
    user_review = None

    if product_obj.category:
        related = (
            Product.objects.filter(is_active=True, category=product_obj.category)
            .exclude(pk=product_obj.pk)
            .annotate(avg_rating=Avg("reviews__rating"))
        )
    else:
        related = Product.objects.none()
    related = related.order_by('-id')[:4]

    in_wishlist = False
    if request.user.is_authenticated:
        user_review = reviews.filter(user=request.user).first()
        in_wishlist = Wishlist.objects.filter(user=request.user, product=product_obj).exists()

    return render(request, 'product_detail.html', {
        'product': product_obj,
        'reviews': reviews,
        'avg_rating': avg_rating,
        'review_count': reviews.count(),
        'related': related,
        'in_wishlist': in_wishlist,
        'review_form': ReviewForm(instance=user_review),
        'user_review': user_review,
    })


def contact(request):
    return render(request, 'contact.html')


# --- reviews & wishlist ---
@login_required
def review_add(request, pk):
    product_obj = get_object_or_404(Product, pk=pk)
    if request.method == "POST":
        form = ReviewForm(request.POST)
        if form.is_valid():
            Review.objects.update_or_create(
                product=product_obj,
                user=request.user,
                defaults={
                    "rating": form.cleaned_data["rating"],
                    "comment": form.cleaned_data["comment"],
                },
            )
            messages.success(request, "บันทึกรีวิวของคุณเรียบร้อยแล้ว ขอบคุณ!")
        else:
            messages.error(request, "กรุณาให้คะแนนก่อนส่งรีวิว")
    return redirect('product_detail', pk=pk)


@login_required
def wishlist_view(request):
    items = (
        Wishlist.objects.filter(user=request.user)
        .select_related('product', 'product__category')
    )
    return render(request, 'wishlist.html', {'items': items})


@login_required
def wishlist_toggle(request, pk):
    product_obj = get_object_or_404(Product, pk=pk)
    obj, created = Wishlist.objects.get_or_create(user=request.user, product=product_obj)
    if created:
        messages.success(request, f"เพิ่ม \"{product_obj.name}\" ในรายการโปรดแล้ว")
    else:
        obj.delete()
        messages.info(request, f"นำ \"{product_obj.name}\" ออกจากรายการโปรดแล้ว")

    referer = request.META.get('HTTP_REFERER')
    from django.utils.http import url_has_allowed_host_and_scheme
    if referer and url_has_allowed_host_and_scheme(referer, allowed_hosts={request.get_host()}):
        return redirect(referer)
    return redirect('product_detail', pk=pk)


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
            # Make sure dependent rows exist even if migrations/signals were skipped.
            UserProfile.objects.get_or_create(user=user)
            Cart.objects.get_or_create(user=user)
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

    # --- สถิติภาพรวม ---
    revenue = (
        Order.objects.exclude(status='cancelled')
        .aggregate(total=Sum('total_price'))['total'] or Decimal('0')
    )
    stats = {
        'revenue': revenue,
        'total_orders': Order.objects.count(),
        'pending_orders': Order.objects.filter(status='pending').count(),
        'total_members': User.objects.count(),
        'total_products': Product.objects.count(),
        'low_stock_count': Product.objects.filter(stock__lte=5).count(),
    }
    low_stock = (
        Product.objects.filter(stock__lte=5).order_by('stock')[:5]
    )
    top_products = (
        OrderItem.objects.values('product_name')
        .annotate(qty=Sum('quantity'))
        .order_by('-qty')[:5]
    )
    recent_orders = Order.objects.select_related('user').order_by('-created_at')[:5]

    return render(request, 'dashboard.html', {
        'products': product_page,
        'product_page': product_page,
        'users': user_page,
        'user_page': user_page,
        'product_q': product_q,
        'user_q': user_q,
        'stats': stats,
        'low_stock': low_stock,
        'top_products': top_products,
        'recent_orders': recent_orders,
        'categories': Category.objects.all(),
        'category_form': CategoryForm(),
    })


@user_passes_test(is_staff_user, login_url='login')
def add_category(request):
    if request.method == "POST":
        form = CategoryForm(request.POST)
        if form.is_valid():
            category = form.save()
            messages.success(request, f"เพิ่มหมวดหมู่ {category.name} เรียบร้อยแล้ว")
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    return redirect('dashboard')


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


# --- user CRUD (admin only) ---
@user_passes_test(is_admin_user, login_url='login')
def add_user(request):
    if request.method == "POST":
        form = StaffUserForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
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
            # Keep derived records in sync so profile/avatar/cart pages work.
            UserProfile.objects.get_or_create(user=user)
            Cart.objects.get_or_create(user=user)
            messages.success(request, f"สร้างบัญชี {user.username} เรียบร้อยแล้ว!")
            return redirect('dashboard')
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(request, f"{field}: {error}")
    return redirect('dashboard')


@user_passes_test(is_admin_user, login_url='login')
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
            UserProfile.objects.get_or_create(user=user)
            Cart.objects.get_or_create(user=user)
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


@user_passes_test(is_admin_user, login_url='login')
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

    if not product.is_active:
        messages.error(request, f"\"{product.name}\" ไม่พร้อมจำหน่ายในขณะนี้")
        return redirect('product')
    if product.stock <= 0:
        messages.error(request, f"\"{product.name}\" สินค้าหมดสต็อกแล้ว")
        return redirect('product')

    cart = get_or_create_cart(request.user)
    item, created = CartItem.objects.get_or_create(cart=cart, product=product)
    if not created:
        if item.quantity + 1 > product.stock:
            messages.error(request, f"\"{product.name}\" มีสินค้าเหลือเพียง {product.stock} ชิ้น")
            return redirect('cart')
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
            messages.success(request, "ลบสินค้าออกจากตะกร้าแล้ว")
        elif quantity > item.product.stock:
            messages.error(request, f"\"{item.product.name}\" มีสินค้าเหลือเพียง {item.product.stock} ชิ้น")
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
    cart_items = cart.items.select_related('product')
    items = list(cart_items)

    if not items:
        messages.error(request, "ตะกร้าของคุณว่างเปล่า กรุณาเลือกสินค้าก่อน")
        return redirect('cart')

    # ตรวจสต็อกก่อนสร้างคำสั่งซื้อ
    for item in items:
        if item.quantity > item.product.stock:
            messages.error(
                request,
                f"\"{item.product.name}\" มีสินค้าเหลือเพียง {item.product.stock} ชิ้น "
                f"แต่ในตะกร้ามี {item.quantity} ชิ้น",
            )
            return redirect('cart')

    subtotal = cart.total_price()
    discount = Decimal('0.00')
    coupon = None

    coupon_code = request.POST.get('coupon_code', '').strip()
    if coupon_code:
        coupon = Coupon.objects.filter(code__iexact=coupon_code).first()
        if coupon and coupon.is_valid() and subtotal >= coupon.min_order_amount:
            discount = coupon.discount_on(subtotal)
        else:
            coupon = None
            messages.warning(request, "คูปองไม่ถูกต้อง ถูกใช้หมดแล้ว หรือยอดสั่งซื้อไม่ถึงขั้นต่ำ")

    total = subtotal - discount

    with transaction.atomic():
        order = Order.objects.create(
            user=request.user,
            coupon=coupon,
            discount_amount=discount,
            total_price=total,
        )
        for item in items:
            OrderItem.objects.create(
                order=order,
                product=item.product,
                product_name=item.product.name,
                price=item.product.price,
                quantity=item.quantity,
            )
            product = item.product
            product.stock = max(product.stock - item.quantity, 0)
            product.save(update_fields=['stock'])

        if coupon:
            coupon.used_count += 1
            coupon.save(update_fields=['used_count'])

        cart_items.delete()

    messages.success(request, f"สั่งซื้อสำเร็จ! หมายเลขคำสั่งซื้อ #{order.id}")
    return redirect('profile')
