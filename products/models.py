from django.db import models

# Create your models here.
class EducationalProduct(models.Model):
    SEGMENT_CHOICES = (
        ('ois','OIS'),
        ('b2b','B2B')
    )
    YEAR_CHOICES = (
        ('23-24','AY 23-24'),
        ('24-25','AY 24-25'),
        ('25-26','AY 25-26'),
        ('26-27','AY 26-27'),
    )
    CATEGORY_CHOICES = (
        ('book', 'Book'),
        ('kit', 'Kit'),
        ('accessory', 'Accessory'),
    )
    SUBCATEGORY_CHOICES = (
        ('textbook', 'TextBook'),
        ('workbook', 'WorkBook'),
        ('notebook', 'NoteBook'),
        ('languagebook', 'LanguageBook'),
        ('dibbook', 'DIBBook'),
    )
    UNIT_CHOICES = [
    ('pcs', 'Piece'),
    ('kg', 'Kilograms'),
    ('ltr', 'Liters'),
    ('box', 'Box'),
    ('pack', 'Pack'),
]
    segment = models.CharField(max_length=100, choices=SEGMENT_CHOICES)
    year = models.CharField(max_length=50,choices=YEAR_CHOICES)
    category = models.CharField(max_length=100, choices=CATEGORY_CHOICES)
    sub_category = models.CharField(max_length=100, choices=SUBCATEGORY_CHOICES)
    grade = models.CharField(max_length=50)
    sku = models.CharField(max_length=50, unique=True)
    product_description = models.CharField(max_length=100)
    unit = models.CharField(max_length=20, choices=UNIT_CHOICES)
    volume = models.CharField(max_length=100)
    publisher = models.CharField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.product_description