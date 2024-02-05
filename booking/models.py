from django.db import models
from django.contrib.auth.models import User
from base.models import Branch
from crm.models import Member
from datetime import timedelta
from django.utils.html import format_html, escape
from django.utils.safestring import mark_safe

# Create your models here.
# BookingLog -> action : new, change, cancel, confirm, reject, noshow, complete
A_NEW = 'new'
A_CHANGE = 'change'
A_CANCEL = 'cancel'
A_CONFIRM = 'confirm'
A_REJECT = 'reject'
A_NOSHOW = 'noshow'
A_COMPLETE = 'complete'
A_DELETE = 'delete'
ACTION = [
    (A_NEW, ('New')),
    (A_CHANGE, ('Change')),
    (A_CANCEL, ('Cancel')),
    (A_CONFIRM, ('Confirm')),
    (A_REJECT, ('Reject')),
    (A_NOSHOW, ('No show')),
    (A_COMPLETE, ('Completed')),
    (A_DELETE, ('Delete')),
]


# datetime_now_local = funUTCtoLocal(datetime_now, cs.countertype.branch.timezone)

class TimeSlot(models.Model):
    # TimeSlot if branch is deleted, timeslot should be deleted
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, null=False, blank=False)    
    # |show_date---show_end_date|---start_date---| 
    # show_date should be < show_end_date < start_date    
    start_date = models.DateTimeField(null=False, blank=False  )
    end_date = models.DateTimeField( null=False, blank=False )
    enabled = models.BooleanField(default=True)

    slot_total = models.IntegerField(default=1)
    slot_available = models.IntegerField(default=1)
    slot_using = models.IntegerField(default=0)
    show_date = models.DateTimeField( null=False, blank=False)
    show_end_date = models.DateTimeField(null=False, blank=False)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_by_temp = models.BooleanField(default=False)
    
    updated = models.DateTimeField(auto_now=True)
    created = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return self.branch.bcode + ' ' + self.start_date.strftime('%Y-%m-%d_%H:%M')

class Booking(models.Model):
    timeslot = models.ForeignKey(TimeSlot, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    member = models.ForeignKey(Member, on_delete=models.SET_NULL, null=True, blank=True)

    status = models.CharField(max_length=100, default='pending')
    name = models.CharField(max_length=100)
    email = models.EmailField(null=True, blank=True)
    mobilephone_country = models.CharField(max_length=200, null=True, blank=True)
    mobilephone = models.CharField(max_length=200, null=True, blank=True)
    people = models.IntegerField(default=1)
    remark = models.TextField(max_length=200, null=True, blank=True)

    updated = models.DateTimeField(auto_now=True)
    created = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return self.name
    
class BookingLog(models.Model):
    timeslot = models.ForeignKey(TimeSlot, on_delete=models.SET_NULL, null=True, blank=True)
    booking = models.ForeignKey(Booking, on_delete=models.SET_NULL, null=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    member = models.ForeignKey(Member, on_delete=models.SET_NULL, null=True, blank=True)
    logtext = models.TextField(max_length=200, null=True, blank=True)

    action = models.CharField(max_length=100, default=A_NEW, choices=ACTION,) # new, change, cancel, confirm, reject, complete
    remark = models.TextField(max_length=200, null=True, blank=True)

    created = models.DateTimeField(auto_now_add=True)
