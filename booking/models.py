from django.db import models
from django.contrib.auth.models import User
from base.models import Branch
from crm.models import Member
from datetime import timedelta
from django.utils.html import format_html, escape
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _

# Create your models here.


# status : pending (new) -> confirmed : confirmed by admin -> completed : completed by admin
#                                                          -> late : late by customer
#                                                          -> noshow : customer no show
#                        -> rejected : rejected by admin
#                        -> cancelled : cancelled by customer

    
    
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
    class STATUS(models.TextChoices):
        PENDING = 'pending', _('Pending (new booking)')
        CONFIRMED = 'confirmed', _('Confirmed')
        COMPLETED = 'completed', _('Completed')
        LATE = 'late', _('Late')
        NOSHOW = 'noshow', _('Customer No show')
        REJECTED = 'rejected', _('Rejected by Admin')
        CANCELLED = 'cancelled', _('Cancelled by Customer')



    timeslot = models.ForeignKey(TimeSlot, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    member = models.ForeignKey(Member, on_delete=models.SET_NULL, null=True, blank=True)

    # status : pending (new) -> confirmed : confirmed by admin -> completed : completed by admin
    #                                                          -> late : late by customer
    #                                                          -> noshow : customer no show
    #                        -> rejected : rejected by admin
    #                        -> cancelled : cancelled by customer
    status = models.CharField(max_length=100, choices=STATUS.choices, default=STATUS.PENDING)
    name = models.CharField(max_length=100, default='')
    email = models.EmailField(null=True, blank=True, default='')
    mobilephone_country = models.CharField(max_length=200, null=True, blank=True, default='')
    mobilephone = models.CharField(max_length=200, null=True, blank=True, default='')
    people = models.IntegerField(default=1)
    remark = models.TextField(max_length=500, null=True, blank=True, default='')

    updated = models.DateTimeField(auto_now=True)
    created = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return self.name
    
class BookingLog(models.Model):
# BookingLog -> action : new, change, cancel, confirm, reject, noshow, complete
    class ACTION(models.TextChoices):
        NEW = 'new', _('New')
        CHANGE = 'change', _('Change')
        CANCEL = 'cancel', _('Cancel')
        CONFIRM = 'confirm', _('Confirm')
        REJECT = 'reject', _('Reject')
        NOSHOW = 'noshow', _('No show')
        COMPLETE = 'complete', _('Completed')
        DELETE = 'delete', _('Delete')


    timeslot = models.ForeignKey(TimeSlot, on_delete=models.SET_NULL, null=True, blank=True)
    booking = models.ForeignKey(Booking, on_delete=models.SET_NULL, null=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    member = models.ForeignKey(Member, on_delete=models.SET_NULL, null=True, blank=True)
    logtext = models.TextField(max_length=200, null=True, blank=True)

    action = models.CharField(max_length=100, choices=ACTION.choices, default=ACTION.NEW, ) 
    remark = models.TextField(max_length=200, null=True, blank=True)

    created = models.DateTimeField(auto_now_add=True)
