# Generated by Django 5.2 on 2025-07-09 07:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0003_alter_educationalproduct_segment_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='educationalproduct',
            name='category',
            field=models.CharField(choices=[('book', 'Book'), ('bookbundle', 'Book Bundle'), ('kit', 'Kit'), ('accessory', 'Accessory')], max_length=100),
        ),
        migrations.AlterField(
            model_name='educationalproduct',
            name='sub_category',
            field=models.CharField(choices=[('textbook', 'TextBook'), ('workbook', 'WorkBook'), ('compositebooks', 'Composite Books'), ('notebook', 'NoteBook'), ('languagebook', 'LanguageBook'), ('dibbook', 'DIBBook'), ('studentplanner', 'StudentPlanner'), ('crayons', 'Crayons')], max_length=100),
        ),
    ]
