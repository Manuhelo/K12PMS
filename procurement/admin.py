from django.contrib import admin
from django import forms
from django.utils.html import format_html
from django.shortcuts import redirect, render
from django.urls import path, reverse
from django.contrib import messages
from django.template.response import TemplateResponse
import csv
import io
from .forms import VendorQuotationUploadForm
from .models import RFQ, RFQItem, VendorQuotation, VendorBid
from purchase_requests.models import RequestItem, PurchaseRequest
from vendors.models import Vendor
import openpyxl
from openpyxl.utils import get_column_letter
from django.http import HttpResponse


admin.site.register(RFQItem)

# Inline for RFQ Items
class RFQItemInline(admin.TabularInline):
    model = RFQItem
    extra = 1

@admin.register(RFQ)
class RFQAdmin(admin.ModelAdmin):
    list_display = ('id', 'purchase_request', 'created_by', 'created_at', 'status')
    inlines = [RFQItemInline]

@admin.register(VendorBid)
class VendorBidAdmin(admin.ModelAdmin):
    list_display = ('id', 'rfq', 'vendor', 'status', 'submitted_at','approve_button', 'reject_button')  # Show these columns in admin list view
    list_filter = ('status', 'rfq', 'vendor')  # Add filter options in the sidebar
    search_fields = ('vendor__name',)  # Enable search on related fields
    readonly_fields = ('submitted_at',)  # Make 'submitted_at' read-only in form

    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
            "<int:pk>/approve/",
            self.admin_site.admin_view(self.approve_quotation),
            name="vendorquotation_approve",  # optional name for reverse()
        ),
        path("<int:pk>/reject/", self.admin_site.admin_view(self.reject_quotation), name="vendorquotation_reject"),
        ]
        return custom_urls + urls

    def approve_button(self, obj):
        if obj.status == 'Approved':
            return "✅ Approved"
        elif obj.status == 'Rejected':
            return "-"
        url = reverse("admin:vendorquotation_approve", args=[obj.pk])
        return format_html('<a class="button" href="{}" style="color:green;">Approve</a>', url)

    approve_button.short_description = "Approve"

    def reject_button(self, obj):
        if obj.status == 'Rejected':
            return "❌ Rejected"
        elif obj.status == 'Approved':
            return "-"
        url = reverse("admin:vendorquotation_reject", args=[obj.pk])
        return format_html('<a class="button" href="{}" style="color:red;">Reject</a>', url)

    reject_button.short_description = "Reject"


    def approve_quotation(self, request, pk):
        try:
            quotation = VendorBid.objects.get(pk=pk)
            rfq = quotation.rfq
            vendor = quotation.vendor

            # Reject all other quotations for this RFQ item
            VendorBid.objects.filter(rfq=rfq,vendor=vendor).exclude(pk=quotation.pk).update(status='Rejected')

            # Approve this one
            quotation.status = 'Approved'
            quotation.save()

            self.message_user(request, "Vendor quotation approved. Others rejected.", level=messages.SUCCESS)
        except VendorBid.DoesNotExist:
            self.message_user(request, "VendorQuotation not found.", level=messages.ERROR)

        return redirect("../")
    
    def reject_quotation(self, request, pk):
        try:
            quotation = VendorBid.objects.get(pk=pk)
            quotation.status = 'Rejected'
            quotation.save()

            self.message_user(request, "Vendor quotation rejected.", level=messages.SUCCESS)
        except VendorBid.DoesNotExist:
            self.message_user(request, "Vendor quotation not found.", level=messages.ERROR)

        return redirect("../")

# admin.site.register(VendorBid,VendorBidAdmin)

@admin.register(VendorQuotation)
class VendorQuotationAdmin(admin.ModelAdmin):
    list_display = ('get_vendor', 'rfq_item', 'quoted_price', 'lead_time_days', 'get_submitted_at')
    change_list_template = "admin/vendorquotation_change_list.html"



    def get_vendor(self, obj):
        if obj.vendor_bid and obj.vendor_bid.vendor:
            return obj.vendor_bid.vendor.name  # or however you want to display the vendor
        return "-"

    def get_submitted_at(self, obj):
        if obj.vendor_bid and obj.vendor_bid.submitted_at:
            return obj.vendor_bid.submitted_at
        return "-"

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "upload-csv/",
                self.admin_site.admin_view(self.upload_csv),
                name="vendorquotation_upload_csv",  # important!
            ),
        ]
        return custom_urls + urls

    def upload_csv(self, request):
        if request.method == "POST":
            form = VendorQuotationUploadForm(request.POST, request.FILES)
            if form.is_valid():
                data = form.cleaned_data['csv_file'].read().decode('utf-8')
                io_string = io.StringIO(data)
                reader = csv.DictReader(io_string)

                unmatched_rows = []  # For rows with SKUs not found

                for row in reader:
                    try:
                        purchase_request_number = row.get('purchase_request_number')
                        sku = row.get('sku')
                        vendor_id = row.get('vendor_id')
                        quoted_price = row.get('quoted_price')
                        lead_time_days = row.get('lead_time_days')
                        remarks = row   .get('remarks', '')

                        # Validate PurchaseRequest
                        try:
                            pr = PurchaseRequest.objects.get(request_number=purchase_request_number)
                        except PurchaseRequest.DoesNotExist:
                            unmatched_rows.append({**row, 'error': 'PurchaseRequest not found'})
                            continue

                        # Validate SKU in RequestItem via EducationalProduct
                        try:
                            request_item = RequestItem.objects.get(
                                purchase_request=pr,
                                product__sku=sku
                            )
                        except RequestItem.DoesNotExist:
                            unmatched_rows.append({**row, 'error': 'SKU not found in RequestItem'})
                            continue

                        # Get or create RFQ
                        rfq, _ = RFQ.objects.get_or_create(
                            purchase_request=pr,
                            defaults={'created_by': request.user}
                        )

                        # Create or get RFQItem
                        rfq_item, _ = RFQItem.objects.get_or_create(
                        rfq=rfq,
                        request_item=request_item
                        )

                        # # Validate Vendor
                        vendor = Vendor.objects.get(id=vendor_id)

                        # Get VendorBid for this vendor and RFQ
                        vendor_bid, _ = VendorBid.objects.get_or_create(
                            rfq=rfq,
                            vendor=vendor,
                            defaults={'status': 'Pending'}
                        )

                        # Create VendorQuotation
                        VendorQuotation.objects.update_or_create(
                            rfq_item=rfq_item,
                            vendor_bid=vendor_bid,
                            defaults={
                                'quoted_price': quoted_price,
                                'lead_time_days': lead_time_days,
                                'remarks': remarks,
                            }
                        )

                    except Exception as e:
                        unmatched_rows.append({**row, 'error': str(e)})

                # If errors occurred, generate Excel file
                if unmatched_rows:
                    response = HttpResponse(
                        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                    )
                    response['Content-Disposition'] = 'attachment; filename=not_found_skus.xlsx'

                    wb = openpyxl.Workbook()
                    ws = wb.active
                    ws.title = "Unmatched Rows"

                    headers = list(unmatched_rows[0].keys())
                    ws.append(headers)

                    for row in unmatched_rows:
                        ws.append([row.get(col, '') for col in headers])

                    # Autofit column widths
                    for col in ws.columns:
                        max_length = max(len(str(cell.value or "")) for cell in col)
                        ws.column_dimensions[get_column_letter(col[0].column)].width = max_length + 2

                    wb.save(response)
                    return response

                self.message_user(request, "Vendor quotations uploaded successfully.", level=messages.SUCCESS)
                return redirect("..")

        else:
            form = VendorQuotationUploadForm()
            context = {
                'form': form,
                'title': 'Upload Vendor Quotation CSV'
            }
        return render(request, "admin/upload_csv_form.html", context)


