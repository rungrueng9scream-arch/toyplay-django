from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework.authtoken.views import obtain_auth_token

from . import api_views

router = DefaultRouter()
router.register(r"products", api_views.ProductViewSet, basename="product")
router.register(r"orders", api_views.OrderViewSet, basename="order")

urlpatterns = [
    path("", include(router.urls)),
    path("auth/register/", api_views.RegisterView.as_view({"post": "create"}), name="api-register"),
    path("auth/login/", obtain_auth_token, name="api-login"),
    path("auth/me/", api_views.CurrentUserView.as_view({"get": "list"}), name="api-me"),
    path("cart/", api_views.cart_api, name="api-cart"),
    path("cart/items/<int:pk>/", api_views.cart_item_api, name="api-cart-item"),
]