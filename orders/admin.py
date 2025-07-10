from django.contrib import admin
from .models import StudentOrder, OrderSummary, ProcurementThreshold    

@admin.register(StudentOrder)
class StudentOrderAdmin(admin.ModelAdmin):
    list_display = ['academic_year', 'warehouse', 'enrollment_code', 'sku', 'quantity', 'paid_date']
    search_fields = ['enrollment_code', 'student_name']


@admin.register(OrderSummary)
class OrderSummaryAdmin(admin.ModelAdmin):
    list_display = ('warehouse', 'grade', 'sku', 'total_quantity')
    list_filter = ('warehouse', 'grade')
    search_fields = ('sku__sku', 'sku__product_description')

@admin.register(ProcurementThreshold)
class ProcurementThresholdAdmin(admin.ModelAdmin):
    list_display = ('threshold_name', 'ok_threshold', 'mandatory_threshold', 'is_active')