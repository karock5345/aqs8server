# Generated by Django 4.2.13 on 2024-06-19 09:37

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0015_alter_branch_queuepriority_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='branch',
            name='bookingToQueueRatioNormal',
            field=models.IntegerField(default=2, help_text='Normal ratio for booking to queue, Default 3:1', verbose_name='Booking to Queue direction ratio [normal] (1 to 10)'),
        ),
    ]
