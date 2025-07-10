from django.db import models
from inventory.models import Warehouse  # assuming you have this in inventory app
from products.models import EducationalProduct  # assuming SKU is linked to this

class StudentOrder(models.Model):
    academic_year = models.CharField(max_length=20)
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE)
    enrollment_code = models.CharField(max_length=50)
    student_name = models.CharField(max_length=100)
    gender = models.CharField(max_length=10)
    student_class = models.CharField(max_length=50)
    sku = models.ForeignKey(EducationalProduct, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    paid_date = models.DateField()

    class Meta:
        unique_together = (
            'academic_year', 'warehouse', 'enrollment_code', 'sku',
        )

    def __str__(self):
        return f"{self.enrollment_code} - {self.sku}"
    

class OrderSummary(models.Model):
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE)
    grade = models.CharField(max_length=100)  # e.g., 'Grade 1', 'Grade 2'
    sku = models.ForeignKey(EducationalProduct, on_delete=models.CASCADE)
    total_quantity = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ('warehouse', 'grade', 'sku')
        verbose_name = "Order Summary"
        verbose_name_plural = "Order Summaries"

    def __str__(self):
        return f"{self.warehouse.name} | {self.grade} | {self.sku.sku} → {self.total_quantity}"
    

class ProcurementThreshold(models.Model):
    threshold_name = models.CharField(max_length=100, default="Default")
    low_threshold = models.PositiveIntegerField(default=75)
    medium_threshold = models.PositiveIntegerField(default=85)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.threshold_name

    class Meta:
        verbose_name = "Procurement Threshold"
        verbose_name_plural = "Procurement Thresholds"
