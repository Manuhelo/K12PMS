# procurement/urls.py

from django.urls import path
from .views import download_po_barcode

print("✅ procurement.urls.py is loaded")

urlpatterns = [
    path('po/<int:po_id>/barcode/', download_po_barcode, name='download_po_barcode'),
]
