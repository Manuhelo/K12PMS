import csv
from datetime import datetime
from django.shortcuts import render, redirect
from django.contrib import messages
from .models import StudentOrder
from inventory.models import Warehouse, GoodsReceiptItem
from products.models import EducationalProduct
from django.db.models import Sum



def upload_student_orders(request):
    if request.method == 'POST' and request.FILES.get('csv_file'):
        file = request.FILES['csv_file']
        decoded_file = file.read().decode('utf-8').splitlines()
        reader = csv.DictReader(decoded_file)

        created = 0
        skipped = 0

        for row in reader:
            try:
                warehouse = Warehouse.objects.get(name=row['Branch Name'].strip())
                sku = EducationalProduct.objects.get(sku=row['SKU Code'].strip())

                obj, created_flag = StudentOrder.objects.get_or_create(
                    academic_year=row['Academic Year'].strip(),
                    warehouse=warehouse,
                    enrollment_code=row['Enrollment Code'].strip(),
                    sku=sku,
                    defaults={
                        'student_name': row['Student Name'].strip(),
                        'gender': row['Gender'].strip(),
                        'student_class': row['Class'].strip(),
                        'quantity': int(row['Quantity']),
                        'paid_date': datetime.strptime(row['Paid Date'], '%Y-%m-%d').date(),
                    }
                )
                if created_flag:
                    created += 1
                else:
                    skipped += 1
            except Exception as e:
                print(f"Error: {e}")
                continue

        messages.success(request, f"Upload complete: {created} created, {skipped} skipped.")
        return redirect('upload_student_orders')

    return render(request, 'orders/upload.html')


# ✅ Dashboard View for Inventory Planning


def order_inventory_dashboard(request):
    # Get filters from request
    selected_year = request.GET.get('year')
    selected_warehouse = request.GET.get('warehouse')
    selected_sku = request.GET.get('sku')

    # Filter orders
    orders = StudentOrder.objects.select_related('sku', 'warehouse')

    if selected_year:
        orders = orders.filter(academic_year=selected_year)
    if selected_warehouse:
        orders = orders.filter(warehouse_id=selected_warehouse)
    if selected_sku:
        orders = orders.filter(sku__sku__icontains=selected_sku)

    # Summary of orders
    summary = orders.values('sku__sku', 'sku__product_description', 'academic_year') \
        .annotate(total_ordered=Sum('quantity'))

    # GRN summary from stock
    stock_summary = GoodsReceiptItem.objects.values('product__sku') \
        .annotate(total_received=Sum('quantity_received'))

    stock_map = {item['product__sku']: item['total_received'] for item in stock_summary}

    # Final report
    dashboard_data = []
    for item in summary:
        sku = item['sku__sku']
        product = item['sku__product_description']
        year = item['academic_year']
        ordered = item['total_ordered']
        received = stock_map.get(sku, 0)
        pending = max(0, ordered - received)

        dashboard_data.append({
            'sku': sku,
            'product': product,
            'academic_year': year,
            'total_ordered': ordered,
            'total_received': received,
            'pending': pending,
            'alert': pending > 0
        })

    # Dropdown options for filters
    years = StudentOrder.objects.values_list('academic_year', flat=True).distinct()
    warehouses = Warehouse.objects.all()

    return render(request, 'orders/dashboard.html', {
        'summary': dashboard_data,
        'orders': orders[:100],  # Optional: show few records above
        'years': years,
        'warehouses': warehouses,
        'selected_year': selected_year,
        'selected_warehouse': selected_warehouse,
        'selected_sku': selected_sku,
        'page_title': 'Inventory Planning Dashboard'
    })
