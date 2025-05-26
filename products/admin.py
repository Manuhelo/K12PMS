import csv
import io
from django.contrib import admin, messages
from django.shortcuts import render, redirect
from django.urls import path
from .forms import EducationalProductUploadForm
from .models import EducationalProduct
# Register your models here.


@admin.register(EducationalProduct)
class EducationalProductAdmin(admin.ModelAdmin):
    list_display = ['sku', 'product_description', 'category', 'sub_category', 'grade','volume']
    search_fields = ['year','sku', 'product_description', 'category', 'sub_category','grade', 'publisher','volume']
    change_list_template = "admin/educational_product_changelist.html"

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('upload-csv/', self.admin_site.admin_view(self.upload_csv), name='upload_educationalproduct_csv'),
        ]
        return custom_urls + urls

    def upload_csv(self, request):
        if request.method == "POST":
            form = EducationalProductUploadForm(request.POST, request.FILES)
            if form.is_valid():
                csv_file = form.cleaned_data['csv_file']
                decoded_file = csv_file.read().decode('utf-8', errors='replace')
                io_string = io.StringIO(decoded_file)
                reader = csv.DictReader(io_string)
                created, updated = 0, 0

                for row in reader:
                    obj, created_flag = EducationalProduct.objects.update_or_create(
                        sku=row['sku'],
                        defaults={
                            'segment': row['segment'],
                            'year': row['year'],
                            'category': row['category'],
                            'sub_category': row['sub_category'],
                            'grade': row['grade'],
                            'product_description': row['product_description'],
                            'unit': row['unit'],
                            'volume': row['volume'],
                            'publisher': row['publisher'],
                        }
                    )
                    if created_flag:
                        created += 1
                    else:
                        updated += 1

                self.message_user(request, f"Upload complete. {created} created, {updated} updated.", level=messages.SUCCESS)
                return redirect("..")
        else:
            form = EducationalProductUploadForm()
        return render(request, "admin/educational_product_upload.html", {"form": form})


# admin.site.register(EducationalProduct)

