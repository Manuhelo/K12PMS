import csv
from django.core.management.base import BaseCommand
from products.models import EducationalProduct

class Command(BaseCommand):
    help = 'Bulk upload Educational Products from CSV'

    def add_arguments(self, parser):
        parser.add_argument('csv_file', type=str)

    def handle(self, *args, **kwargs):
        file_path = kwargs['csv_file']
        with open(file_path, newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            count = 0
            for row in reader:
                EducationalProduct.objects.update_or_create(
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
                count += 1
            self.stdout.write(self.style.SUCCESS(f'Successfully uploaded {count} products'))
