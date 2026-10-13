from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, include, re_path
from django.views.static import serve
from django.contrib.auth import views as auth_views
from myapp import views

urlpatterns = [
    path('', views.home, name='home'),
    path('health/', views.health_check, name='health'),
    path('product/', views.product, name='product'),
    path('contact/', views.contact, name='contact'),
    
    # ระบบหลังบ้าน
    path('dashboard/', views.dashboard, name='dashboard'),
    path('dashboard/product/add/', views.add_product, name='add_product'),
    path('dashboard/product/edit/<int:pk>/', views.edit_product, name='edit_product'),
    path('dashboard/product/delete/<int:pk>/', views.delete_product, name='delete_product'),

    # ระบบจัดการสมาชิก/พนักงาน
    path('dashboard/user/add/', views.add_user, name='add_user'),
    path('dashboard/user/edit/<int:pk>/', views.edit_user, name='edit_user'),
    path('dashboard/user/delete/<int:pk>/', views.delete_user, name='delete_user'),

    # ล็อกอิน / สมัครสมาชิก
    path('login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    path('register/', views.register_view, name='register'),
    
    # ล็อกเอาต์ระบบใหม่ (ส่งไปเคลียร์ค่าที่ views เพื่อป้องกันปัญหาจอขาว)
    path('logout/', views.logout_view, name='logout'),

    # โปรไฟล์สมาชิก
    path('profile/', views.profile_view, name='profile'),

    # REST API (Bonus)
    path('api/', include('myapp.api_urls')),

    # คำสั่งซื้อ (staff/admin)
    path('dashboard/orders/', views.order_list, name='order_list'),
    path('dashboard/orders/update/<int:pk>/', views.update_order_status, name='order_update'),

    # ตะกร้าสินค้า (reload trigger)
    path('cart/', views.cart_view, name='cart'),
    path('cart/add/<int:pk>/', views.cart_add, name='cart_add'),
    path('cart/update/<int:pk>/', views.cart_update, name='cart_update'),
    path('cart/remove/<int:pk>/', views.cart_remove, name='cart_remove'),
    path('checkout/', views.checkout, name='checkout'),
]
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if not settings.DEBUG:
    urlpatterns += [
        re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}),
    ]