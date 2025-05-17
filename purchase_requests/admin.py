from django.contrib import admin
from .models import PurchaseRequest, RequestItem
from products.models import EducationalProduct
from .forms import PurchaseRequestUploadForm
import openpyxl
from openpyxl.utils import get_column_letter
from django.http import HttpResponse

from django.contrib.auth import get_user_model
from django.urls import path, reverse
from django.shortcuts import render, redirect
from django.contrib import messages
from django.utils import timezone
import pandas as pd

from django import forms    


User = get_user_model()



@admin.register(PurchaseRequest)
class PurchaseRequestAdmin(admin.ModelAdmin):
    list_display = ('request_number', 'requested_by', 'status', 'description', 'created_at','updated_at')
    change_list_template = "admin/purchase_requests/purchase_request_changelist.html"
    actions = ['submit_request','mark_as_reviewed', 'send_back_for_rework','export_with_items_to_excel']

    
    def formfield_for_choice_field(self, db_field, request, **kwargs):
        if db_field.name == 'status':
            user = request.user
            original_choices = db_field.choices

            if user.role == 'ProcurementManager':
                allowed_choices = ['Under Review', 'Rework Required', 'Reviewed']
                kwargs['choices'] = [choice for choice in original_choices if choice[0] in allowed_choices]

            elif user.role == 'DepartmentUser':
                allowed_choices = ['Draft', 'Submitted']
                kwargs['choices'] = [choice for choice in original_choices if choice[0] in allowed_choices]

            else:
                # For all other users, remove status field
                kwargs['choices'] = []

        return super().formfield_for_choice_field(db_field, request, **kwargs)
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "requested_by":
            queryset = kwargs.get("queryset", User.objects.all())
            kwargs["queryset"] = queryset.filter(id=request.user.id)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


    def change_view(self, request, object_id, form_url='', extra_context=None):
        extra_context = extra_context or {}
        export_url = reverse('admin:purchase_request_export', args=[object_id])
        extra_context['export_url'] = export_url
        return super().change_view(request, object_id, form_url, extra_context=extra_context)
    

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('upload/', self.admin_site.admin_view(self.upload_csv), name='purchase_request_upload'),
            path('export/<int:pk>/', self.admin_site.admin_view(self.export_excel), name='purchase_request_export'),
        ]
        return custom_urls + urls
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)

        print("request.user:", request.user, type(request.user))

        if request.user.role == 'DepartmentUser':
            return qs.filter(requested_by=request.user)
        elif request.user.role == 'ProcurementManager':
            # Exclude Drafts
            return qs.exclude(status='Draft')
            # return qs.filter(status__in=['Submitted', 'Under Review'])
        return qs

    def get_readonly_fields(self, request, obj=None):
        if not obj:
            return []

        user = request.user
        if user.role == 'DepartmentUser':
            if obj.status in ['Submitted', 'Under Review', 'Reviewed']:
                return [f.name for f in self.model._meta.fields if f.name != 'status']
        elif user.role == 'ProcurementManager':
            # Let PM edit only the status
            return [f.name for f in self.model._meta.fields if f.name not in ['status', 'remarks']]
        return []

    def has_change_permission(self, request, obj=None):
        user = request.user
        if user.role == 'DepartmentUser' and obj:
            return obj.status in ['Draft', 'Rework Required']
        
        # ProcurementManager should not be able to change anything
        if user.role == 'ProcurementManager':
            return True
        return super().has_change_permission(request, obj)
    
    # ✅ Add this method
    def submit_request(self, request, queryset):
        updated = queryset.update(status='Submitted')
        self.message_user(request, f"{updated} request(s) submitted for review.")
    submit_request.short_description = "Submit to Procurement for Review"

    def mark_as_reviewed(self, request, queryset):
        updated = queryset.update(status='Reviewed')
        self.message_user(request, f"{updated} request(s) marked as Reviewed.")
    mark_as_reviewed.short_description = "Approve Request (Mark as Reviewed)"

    def send_back_for_rework(self, request, queryset):
        updated = queryset.update(status='Rework Required')
        self.message_user(request, f"{updated} request(s) sent back for rework.")
    send_back_for_rework.short_description = "Send Back to Department for Rework"

    def upload_csv(self, request):
        if request.method == "POST":
            form = PurchaseRequestUploadForm(request.POST, request.FILES)
            if form.is_valid():
                try:
                    df = pd.read_csv(request.FILES['file'])
                except Exception:
                    messages.error(request, "Invalid CSV format.")
                    return redirect("..")

                df['sku'] = df['sku'].astype(str).str.strip().str.upper()
                skus = df['sku'].tolist()

                # Normalize DB SKUs as well
                existing_products_qs = EducationalProduct.objects.filter(sku__in=skus)
                existing_products = {p.sku.strip().upper(): p for p in existing_products_qs}

                missing_skus = [sku for sku in skus if sku not in existing_products]

                if missing_skus:
                    messages.error(request, f"Purchase request not created. Missing SKUs: {', '.join(missing_skus)}")
                    return redirect("..")

                # Create purchase request
                now = timezone.now()
                user = request.user
                description = form.cleaned_data['description']
                remarks = form.cleaned_data['remarks']
                request_number = f"REQ-{now.strftime('%Y%m%d')}-{PurchaseRequest.objects.count() + 1:03d}"

                purchase_request = PurchaseRequest.objects.create(
                    requested_by=user,
                    description=description,
                    status='Draft',
                    remarks=remarks,
                    request_number=request_number
                )

                for _, row in df.iterrows():
                    sku = row['sku']
                    quantity = int(row.get('quantity', 0))
                    item_remarks = row.get('remarks', '')

                    product = existing_products.get(sku)  # Now it's safe!
                    RequestItem.objects.create(
                        purchase_request=purchase_request,
                        product=product,
                        quantity=quantity,
                        remarks=item_remarks
                    )

                messages.success(request, f"Purchase Request {purchase_request.request_number} created successfully.")
                return redirect("..")

        else:
            form = PurchaseRequestUploadForm()

        return render(request, "admin/purchase_requests/purchase_request_upload.html", {"form": form})
    
    def export_excel(self, request, pk):
        from .models import PurchaseRequest  # adjust if needed

        pr = PurchaseRequest.objects.get(pk=pk)

        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Purchase Request"

        headers = [
            'Request ID', 'Status', 'Requested By', 'Created At',
            'Item ID', 'Product Name', 'Category', 'Subcategory', 'Grade', 'Quantity'
        ]
        ws.append(headers)

        for item in pr.request_items.all():
            product = item.product
            ws.append([
                pr.request_number,
                pr.status,
                pr.requested_by.username,
                pr.created_at.strftime("%Y-%m-%d %H:%M"),
                product.sku,
                product.product_description,
                product.category,
                product.sub_category,
                product.grade,
                item.quantity
            ])

        for col in ws.columns:
            max_length = max(len(str(cell.value) if cell.value else "") for cell in col)
            ws.column_dimensions[get_column_letter(col[0].column)].width = max_length + 2

        response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = f'attachment; filename=purchase_request_{pk}.xlsx'
        wb.save(response)
        return response

# admin.site.register(PurchaseRequest)
# admin.site.register(RequestItem)

@admin.register(RequestItem)
class RequestItemAdmin(admin.ModelAdmin):
    list_display = ('purchase_request', 'product', 'quantity','category', 
        'subcategory', 
        'grade')
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        print("request.user:", request.user, type(request.user))
        if request.user.role == 'ProcurementManager':
            # Show items only for non-Draft requests
            return qs.exclude(purchase_request__status='Draft')
        elif request.user.role == 'DepartmentUser':
            return qs.filter(purchase_request__requested_by=request.user)
        return qs
    
    def category(self, obj):
        return obj.product.category if obj.product else None

    def subcategory(self, obj):
        return obj.product.sub_category if obj.product else None

    def grade(self, obj):
        return obj.product.grade if obj.product else None

    def has_change_permission(self, request, obj=None):
        if request.user.role == 'ProcurementManager':
            return False
        
        if obj and obj.purchase_request.status not in ['Draft', 'Rework Required']:
            return False
        
        return super().has_change_permission(request, obj)

    def has_add_permission(self, request):

        if request.user.role == 'ProcurementManager':
            return False
        
        # Only allow adding if purchase request ID is in the URL and it's in Draft
        purchase_request_id = request.GET.get('purchase_request__id__exact')
        if purchase_request_id:
            try:
                pr = PurchaseRequest.objects.get(id=purchase_request_id)
                return pr.status in ['Draft', 'Rework Required']
            except PurchaseRequest.DoesNotExist:
                return False
        return True

    def has_delete_permission(self, request, obj=None):
        if request.user.role == 'ProcurementManager':
            return False
        
        if obj and obj.purchase_request.status not in ['Draft', 'Rework Required']:
            return False
        return super().has_delete_permission(request, obj)
    
