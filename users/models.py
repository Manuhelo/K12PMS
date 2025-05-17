from django.contrib.auth.models import AbstractUser
from django.db import models

class CustomUser(AbstractUser):
    ROLE_CHOICES = (
        ('Admin', 'Admin'),
        ('ProcurementManager', 'Procurement Manager'),
        ('DepartmentUser', 'Department User'),
        ('WarehouseManager', 'Warehouse Manager'),
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    department = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return self.username
