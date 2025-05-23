# vendors/admin.py
from django.contrib import admin
from .models import Vendor

@admin.register(Vendor)
class VendorAdmin(admin.ModelAdmin):
    list_display = ('name','contact_person','email','phone','address','is_active')
