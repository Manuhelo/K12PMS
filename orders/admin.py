from django.contrib import admin
from .models import StudentOrder

@admin.register(StudentOrder)
class StudentOrderAdmin(admin.ModelAdmin):
    list_display = ['academic_year', 'warehouse', 'enrollment_code', 'sku', 'quantity', 'paid_date']
    search_fields = ['enrollment_code', 'student_name']
