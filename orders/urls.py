from django.urls import path
from . import views

urlpatterns = [
    path('upload/', views.upload_student_orders, name='upload_student_orders'),
    path('upload-order-summary/', views.upload_order_summary, name='upload_order_summary'),
    path('orders/upload/sample/', views.download_student_order_sample, name='download_student_order_sample'),
    path('dashboard/', views.order_inventory_dashboard, name='order_inventory_dashboard'),
]
