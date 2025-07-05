from django.db import models
from django.utils import timezone
from django.contrib.auth import get_user_model
from products.models import EducationalProduct
from procurement.models import *

User = get_user_model()



class Warehouse(models.Model):
    name = models.CharField(max_length=100)
    location = models.TextField(blank=True)
    manager = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return self.name
    

class InventoryItem(models.Model):
    product = models.ForeignKey(EducationalProduct, on_delete=models.CASCADE)
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE)
    quantity_in_stock = models.IntegerField(default=0)


    class Meta:
        unique_together = ('product', 'warehouse')  # 🔐 Ensures no duplicates

    def __str__(self):
        return f"{self.product.product_description} - {self.warehouse.name} - Stock: {self.quantity_in_stock}"
    
class StockHistory(models.Model):
    ACTION_CHOICES = [
        ('RECEIPT', 'Goods Receipt'),
        ('ADJUST_ADD', 'Adjustment Add'),
        ('ADJUST_REMOVE', 'Adjustment Remove'),
    ]
    product = models.ForeignKey(EducationalProduct, on_delete=models.CASCADE)
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE)
    previous_quantity = models.IntegerField()
    changed_quantity = models.IntegerField()
    new_quantity = models.IntegerField()
    action_type = models.CharField(max_length=20, choices=ACTION_CHOICES)
    reference_id = models.CharField(max_length=100, blank=True)
    changed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    changed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.product.product_description} [{self.action_type}] on {self.changed_at}"


class GoodsReceipt(models.Model):
    purchase_order = models.ForeignKey('procurement.PurchaseOrder', on_delete=models.CASCADE)  # adjust app label
    warehouse = models.ForeignKey('Warehouse', on_delete=models.CASCADE)
    received_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    received_at = models.DateTimeField(auto_now_add=True)
    remarks = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"GRN for PO {self.purchase_order.po_number}"
    
    def delete(self, *args, **kwargs):
        # ✅ Delete each item explicitly so its .delete() method runs
        for item in self.items.all():
            item.delete()
        super().delete(*args, **kwargs)


class GoodsReceiptItem(models.Model):
    receipt = models.ForeignKey(GoodsReceipt, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(EducationalProduct, on_delete=models.PROTECT)
    quantity_received = models.PositiveIntegerField()
    damage_return = models.PositiveIntegerField(null=True,blank=True)

    def save(self, *args, **kwargs):
        # ✅ Validation: ensure product belongs to PO
        po = self.receipt.purchase_order
        valid_product_ids = po.vendor_bid.quotations.values_list(
            'rfq_item__request_item__product_id', flat=True
        )

        if self.product.id not in valid_product_ids:
            raise ValueError("Product not part of the associated Purchase Order.")

        # ✅ Save the item
        super().save(*args, **kwargs)

        # ✅ Update inventory
        inventory_item, _ = InventoryItem.objects.get_or_create(product=self.product, warehouse=self.receipt.warehouse)
        previous = inventory_item.quantity_in_stock
        inventory_item.quantity_in_stock += self.quantity_received
        inventory_item.save()

        # ✅ Record stock history
        StockHistory.objects.create(
            product=self.product,
            warehouse=self.receipt.warehouse,  # ✅ Fix
            previous_quantity=previous,
            changed_quantity=self.quantity_received,
            new_quantity=inventory_item.quantity_in_stock,
            action_type='RECEIPT',
            reference_id=f"GRN-{self.receipt.id}",
            changed_by=self.receipt.received_by
        )
    def delete(self, *args, **kwargs):
        try:
        # Roll back stock
            inventory_item = InventoryItem.objects.get(product=self.product)
            previous = inventory_item.quantity_in_stock
            inventory_item.quantity_in_stock -= self.quantity_received
            inventory_item.save()

            # Record in history
            StockHistory.objects.create(
                product=self.product,
                warehouse=self.receipt.warehouse,  # ✅ Fix
                previous_quantity=previous,
                changed_quantity=-self.quantity_received,
                new_quantity=inventory_item.quantity_in_stock,
                action_type='ADJUST_REMOVE',
                reference_id=f"GRN-DEL-{self.receipt.id}",
                changed_by=self.receipt.received_by
            )
        except InventoryItem.DoesNotExist:
            # Optionally log this
            print(f"⚠️ InventoryItem for product {self.product} not found. Skipping rollback.")

        super().delete(*args, **kwargs)


class POItem(models.Model):
    purchase_order = models.ForeignKey(PurchaseOrder, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(EducationalProduct, on_delete=models.CASCADE)
    quantity_ordered = models.PositiveIntegerField()

    def __str__(self):
        return f"{self.purchase_order.po_number} - {self.product.product_description}"
    
class GRNRecord(models.Model):
    po_item = models.ForeignKey(POItem, on_delete=models.CASCADE, related_name='grn_records')
    grn = models.ForeignKey(GoodsReceipt, on_delete=models.CASCADE)
    quantity_received = models.PositiveIntegerField()
    damage_quantity = models.PositiveIntegerField(default=0)
    received_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.po_item.product} - {self.quantity_received} (GRN)"




class StockAdjustment(models.Model):
    ADJUST_TYPE = [('ADD', 'Add'), ('REMOVE', 'Remove')]
    REASON_TYPE = [
        ('DAMAGE', 'Damaged Stock'),
        ('EXCESS', 'Excess Found'),
        ('MISSING', 'Missing Stock'),
        ('RETURN', 'Customer Return'),
        ('EXPIRED', 'Expired Items'),
        ('CYCLE_COUNT', 'Cycle Count Correction'),
        ('TRANSFER', 'Transfer Adjustment'),
        ('OTHER', 'Other'),
    ]
    product = models.ForeignKey(EducationalProduct, on_delete=models.CASCADE)
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE)
    adjustment_type = models.CharField(max_length=10, choices=ADJUST_TYPE)
    adjustment_reason_type = models.CharField(max_length=20, choices=REASON_TYPE, default='OTHER')  # <-- New field
    quantity = models.PositiveIntegerField()
    reason = models.TextField()
    adjusted_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    adjusted_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        #from inventory.models import InventoryItem, StockHistory
        inventory_item = InventoryItem.objects.get(product=self.product, warehouse=self.warehouse)
        previous = inventory_item.quantity_in_stock

        if self.adjustment_type == 'ADD':
            inventory_item.quantity_in_stock += self.quantity
            change = self.quantity
            action = 'ADJUST_ADD'
        else:
            inventory_item.quantity_in_stock -= self.quantity
            change = -self.quantity
            action = 'ADJUST_REMOVE'

        inventory_item.save()

        StockHistory.objects.create(
            product=self.product,
            previous_quantity=previous,
            changed_quantity=change,
            new_quantity=inventory_item.quantity_in_stock,
            action_type=action,
            reference_id=f"ADJUST-{self.id}",
            changed_by=self.adjusted_by
        )


class StockTransfer(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('IN_TRANSIT', 'In Transit'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
    ]

    product = models.ForeignKey(EducationalProduct, on_delete=models.CASCADE)
    from_warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE, related_name='transfers_out')
    to_warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE, related_name='transfers_in')
    quantity = models.PositiveIntegerField()
    requested_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='transfer_requests')
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='transfer_approvals')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    reason = models.TextField(blank=True)
    requested_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)

        if self.status == 'COMPLETED':
            # Update inventory for both warehouses
            from_item = InventoryItem.objects.get(product=self.product, warehouse=self.from_warehouse)
            to_item, _ = InventoryItem.objects.get_or_create(product=self.product, warehouse=self.to_warehouse)

            from_item.quantity_in_stock -= self.quantity
            to_item.quantity_in_stock += self.quantity

            from_item.save()
            to_item.save()

            # Record in StockHistory
            StockHistory.objects.create(
                product=self.product,
                previous_quantity=from_item.quantity_in_stock + self.quantity,
                changed_quantity=-self.quantity,
                new_quantity=from_item.quantity_in_stock,
                action_type='TRANSFER_OUT',
                reference_id=f"TRANSFER-{self.id}",
                changed_by=self.approved_by or self.requested_by
            )

            StockHistory.objects.create(
                product=self.product,
                previous_quantity=to_item.quantity_in_stock - self.quantity,
                changed_quantity=self.quantity,
                new_quantity=to_item.quantity_in_stock,
                action_type='TRANSFER_IN',
                reference_id=f"TRANSFER-{self.id}",
                changed_by=self.approved_by or self.requested_by
            )


class AcademicYear(models.Model):
    name = models.CharField(max_length=20)  # e.g., "2024-2025"
    start_date = models.DateField()
    end_date = models.DateField()

    def __str__(self):
        return self.name
    
class ProductPrice(models.Model):
    product = models.ForeignKey(EducationalProduct, on_delete=models.CASCADE)
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE)
    cost_price = models.DecimalField(max_digits=10, decimal_places=2)
    selling_price = models.DecimalField(max_digits=10, decimal_places=2)
    added_on = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('product', 'academic_year')  # One price per product per year

    def __str__(self):
        return f"{self.product.product_description} - {self.academic_year.name} - CP: {self.cost_price} - SP: {self.selling_price}"


class StockRequest(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
        ('FULFILLED', 'Fulfilled'),
    ]

    requesting_warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE, related_name='requests_made')
    requested_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    remarks = models.TextField(blank=True)
    requested_at = models.DateTimeField(auto_now_add=True)
    approved_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name='approved_requests')
    approved_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Request #{self.id} from {self.requesting_warehouse.name}"
    
class StockRequestItem(models.Model):
    stock_request = models.ForeignKey(StockRequest, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(EducationalProduct, on_delete=models.CASCADE)
    quantity_requested = models.PositiveIntegerField()
    quantity_approved = models.PositiveIntegerField(null=True, blank=True)  # Optional: if partial approval

    def __str__(self):
        return f"{self.product.product_description} - {self.quantity_requested}"
