# inventory/urls.py
from django.urls import path
from .views import *

urlpatterns = [
    path('scan-po/', scan_po, name='scan_po'),

    #Warhouse
    path('warehouse/add/', add_warehouse, name='add_warehouse'),
    path('warehouse/upload/', upload_warehouses, name='upload_warehouses'),
    path('warehouse/manage/', manage_warehouse, name='manage_warehouse'),
    path('warehouse/edit/<int:warehouse_id>/', edit_warehouse, name='edit_warehouse'),
    path('warehouse/delete/<int:warehouse_id>/', delete_warehouse, name='delete_warehouse'),

    #GRN
    path('grn/upload/', upload_grn_items, name='upload_grn_items'),
    path('grn/confirm/', confirm_grn_upload, name='confirm_grn_upload'),
    path('grn/manage/', manage_grns, name='grn_manage'),
    path('grn/<int:grn_id>/', grn_detail, name='grn_detail'),
    path('grn/<int:grn_id>/delete/', delete_grn, name='delete_grn'),
    path('grn/<int:grn_id>/download/', download_grn_detail, name='download_grn_detail'),
    path('grn/<int:grn_id>/download-pdf/', download_grn_pdf, name='download_grn_pdf'),

    #inventory
    path('inventory/', inventory_list, name='inventory_list'),
    path('inventory/history/', stock_history_list, name='stock_history_list'),

    path('not-authorized/', not_authorized, name='not_authorized'),

    #Stock Request
    path('stock-request/create/', create_stock_request, name='create_stock_request'),
    path('stock-request/upload/', bulk_upload_stock_request, name='upload_stock_request_excel'),
    path('download-sample-template/', download_sample_stock_request_excel, name='download_sample_stock_template'),
    path('stock-request/list/', stock_request_list, name='stock_request_list'),
    path('stock-request/action/', stock_request_action, name='stock_request_action'),
    path('stock-request/<int:request_id>/export/', export_stock_requests_excel, name='export_stock_requests_excel'),
    path('stock-request/<int:pk>/', view_stock_request, name='view_stock_request'),
    path('stock-request/<int:pk>/delete/', delete_stock_request, name='delete_stock_request'),

    path('po-details/<str:po_number>/', po_details_by_number, name='po_details_by_number'),
    path('receive/<str:po_number>/', receive_po_view, name='receive_goods'),
    # path('ajax/get-po-products/', get_po_products, name='get_po_products'),
]
