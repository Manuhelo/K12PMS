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
