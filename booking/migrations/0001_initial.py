# Generated by Django 4.2.13 on 2024-06-22 07:42

from django.conf import settings
import django.core.validators
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('crm', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('base', '0016_alter_branch_bookingtoqueuerationormal'),
    ]

    operations = [
        migrations.CreateModel(
            name='Booking',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.CharField(blank=True, choices=[('null', '---'), ('new', 'New booking'), ('confirmed', 'Confirmed'), ('rejected', 'Rejected by Admin'), ('cancelled', 'Cancelled by Customer'), ('arrived', 'Customer Arrived'), ('noshow', 'Customer No show'), ('started', 'Start Service'), ('queue', 'Queue'), ('started_ontime', 'Start Service (force on time)'), ('queue_ontime', 'Queue (force on time)'), ('completed', 'Completed'), ('changed', 'Changed'), ('deleted', 'Deleted')], default='new', max_length=100, null=True, verbose_name='Booking Status')),
                ('name', models.CharField(default='', max_length=100)),
                ('email', models.EmailField(blank=True, default='', max_length=254, null=True)),
                ('mobilephone_country', models.CharField(blank=True, default='', max_length=200, null=True)),
                ('mobilephone', models.CharField(blank=True, default='', max_length=200, null=True)),
                ('people', models.IntegerField(default=1)),
                ('remark', models.TextField(blank=True, default='', max_length=500, null=True)),
                ('arrival_time', models.DateTimeField(blank=True, null=True)),
                ('lated', models.BooleanField(default=False)),
                ('force_ontime', models.BooleanField(default=False)),
                ('late_min', models.IntegerField(default=0)),
                ('booking_score', models.IntegerField(default=0)),
                ('isubtype', models.IntegerField(default=0)),
                ('updated', models.DateTimeField(auto_now=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('branch', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='base.branch')),
                ('member', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='crm.member')),
            ],
        ),
        migrations.CreateModel(
            name='TimeslotTemplate',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('enabled', models.BooleanField(default=True)),
                ('name', models.CharField(default='Template name', max_length=100)),
                ('sunday', models.BooleanField(default=False)),
                ('monday', models.BooleanField(default=True)),
                ('tuesday', models.BooleanField(default=False)),
                ('wednesday', models.BooleanField(default=False)),
                ('thursday', models.BooleanField(default=False)),
                ('friday', models.BooleanField(default=False)),
                ('saturday', models.BooleanField(default=False)),
                ('show_day_before', models.FloatField(default=7, help_text='Show the booking before start_date, 7 means 7 days before')),
                ('show_period', models.FloatField(default=5, help_text='Show the booking period, 5 means 5 days')),
                ('create_before', models.FloatField(default=8, help_text='Create the booking before show_day, e.g. booking:6-30 show_day_before=7 create_before=8, then create booking at 6-15')),
                ('branch', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='base.branch')),
                ('user', models.ForeignKey(blank=True, help_text='Service provider', null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='TimeSlot_item',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('index', models.IntegerField(default=0)),
                ('start_time', models.TimeField(default='12:00:00')),
                ('service_hours', models.IntegerField(default=1, validators=[django.core.validators.MaxValueValidator(12), django.core.validators.MinValueValidator(0)])),
                ('service_mins', models.IntegerField(default=0, validators=[django.core.validators.MaxValueValidator(59), django.core.validators.MinValueValidator(0)])),
                ('slot_total', models.IntegerField(default=1)),
                ('updated', models.DateTimeField(auto_now=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('branch', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='base.branch')),
            ],
        ),
        migrations.CreateModel(
            name='TimeSlot',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('start_date', models.DateTimeField()),
                ('end_date', models.DateTimeField()),
                ('enabled', models.BooleanField(default=True)),
                ('slot_total', models.IntegerField(default=1)),
                ('slot_available', models.IntegerField(default=1)),
                ('slot_using', models.IntegerField(default=0)),
                ('show_date', models.DateTimeField()),
                ('show_end_date', models.DateTimeField()),
                ('created_by_temp', models.BooleanField(default=False)),
                ('updated', models.DateTimeField(auto_now=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('branch', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='base.branch')),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='TempLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('year', models.IntegerField(default=0)),
                ('month', models.IntegerField(default=0)),
                ('day', models.IntegerField(default=0)),
                ('hour', models.IntegerField(default=0)),
                ('min', models.IntegerField(default=0)),
                ('second', models.IntegerField(default=0)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('bookingtemplate', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='booking.timeslottemplate')),
                ('item', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='booking.timeslot_item')),
            ],
        ),
        migrations.CreateModel(
            name='SMS_Log',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('phone', models.CharField(blank=True, max_length=20, null=True)),
                ('sent', models.BooleanField(default=False)),
                ('numSMS', models.IntegerField(default=0)),
                ('ref', models.CharField(blank=True, max_length=200, null=True)),
                ('status', models.IntegerField(blank=True, default=django.db.models.deletion.SET_NULL, null=True)),
                ('return_code', models.IntegerField(blank=True, default=django.db.models.deletion.SET_NULL, null=True)),
                ('msg_for', models.CharField(blank=True, max_length=200, null=True)),
                ('errormsg', models.CharField(blank=True, max_length=200, null=True)),
                ('updated', models.DateTimeField(auto_now=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('branch', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='base.branch')),
            ],
        ),
        migrations.CreateModel(
            name='BookingLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('logtime', models.DateTimeField()),
                ('logtext', models.TextField(blank=True, max_length=200, null=True)),
                ('timeslot_action', models.CharField(choices=[('null', '---'), ('new', 'New'), ('change', 'Change'), ('delete', 'Delete')], default='null', max_length=100, verbose_name='Time Slot Action')),
                ('booking_status', models.CharField(choices=[('null', '---'), ('new', 'New booking'), ('confirmed', 'Confirmed'), ('rejected', 'Rejected by Admin'), ('cancelled', 'Cancelled by Customer'), ('arrived', 'Customer Arrived'), ('noshow', 'Customer No show'), ('started', 'Start Service'), ('queue', 'Queue'), ('started_ontime', 'Start Service (force on time)'), ('queue_ontime', 'Queue (force on time)'), ('completed', 'Completed'), ('changed', 'Changed'), ('deleted', 'Deleted')], default='null', max_length=100, verbose_name='Booking Status')),
                ('remark', models.TextField(blank=True, max_length=200, null=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('booking', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='booking.booking')),
                ('branch', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='base.branch')),
                ('member', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='crm.member')),
                ('timeslot', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='booking.timeslot')),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AddField(
            model_name='booking',
            name='timeslot',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='booking.timeslot'),
        ),
        migrations.AddField(
            model_name='booking',
            name='user',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL),
        ),
    ]
