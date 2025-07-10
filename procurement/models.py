from django.db import models
from django.utils import timezone
from django.contrib.auth import get_user_model
from purchase_requests.models import PurchaseRequest, RequestItem
from vendors.models import Vendor  # if you have vendor app, or define here
import uuid
from inventory.models import Warehouse, POItem, GoodsReceiptItem
from django.db.models import Sum

User = get_user_model()

class RFQ(models.Model):
    purchase_request = models.ForeignKey(PurchaseRequest, on_delete=models.CASCADE, related_name='rfqs')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=[('Draft', 'Draft'), ('Sent', 'Sent'), ('Closed', 'Closed')], default='Draft')

    def __str__(self):
        return f"RFQ for {self.purchase_request.request_number}"


class RFQItem(models.Model):
    rfq = models.ForeignKey(RFQ, on_delete=models.CASCADE, related_name='rfq_items')
    request_item = models.ForeignKey(RequestItem, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.rfq} - {self.request_item.product}"
    

class VendorBid(models.Model):
    rfq = models.ForeignKey(RFQ, on_delete=models.CASCADE)
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE)
    # NEW FIELD: A unique identifier for each bid submission/upload
    submission_group = models.UUIDField(default=uuid.uuid4, editable=False)
    status = models.CharField(max_length=20, choices=[("Pending", "Pending"), ("Approved", "Approved"), ("Rejected", "Rejected")])
    submitted_at = models.DateTimeField(auto_now_add=True)
    remarks = models.TextField(blank=True, null=True)

    class Meta:
        indexes = [
            models.Index(fields=['rfq']),
            models.Index(fields=['vendor']),
        ]
        unique_together = ('rfq', 'vendor','submission_group')
        

class VendorQuotation(models.Model):
    rfq_item = models.ForeignKey(RFQItem, on_delete=models.CASCADE, related_name='vendor_quotations')
    vendor_bid = models.ForeignKey(VendorBid, on_delete=models.CASCADE, related_name='quotations', null=True, blank=True)  # ✅ instead of vendor
    quoted_price = models.DecimalField(max_digits=10, decimal_places=2)
    lead_time_days = models.PositiveIntegerField()
    remarks = models.TextField(blank=True, null=True)

    class Meta:
        unique_together = ('rfq_item', 'vendor_bid')

    def __str__(self):
        if self.vendor_bid and self.vendor_bid.vendor:
            return f"{self.vendor_bid.vendor.name} quote for {self.rfq_item}"
        return f"Quotation for {self.rfq_item}"


class PurchaseOrder(models.Model):
    vendor_bid = models.ForeignKey(VendorBid, on_delete=models.CASCADE,null=True, blank=True)
    warehouse = models.ForeignKey(Warehouse,on_delete=models.CASCADE,null=True,blank=True)
    po_number = models.CharField(max_length=50, unique=True, blank=True)
    issued_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    issued_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=[
        ('Initiated', 'Initiated'),
        ('Approved', 'Approved'),
        ('Dispatched', 'Dispatched'),
        ('Partially Received', 'Partially Received'),
        ('Delivered', 'Delivered')
    ], default='Initiated')

    def save(self, *args, **kwargs):
        if not self.po_number:
            now = timezone.now()
            count = PurchaseOrder.objects.filter(issued_at__date=now.date()).count() + 1
            self.po_number = f"PO-{now.strftime('%Y%m%d')}-{count:03d}"
        super().save(*args, **kwargs)

    def check_and_update_status(self):
        po_items = POItem.objects.filter(purchase_order=self)
        gr_items = GoodsReceiptItem.objects.filter(receipt__purchase_order=self)
        all_received = True
        any_received = False

        for item in po_items:
            ordered_qty = item.quantity_ordered
            received_qty = gr_items.filter(product=item.product).aggregate(
                total=Sum('quantity_received')
            )['total'] or 0

            # Cap over-receiving
            received_qty = min(received_qty, ordered_qty)

            if received_qty > 0:
                any_received = True
            if received_qty < ordered_qty:
                all_received = False

        if all_received:
            self.status = 'Delivered'
        elif any_received:
            self.status = 'Partially Received'
        else:
            self.status = 'Approved'

        self.save()

    def __str__(self):
        return self.po_number


class DeliveryTracking(models.Model):
    purchase_order = models.OneToOneField(PurchaseOrder, on_delete=models.CASCADE, related_name='delivery')
    estimated_delivery = models.DateField()
    actual_delivery = models.DateField(null=True, blank=True)
    delay_reason = models.TextField(blank=True, null=True)
    received_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='deliveries_received')
    notes = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Delivery for {self.purchase_order.po_number}"
