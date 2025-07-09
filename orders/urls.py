from django.urls import path
from . import views

urlpatterns = [
    path('upload/', views.upload_student_orders, name='upload_student_orders'),
    path('dashboard/', views.order_inventory_dashboard, name='order_inventory_dashboard'),
]
