from .models import Cart, Category, Wishlist


def cart_context(request):
    """ทำให้ทุก template เข้าถึงจำนวนสินค้าในตะกร้าและหมวดหมู่ได้"""
    data = {
        "nav_cart_count": 0,
        "nav_wishlist_count": 0,
        "nav_categories": Category.objects.all(),
    }
    if request.user.is_authenticated:
        cart, created = Cart.objects.get_or_create(user=request.user)
        data["nav_cart_count"] = cart.total_items()
        data["nav_wishlist_count"] = Wishlist.objects.filter(user=request.user).count()
    return data
