# Generated by Django 5.2 on 2025-05-22 08:14

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('procurement', '0003_alter_vendorquotation_vendor_vendorbid_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='vendorquotation',
            name='vendor',
        ),
    ]
