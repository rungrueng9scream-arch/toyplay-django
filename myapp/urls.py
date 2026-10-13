from django.urls import path
from django.contrib.auth import views as auth_views
from myapp import views

urlpatterns = [
    path('', views.home, name='home'),
    path('product/', views.product, name='product'),
    path('contact/', views.contact, name='contact'),
    
    # ระบบหลังบ้าน
    path('dashboard/', views.dashboard, name='dashboard'),
    path('dashboard/product/add/', views.add_product, name='add_product'),
    path('dashboard/product/delete/<int:pk>/', views.delete_product, name='delete_product'),
    
    # ระบบจัดการสมาชิก/พนักงาน
    path('dashboard/user/add/', views.add_user, name='add_user'),
    path('dashboard/user/delete/<int:pk>/', views.delete_user, name='delete_user'),

    # ล็อกอิน / สมัครสมาชิก
    path('login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    path('register/', views.register_view, name='register'),
    
    # ล็อกเอาต์ระบบใหม่ (ส่งไปเคลียร์ค่าที่ views เพื่อป้องกันปัญหาจอขาว)
    path('logout/', views.logout_view, name='logout'),
]