# Generated by Django 4.2.13 on 2024-08-25 14:59

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('crm', '0020_alter_quotation_customer_email'),
    ]

    operations = [
        migrations.AlterField(
            model_name='quotation_item',
            name='product',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='crm.product'),
        ),
    ]
