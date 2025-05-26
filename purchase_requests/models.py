from django.db import models
from django.contrib.auth import get_user_model
from products.models import EducationalProduct
from django.utils import timezone

User = get_user_model()

class PurchaseRequest(models.Model):
    SEGMENT_CHOICES = [
        ('OIS', 'OIS'),
        ('B2B', 'B2B'),
        ('OCSE', 'OCSE'),
    ]
    STATUS_CHOICES = [
        ('Draft', 'Draft'),
        ('Submitted', 'Submitted'),
        ('Under Review', 'Under Review'),
        ('Rework Required', 'Rework Required'),
        ('Reviewed', 'Reviewed'),
    ]
    segment = models.CharField(max_length=10, choices=SEGMENT_CHOICES, blank=False, null=False, verbose_name="Segment")
    request_number = models.CharField(max_length=50, unique=True, blank=True)
    requested_by = models.ForeignKey(User, on_delete=models.CASCADE)
    description = models.CharField(max_length=300)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Draft')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    remarks = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.request_number or f"Request by {self.requested_by}"
    
    def save(self, *args, **kwargs):
        is_new = not self.pk

        # Generate request_number if it's a new object or request_number is missing
        if is_new or not self.request_number:
            now = timezone.now()
            count = PurchaseRequest.objects.filter(created_at__date=now.date()).count() + 1
            self.request_number = f"REQ-{now.strftime('%Y%m%d')}-{count:03d}"

        # If it's an update and status changed, record it in history
        if not is_new:
            old = PurchaseRequest.objects.get(pk=self.pk)
            if old.status != self.status:
                PurchaseRequestStatusHistory.objects.create(
                    purchase_request=self,
                    old_status=old.status,
                    new_status=self.status,
                    changed_by=getattr(self, '_changed_by', None),  # set in admin
                    changed_at=timezone.now()
                )

        super().save(*args, **kwargs)

class RequestItem(models.Model):
    purchase_request = models.ForeignKey(PurchaseRequest, on_delete=models.CASCADE, related_name='request_items')
    product = models.ForeignKey(EducationalProduct, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField()
    remarks = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.product.product_description} x {self.quantity}"
    

class PurchaseRequestStatusHistory(models.Model):
    purchase_request = models.ForeignKey(PurchaseRequest, on_delete=models.CASCADE, related_name='status_history')
    old_status = models.CharField(max_length=50)
    new_status = models.CharField(max_length=50)
    changed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    changed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.purchase_request.id} - {self.old_status} → {self.new_status} at {self.changed_at}"

