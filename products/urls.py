# purchase/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('products/', views.product_list_view, name='product_list'),
    path('products/download/csv/', views.download_products_csv, name='download_products_csv'),
    path('products/download/excel/', views.download_products_excel, name='download_products_excel'),
  
    
]