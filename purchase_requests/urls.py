# purchase/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('requests/', views.purchase_request_list, name='purchase_request_list'),
    path('requests/create/', views.create_purchase_request, name='create_purchase_request'),
    path('requests/<int:pk>/edit/', views.update_purchase_request, name='update_purchase_request'),
    path('requests/<int:pk>/delete/', views.delete_purchase_request, name='delete_purchase_request'),
    path('requests/<int:pk>/status/<str:new_status>/', views.update_request_status, name='update_purchase_status'),
    path('purchase-requests/upload/', views.bulk_upload_purchase_requests_csv, name='bulk_upload_purchase_requests'),
    path('purchase-requests/sample/', views.download_sample_template, name='download_sample_template'),
    path('purchase-requests/<int:pk>/', views.purchase_request_detail, name='purchase_request_detail'),
    
]