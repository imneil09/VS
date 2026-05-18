from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # Home
    path('', views.home, name='home'),

    # Authentication
    path('login/', views.login_view, name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='home'), name='logout'),
    path('registerTeacher/', views.registerSeller, name='registerSeller'),
    path('registerStudent/', views.registerBuyer, name='registerBuyer'),

    # Dashboards
    path('dashboardTeacher/', views.dashboardSeller, name='dashboardSeller'),
    path('dashboardStudent/', views.dashboardBuyer, name='dashboardBuyer'),

    # Study materials
    path('materials/', views.materials, name='materials'),
    path('upload/', views.upload, name='upload'),
    path('update/<int:pk>/', views.update, name='update'),

    # Checkout & payment
    path('checkout/<int:material_id>/', views.checkout, name='checkout'),
    path('verify-payment/', views.verify_payment, name='verify_payment'),

    # Static or fallback views
    path('not_verified/', views.not_verified, name='not_verified'),
]
