from django.db import transaction
from django.shortcuts import get_object_or_404

from rest_framework import permissions, status, viewsets
from rest_framework import filters
from rest_framework.authentication import SessionAuthentication, TokenAuthentication
from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from .models import Product, CartItem, Order, OrderItem
from .serializers import (
    ProductSerializer,
    RegisterSerializer,
    UserSerializer,
    OrderSerializer,
)
from .views import get_or_create_cart


class IsStaffOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return bool(request.user and request.user.is_staff)


class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all().order_by("-id")
    serializer_class = ProductSerializer
    permission_classes = [IsStaffOrReadOnly]
    filter_backends = [filters.SearchFilter]
    search_fields = ("name",)


class RegisterView(viewsets.ViewSet):
    permission_classes = [permissions.AllowAny]

    def create(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            token, _ = Token.objects.get_or_create(user=user)
            return Response(
                {"user": UserSerializer(user).data, "token": token.key},
                status=status.HTTP_201_CREATED,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CurrentUserView(viewsets.ViewSet):
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def list(self, request):
        return Response(UserSerializer(request.user).data)


class OrderViewSet(viewsets.ViewSet):
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def list(self, request):
        orders = Order.objects.filter(user=request.user).order_by("-created_at")
        return Response(OrderSerializer(orders, many=True).data)

    def retrieve(self, request, pk=None):
        order = get_object_or_404(Order, pk=pk, user=request.user)
        return Response(OrderSerializer(order).data)

    def create(self, request):
        cart = get_or_create_cart(request.user)
        cart_items = cart.items.select_related("product")
        items = list(cart_items)
        if not items:
            return Response({"detail": "ตะกร้าว่างเปล่า"}, status=status.HTTP_400_BAD_REQUEST)

        for item in items:
            if item.quantity > item.product.stock:
                return Response(
                    {"detail": f"{item.product.name} มีสินค้าไม่เพียงพอ (เหลือ {item.product.stock})"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        with transaction.atomic():
            order = Order.objects.create(user=request.user, total_price=cart.total_price())
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
                product.save(update_fields=["stock"])
            cart_items.delete()
        return Response(OrderSerializer(order).data, status=status.HTTP_201_CREATED)


@api_view(["GET", "POST"])
@permission_classes([permissions.IsAuthenticated])
def cart_api(request):
    cart = get_or_create_cart(request.user)
    if request.method == "GET":
        data = [
            {
                "id": item.id,
                "product_id": item.product.id,
                "product_name": item.product.name,
                "quantity": item.quantity,
                "subtotal": str(item.subtotal()),
            }
            for item in cart.items.all()
        ]
        return Response({"items": data, "total_price": str(cart.total_price())})

    product_id = request.data.get("product_id")
    quantity = int(request.data.get("quantity", 1))
    product = get_object_or_404(Product, pk=product_id)

    if product.stock <= 0:
        return Response({"detail": "สินค้าหมดสต็อก"}, status=status.HTTP_400_BAD_REQUEST)

    item, created = CartItem.objects.get_or_create(cart=cart, product=product)
    new_quantity = quantity if created else item.quantity + quantity
    if new_quantity > product.stock:
        return Response(
            {"detail": f"มีสินค้าเหลือเพียง {product.stock} ชิ้น"},
            status=status.HTTP_400_BAD_REQUEST,
        )
    item.quantity = new_quantity
    item.save()
    return Response({"detail": "เพิ่มลงตะกร้าแล้ว"}, status=status.HTTP_201_CREATED)


@api_view(["DELETE"])
@permission_classes([permissions.IsAuthenticated])
def cart_item_api(request, pk):
    cart = get_or_create_cart(request.user)
    item = get_object_or_404(CartItem, pk=pk, cart=cart)
    item.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)