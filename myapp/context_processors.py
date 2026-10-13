from .models import Cart

def cart_context(request):
    """ทำให้ทุก template เข้าถึงจำนวนสินค้าในตะกร้าได้ผ่านตัวแปร nav_cart_count"""
    if request.user.is_authenticated:
        cart, created = Cart.objects.get_or_create(user=request.user)
        return {'nav_cart_count': cart.total_items()}
    return {'nav_cart_count': 0}