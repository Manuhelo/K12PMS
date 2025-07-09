# views.py
import csv
import openpyxl
from django.http import HttpResponse
from django.shortcuts import render
from .models import EducationalProduct

def product_list_view(request):
    products = EducationalProduct.objects.all()

    # Filters
    selected_segments = request.GET.getlist('segment')
    selected_years = request.GET.getlist('year')
    selected_categories = request.GET.getlist('category')
    selected_subcategories = request.GET.getlist('subcategory')
    selected_grades = request.GET.getlist('grade')
    selected_volumes = request.GET.getlist('volume')

    if selected_segments:
        products = products.filter(segment__in=selected_segments)
    if selected_years:
        products = products.filter(year__in=selected_years)
    if selected_categories:
        products = products.filter(category__in=selected_categories)
    if selected_subcategories:
        products = products.filter(sub_category__in=selected_subcategories)
    if selected_grades:
        products = products.filter(grade__in=selected_grades)
    if selected_volumes:
        products = products.filter(volume__in=selected_volumes)

    segments = sorted(set(EducationalProduct.objects.values_list('segment', flat=True)))
    years = sorted(set(EducationalProduct.objects.values_list('year', flat=True)))
    categories = sorted(set(EducationalProduct.objects.values_list('category', flat=True)))
    subcategories = sorted(set(EducationalProduct.objects.values_list('sub_category', flat=True)))
    grades = sorted(set(EducationalProduct.objects.values_list('grade', flat=True)))
    volumes = sorted(set(EducationalProduct.objects.values_list('volume', flat=True)))

    # Handle CSV and Excel Download
    download = request.GET.get('download')
    if download == 'csv':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="products.csv"'
        writer = csv.writer(response)
        writer.writerow(['SKU', 'Product Description', 'Segment', 'Year', 'Category', 'Subcategory', 'Grade', 'Volume', 'Unit', 'Publisher'])
        for p in products:
            writer.writerow([
                p.sku, p.product_description, p.segment, p.year, p.category,
                p.sub_category, p.grade, p.volume, p.unit, p.publisher
            ])
        return response

    elif download == 'excel':
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Products"
        ws.append(['SKU', 'Product Description', 'Segment', 'Year', 'Category', 'Subcategory', 'Grade', 'Volume', 'Unit', 'Publisher'])
        for p in products:
            ws.append([
                p.sku, p.product_description, p.segment, p.year, p.category,
                p.sub_category, p.grade, p.volume, p.unit, p.publisher
            ])
        response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = 'attachment; filename="products.xlsx"'
        wb.save(response)
        return response

    return render(request, 'products/product_list.html', {
        'products': products,
        'segments': segments,
        'years': years,
        'categories': categories,
        'subcategories': subcategories,
        'grades': grades,
        'volumes': volumes,
        'selected_segments': selected_segments,
        'selected_years': selected_years,
        'selected_categories': selected_categories,
        'selected_subcategories': selected_subcategories,
        'selected_grades': selected_grades,
        'selected_volumes': selected_volumes,
        'page_title': 'Product Master List'
    })



def download_products_csv(request):
    products = EducationalProduct.objects.all()

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="products.csv"'

    writer = csv.writer(response)
    writer.writerow(['SKU', 'Product Description', 'Segment', 'Year', 'Category', 'Grade', 'Unit', 'Publisher'])

    for p in products:
        writer.writerow([
            p.sku, p.product_description, p.segment, p.year, p.category,
            p.grade, p.unit, p.publisher
        ])

    return response


def download_products_excel(request):
    products = EducationalProduct.objects.all()

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Products"

    headers = ['SKU', 'Product Description', 'Segment', 'Year', 'Category', 'Grade', 'Unit', 'Publisher']
    ws.append(headers)

    for p in products:
        ws.append([
            p.sku, p.product_description, p.segment, p.year, p.category,
            p.grade, p.unit, p.publisher
        ])

    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename=products.xlsx'
    wb.save(response)
    return response
