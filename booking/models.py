from django.db import models
from django.contrib.auth.models import User
from base.models import Branch
from crm.models import Member
from datetime import timedelta
import django.utils.html
from django.utils.html import format_html, escape
from django.utils.safestring import mark_safe

# Create your models here.

class TimeSlot(models.Model):
    # TimeSlot
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE)
    # |show_date---show_end_date|---booking_date---| 
    # show_date should be < show_end_date < booking_date
    booking_date = models.DateTimeField()
    enabled = models.BooleanField(default=True)
    status = models.CharField(max_length=100, default='pending')
    slot_total = models.IntegerField(default=1)
    slot_available = models.IntegerField(default=1)
    show_date = models.DateTimeField()
    show_end_date = models.DateTimeField()
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
   
    def __str__(self):
        return self.branch + ' ' + self.booking_date

class Booking(models.Model):
    timeslot = models.ForeignKey(TimeSlot, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    member = models.ForeignKey(Member, on_delete=models.CASCADE)

    status = models.CharField(max_length=100, default='pending')
    name = models.CharField(max_length=100)
    email = models.EmailField(null=True, blank=True)
    mobilephone_country = models.CharField(max_length=200, null=True, blank=True)
    mobilephone = models.CharField(max_length=200, null=True, blank=True)
    remark = models.TextField(max_length=200, null=True, blank=True)

    updated = models.DateTimeField(auto_now=True)
    created = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return self.name