from django.contrib import admin
from .models import (
    Warehouse,
    InventoryItem,
    GoodsReceipt,
    GoodsReceiptItem,
    StockAdjustment,
    StockHistory,
)
from django import forms


from django.forms.models import BaseInlineFormSet

class GoodsReceiptItemInlineFormSet(BaseInlineFormSet):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        parent_obj = kwargs.get('instance')

        if parent_obj and getattr(parent_obj, 'purchase_order_id', None):
            try:
                po = parent_obj.purchase_order
                product_ids = po.vendor_bid.quotations.values_list(
                    'rfq_item__request_item__product_id', flat=True
                )
                for form in self.forms:
                    if 'product' in form.fields:
                        form.fields['product'].queryset = form.fields['product'].queryset.filter(id__in=product_ids)
            except Exception:
                pass  # silently ignore on creation


@admin.register(Warehouse)
class WarehouseAdmin(admin.ModelAdmin):
    list_display = ('name', 'location', 'manager')
    search_fields = ('name', 'location')


@admin.register(InventoryItem)
class InventoryItemAdmin(admin.ModelAdmin):
    list_display = ('product', 'quantity_in_stock')
    search_fields = ('product__product_description',)
    list_filter = ('product__sub_category',)

    def has_delete_permission(self, request, obj=None):
        return False  # Prevent accidental deletions


class GoodsReceiptItemInline(admin.TabularInline):
    model = GoodsReceiptItem
    formset = GoodsReceiptItemInlineFormSet
    extra = 0


@admin.register(GoodsReceipt)
class GoodsReceiptAdmin(admin.ModelAdmin):
    list_display = ('purchase_order', 'warehouse', 'received_by', 'received_at')
    search_fields = ('purchase_order__po_number',)
    list_filter = ('warehouse', 'received_at')
    inlines = [GoodsReceiptItemInline]

    def delete_model(self, request, obj):
        # Ensures the custom delete logic runs
        obj.delete()

    def delete_queryset(self, request, queryset):
        # For bulk deletes
        for obj in queryset:
            obj.delete()

    class Media:
        js = ('js/grn_filter.js',)  # static path to custom JS




@admin.register(StockAdjustment)
class StockAdjustmentAdmin(admin.ModelAdmin):
    list_display = ('product', 'adjustment_type', 'quantity', 'adjusted_by', 'adjusted_at')
    list_filter = ('adjustment_type', 'adjusted_at')
    search_fields = ('product__product_description', 'adjusted_by__email')


@admin.register(StockHistory)
class StockHistoryAdmin(admin.ModelAdmin):
    list_display = (
        'product', 'action_type', 'changed_quantity',
        'previous_quantity', 'new_quantity', 'reference_id', 'changed_by', 'changed_at'
    )
    search_fields = ('product__product_description', 'reference_id', 'changed_by__email')
    list_filter = ('action_type', 'changed_at')

    def has_delete_permission(self, request, obj=None):
        return False