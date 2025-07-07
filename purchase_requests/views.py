# purchase/views.py
from django.shortcuts import render, redirect, get_object_or_404
from .models import *
from inventory.models import *
from django.contrib.auth.decorators import login_required
from django.contrib import messages
import csv
from io import TextIOWrapper
from django.contrib import messages
from django.http import HttpResponse
from django.forms import modelformset_factory


@login_required
def purchase_request_list(request):
    requests = PurchaseRequest.objects.all().select_related('warehouse', 'requested_by')

    warehouse_id = request.GET.get('warehouse')
    segment = request.GET.get('segment')
    status = request.GET.get('status')

    if warehouse_id:
        requests = requests.filter(warehouse__id=warehouse_id)
    if segment:
        requests = requests.filter(segment=segment)
    if status:
        requests = requests.filter(status=status)

    warehouses = Warehouse.objects.all()
    return render(request, 'purchase_requests/list.html', {
        'requests': requests,
        'warehouses': warehouses,
        'segments': PurchaseRequest.SEGMENT_CHOICES,
        'statuses': PurchaseRequest.STATUS_CHOICES,
        'page_title': 'Purchase Requests'
    })


@login_required
def purchase_request_detail(request, pk):
    pr = get_object_or_404(PurchaseRequest.objects.select_related('warehouse', 'requested_by'), pk=pk)
    items = pr.request_items.select_related('product')
    history = pr.status_history.select_related('changed_by').order_by('-changed_at')
    
    return render(request, 'purchase_requests/purchase_request_detail.html', {
        'request_obj': pr,
        'items': items,
        'history': history,
    })


@login_required
def create_purchase_request(request):
    if request.method == 'POST':
        description = request.POST.get('description')
        segment = request.POST.get('segment')
        warehouse_id = request.POST.get('warehouse')
        try:
            warehouse = Warehouse.objects.get(id=warehouse_id)
        except Warehouse.DoesNotExist:
            messages.error(request, "Invalid warehouse selected.")
            return redirect('create_purchase_request')

        pr = PurchaseRequest.objects.create(
            description=description,
            segment=segment,
            warehouse=warehouse,
            requested_by=request.user,
        )
        messages.success(request, 'Purchase request created.')
        return redirect('purchase_request_list')
    

    # For GET request, pr is not yet created
    pr = None

    warehouses = Warehouse.objects.all()
    products = EducationalProduct.objects.all()

    return render(request, 'purchase_requests/purchase_request_form.html', {
        'warehouses': warehouses,
        'segments': PurchaseRequest.SEGMENT_CHOICES,
        'products': products,
        'request_obj': pr if pr else None,
        'request_items': pr.request_items.all() if pr else [],
    })


@login_required
def update_purchase_request(request, pk):
    pr = get_object_or_404(PurchaseRequest, pk=pk)

    if pr.status != 'Draft':
        messages.warning(request, "Only Draft requests can be edited.")
        return redirect('purchase_request_list')

    RequestItemFormSet = modelformset_factory(RequestItem, fields=('product', 'quantity'), extra=0, can_delete=True)

    if request.method == 'POST':
        pr.description = request.POST.get('description')
        pr.segment = request.POST.get('segment')
        pr.remarks = request.POST.get('remarks')
        warehouse_id = request.POST.get('warehouse')

        try:
            pr.warehouse = Warehouse.objects.get(id=warehouse_id)
        except Warehouse.DoesNotExist:
            messages.error(request, "Invalid warehouse selected.")
            return redirect('update_purchase_request', pk=pk)

        formset = RequestItemFormSet(request.POST, queryset=pr.request_items.all())
        if formset.is_valid():
            pr.save()
            instances = formset.save(commit=False)
            for instance in instances:
                instance.purchase_request = pr
                instance.save()
            for obj in formset.deleted_objects:
                obj.delete()
            messages.success(request, "Purchase request updated successfully.")
            return redirect('purchase_request_list')
        else:
            messages.error(request, "Error in item details. Please correct them.")
    else:
        formset = RequestItemFormSet(queryset=pr.request_items.all())

    return render(request, 'purchase_requests/purchase_request_form.html', {
        'request_obj': pr,
        'warehouses': Warehouse.objects.all(),
        'segments': PurchaseRequest.SEGMENT_CHOICES,
        'products': EducationalProduct.objects.all(),
        'request_items': pr.request_items.all(),
    })


@login_required
def delete_purchase_request(request, pk):
    pr = get_object_or_404(PurchaseRequest, pk=pk)

    # ⛔ Prevent deleting non-draft requests
    if pr.status != 'Draft':
        messages.warning(request, "Only Draft requests can be deleted.")
        return redirect('purchase_request_list')
    

    if request.method == 'POST':
        pr.delete()
        messages.success(request, 'Request deleted.')
        return redirect('purchase_request_list')
    return render(request, 'purchase_requests/confirm_delete.html', {'object': pr})


@login_required
def update_request_status(request, pk):
    pr = get_object_or_404(PurchaseRequest, pk=pk)

    if request.method == 'POST':
        new_status = request.POST.get('new_status')
        if new_status != pr.status:
            pr._changed_by = request.user  # Used in save()
            pr.status = new_status
            pr.save()
            messages.success(request, "Status updated.")
        else:
            messages.info(request, "No status change.")
        return redirect('purchase_request_list')

    return render(request, 'purchase_requests/update_status.html', {
        'request_obj': pr,
        'status_choices': PurchaseRequest.STATUS_CHOICES
    })


@login_required
def add_request_items(request, pk):
    pr = get_object_or_404(PurchaseRequest, pk=pk)
    
    if request.method == 'POST':
        product_ids = request.POST.getlist('product')
        quantities = request.POST.getlist('quantity')

        for product_id, qty in zip(product_ids, quantities):
            product = EducationalProduct.objects.get(id=product_id)
            RequestItem.objects.create(
                purchase_request=pr,
                product=product,
                quantity=qty
            )
        messages.success(request, "Items added.")
        return redirect('purchase_request_list')

    products = EducationalProduct.objects.all()
    return render(request, 'purchase_requests/add_items.html', {
        'request_obj': pr,
        'products': products
    })

    
from django.db import IntegrityError

@login_required
def bulk_upload_purchase_requests_csv(request):
    if request.method == 'POST' and request.FILES.get('file'):
        file = request.FILES['file']
        decoded_file = TextIOWrapper(file, encoding='utf-8')
        reader = csv.DictReader(decoded_file)

        for row in reader:
            try:
                # Parse and get necessary data
                segment = row.get('Segment')
                warehouse_name = row.get('Warehouse')
                description = row.get('Description')
                sku = row.get('SKU')
                quantity = row.get('Quantity')

                # Get warehouse and product
                warehouse = Warehouse.objects.get(name=warehouse_name)
                product = EducationalProduct.objects.get(sku=sku)

                # Generate new unique request
                pr = PurchaseRequest.objects.create(
                    segment=segment,
                    warehouse=warehouse,
                    description=description,
                    requested_by=request.user
                )

                # Save item
                RequestItem.objects.create(
                    purchase_request=pr,
                    product=product,
                    quantity=quantity
                )

            except IntegrityError as e:
                messages.error(request, f"Duplicate request number or data issue: {e}")
                continue
            except Exception as e:
                messages.error(request, f"Error in row {row}: {e}")
                continue

        messages.success(request, "CSV upload complete.")
        return redirect('purchase_request_list')

    return render(request, 'purchase_requests/bulk_upload.html')


@login_required
def download_sample_template(request):
    response = HttpResponse(
        content_type='text/csv',
        headers={'Content-Disposition': 'attachment; filename="sample_purchase_upload.csv"'},
    )

    writer = csv.writer(response)
    writer.writerow(['Segment', 'Warehouse', 'Description', 'SKU', 'Quantity'])
    writer.writerow(['OIS', 'Chennai Central', 'Books for Grade 4', 'EDU-1024', '100'])
    writer.writerow(['B2B', 'Hyderabad South', 'Science Kits', 'EDU-2031', '50'])

    return response



