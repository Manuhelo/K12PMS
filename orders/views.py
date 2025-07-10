import csv
import openpyxl
from openpyxl.utils import get_column_letter
from datetime import datetime
from django.shortcuts import render, redirect
from django.contrib import messages
from .models import StudentOrder, OrderSummary, ProcurementThreshold
from inventory.models import Warehouse, InventoryItem
from products.models import EducationalProduct
from django.db.models import Sum
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required


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


def download_student_order_sample(request):
    response = HttpResponse(
        content_type='text/csv',
        headers={'Content-Disposition': 'attachment; filename="student_order_sample.csv"'},
    )

    writer = csv.writer(response)
    # Write headers
    writer.writerow([
        'Academic Year', 'Branch Name', 'Enrollment Code', 'Student Name',
        'Gender', 'Class', 'SKU Code', 'Quantity', 'Paid Date'
    ])

    # Sample data rows
    writer.writerow(['2025-26', 'Hyderabad Branch', 'ENR001', 'John Doe', 'Male', 'Grade 1', '4000001234', '3', '2025-07-01'])
    writer.writerow(['2025-26', 'Hyderabad Branch', 'ENR002', 'Jane Smith', 'Female', 'Grade 2', '4000005678', '2', '2025-07-02'])

    return response

def upload_order_summary(request):
    if request.method == "POST" and request.FILES.get("file"):
        file = request.FILES["file"]
        file_name = file.name.lower()

        rows = []
        errors = []

        # Parse file
        try:
            if file_name.endswith(".csv"):
                decoded_file = file.read().decode('utf-8').splitlines()
                reader = csv.DictReader(decoded_file)
                for row in reader:
                    rows.append(row)

            elif file_name.endswith((".xls", ".xlsx")):
                wb = openpyxl.load_workbook(file)
                sheet = wb.active
                headers = [str(cell.value).strip().lower() for cell in sheet[1]]
                for row in sheet.iter_rows(min_row=2, values_only=True):
                    row_dict = dict(zip(headers, row))
                    rows.append(row_dict)

            else:
                messages.error(request, "Unsupported file format. Use CSV or Excel.")
                return redirect("upload_order_summary")
        except Exception as e:
            messages.error(request, f"Error reading file: {e}")
            return redirect("upload_order_summary")

        uploaded_count = 0

        for row in rows:
            try:
                warehouse_name = row.get("branch name", "").strip()
                grade = row.get("grade", "").strip()
                sku_code = str(row.get("sku code", "")).strip().upper()
                quantity = int(str(row.get("quantity", "0")).replace(",", "").strip())

                warehouse = Warehouse.objects.get(name__iexact=warehouse_name)
                sku = EducationalProduct.objects.get(sku=sku_code)

                summary, created = OrderSummary.objects.get_or_create(
                    warehouse=warehouse,
                    grade=grade,
                    sku=sku,
                    defaults={'total_quantity': quantity}
                )
                if not created:
                    summary.total_quantity = quantity  # Overwrite instead of add
                    summary.save()

                uploaded_count += 1

            except Warehouse.DoesNotExist:
                row["error"] = f"Warehouse '{warehouse_name}' not found"
                errors.append(row)
            except EducationalProduct.DoesNotExist:
                row["error"] = f"SKU '{sku_code}' not found"
                errors.append(row)
            except Exception as e:
                row["error"] = str(e)
                errors.append(row)

        # Handle errors
        if errors:
            wb = openpyxl.Workbook()
            ws = wb.active
            ws.title = "Errors"

            # Write headers
            headers = list(errors[0].keys())
            ws.append(headers)
            for row in errors:
                ws.append([row.get(h, '') for h in headers])

            for col in ws.columns:
                max_len = max(len(str(cell.value or '')) for cell in col)
                ws.column_dimensions[get_column_letter(col[0].column)].width = max_len + 2

            response = HttpResponse(
                content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
            response['Content-Disposition'] = 'attachment; filename=upload_errors.xlsx'
            wb.save(response)
            return response

        messages.success(request, f"{uploaded_count} order summary rows uploaded successfully.")
        return redirect("upload_order_summary")

    return render(request, "orders/upload_order_summary.html")



# ✅ Dashboard View for Inventory Planning


def order_inventory_dashboard(request):
    # Get filters
    selected_warehouse = request.GET.get('warehouse')
    selected_grade = request.GET.get('grade')
    selected_sku = request.GET.get('sku')

    # Get thresholds or default values
    thresholds = ProcurementThreshold.objects.first()
    low = thresholds.low_threshold if thresholds else 75
    medium = thresholds.medium_threshold if thresholds else 85

    # Base queryset from OrderSummary
    summaries = OrderSummary.objects.select_related('warehouse', 'sku')
    if selected_warehouse:
        summaries = summaries.filter(warehouse_id=selected_warehouse)
    if selected_grade:
        summaries = summaries.filter(grade__iexact=selected_grade)
    if selected_sku:
        summaries = summaries.filter(sku__sku__icontains=selected_sku)

    # Map OrderSummary by (warehouse_id, sku_id)
    order_map = {
        (s.warehouse_id, s.sku_id): s
        for s in summaries
    }

    # Inventory queryset
    inventory_qs = InventoryItem.objects.select_related('product', 'warehouse')
    if selected_warehouse:
        inventory_qs = inventory_qs.filter(warehouse_id=selected_warehouse)
    if selected_sku:
        inventory_qs = inventory_qs.filter(product__sku__icontains=selected_sku)

    dashboard_data = []

    # Step 1: Add all inventory rows (even if no orders exist)
    for item in inventory_qs:
        key = (item.warehouse.id, item.product.id)
        order = order_map.get(key)
        orders_received = order.total_quantity if order else 0
        stock_available = item.quantity_in_stock
        shortage = max(0, orders_received - stock_available)

        percent_fulfilled = (stock_available / orders_received * 100) if orders_received else 0

        if percent_fulfilled < low:
            status = "OK"
        elif low <= percent_fulfilled < medium:
            status = "Yet to Procure"
        else:
            status = "Mandatory to Procure"

        dashboard_data.append({
            'warehouse': item.warehouse.name,
            'grade': order.grade if order else '',
            'sku': item.product.sku,
            'product': item.product.product_description,
            'orders_received': orders_received,
            'stock_available': stock_available,
            'shortage': shortage,
            'percent_fulfilled': round(percent_fulfilled, 1),
            'status': status,
            'alert': shortage > 0,
        })

    # Step 2: Add orders with no inventory (i.e., 0 stock cases)
    inventory_keys = {(i.warehouse.id, i.product.id) for i in inventory_qs}
    for key, order in order_map.items():
        if key not in inventory_keys:
            dashboard_data.append({
                'warehouse': order.warehouse.name,
                'grade': order.grade,
                'sku': order.sku.sku,
                'product': order.sku.product_description,
                'orders_received': order.total_quantity,
                'stock_available': 0,
                'shortage': order.total_quantity,
                'percent_fulfilled': 0,
                'status': "OK",
                'alert': True,
            })

    # Filters
    warehouses = Warehouse.objects.all()
    grades = OrderSummary.objects.values_list('grade', flat=True).distinct()
    if not grades.exists():
        grades = StudentOrder.objects.values_list('student_class', flat=True).distinct()

    return render(request, 'orders/dashboard.html', {
        'summary': dashboard_data,
        'warehouses': warehouses,
        'grades': grades,
        'selected_warehouse': selected_warehouse,
        'selected_grade': selected_grade,
        'selected_sku': selected_sku,
        'page_title': 'Inventory Planning Dashboard',
        'thresholds': {
            'low': low,
            'medium': medium
        }
    })



@login_required
def update_thresholds(request):
    threshold = ProcurementThreshold.objects.filter(is_active=True).first()
    if request.method == 'POST':
        ok_threshold = int(request.POST.get('ok_threshold'))
        mandatory_threshold = int(request.POST.get('mandatory_threshold'))

        if threshold:
            threshold.low_threshold = ok_threshold
            threshold.medium_threshold = mandatory_threshold
            threshold.save()
        else:
            ProcurementThreshold.objects.create(
                low_threshold=ok_threshold,
                medium_threshold=mandatory_threshold,
                is_active=True
            )
        messages.success(request, "Thresholds updated successfully.")
        return redirect('order_inventory_dashboard')

    return render(request, 'orders/update_thresholds.html', {
        'threshold': threshold
    })