# Generated by Django 4.2.13 on 2024-07-12 09:21

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0020_testingmodel2_des'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='testingmodel2',
            name='des',
        ),
    ]
