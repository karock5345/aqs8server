from django.db import models
from django.contrib.auth.models import User
from base.models import Branch
from crm.models import Member
from datetime import timedelta
from django.utils.html import format_html, escape
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _
from base.api.views import funUTCtoLocal

# Create your models here.

# Booking status:
# status : New -> confirmed : confirmed by admin -> Arrived -> start : Start Service     -> completed : completed by admin
#                                                           -> late : customer is late   -> completed : completed by admin
#                                                           -> noshow : customer no show
#                                                           -> queue : change to queue   -> queue system status : 1. Queue done, 2. Ticket void, 3. Ticket no show
#              -> rejected : rejected by admin
#              -> cancelled : cancelled by customer

    
    
# datetime_now_local = funUTCtoLocal(datetime_now, cs.countertype.branch.timezone)

class TimeSlot(models.Model):
    # Time slot action : new, change, delete, full, disable, enable
    class ACTION(models.TextChoices):
        # this is for timeslot
        NULL = 'null', _('---')
        NEW = 'new', _('New')
        CHANGED = 'change', _('Change')
        #CANCELLED = 'cancel', _('Cancel')
        #CONFIRMED = 'confirm', _('Confirm')
        #REJECTED = 'reject', _('Reject')
        #NOSHOW = 'noshow', _('No show')
        #COMPLETED = 'complete', _('Completed')
        DELETED = 'delete', _('Delete')    
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
        start_date_local = self.start_date
        start_date_local = funUTCtoLocal(start_date_local, self.branch.timezone)
        return self.branch.bcode + ' ' + start_date_local.strftime('%Y-%m-%d_%H:%M')




class Booking(models.Model):
    class STATUS(models.TextChoices):
        NULL = 'null', _('---')
        NEW = 'new', _('New booking')

        CONFIRMED = 'confirmed', _('Confirmed')
        REJECTED = 'rejected', _('Rejected by Admin')
        CANCELLED = 'cancelled', _('Cancelled by Customer')

        ARRIVED = 'arrived', _('Customer Arrived')
        NOSHOW = 'noshow', _('Customer No show')

        # If arrived on time
        STARTED = 'started', _('Start Service')
        QUEUE = 'queue', _('Queue')
        # If arrived late
        STARTED_ONTIME = 'started_ontime', _('Start Service (force on time)')
        QUEUE_ONTIME = 'queue_ontime', _('Queue (force on time)')

        COMPLETED = 'completed', _('Completed')

        CHANGED = 'changed', _('Changed')
        DELETED = 'deleted', _('Deleted') # this is for booking fake delete

        

    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, null=False, blank=False)
    # branch = models.ForeignKey(Branch, on_delete=models.CASCADE, default=Branch.get_default_pk)
    timeslot = models.ForeignKey(TimeSlot, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    member = models.ForeignKey(Member, on_delete=models.SET_NULL, null=True, blank=True)

    status = models.CharField(max_length=100, choices=STATUS.choices, default=STATUS.NEW, null=True, blank=True, verbose_name='Booking Status')
    name = models.CharField(max_length=100, default='')
    email = models.EmailField(null=True, blank=True, default='')
    mobilephone_country = models.CharField(max_length=200, null=True, blank=True, default='')
    mobilephone = models.CharField(max_length=200, null=True, blank=True, default='')
    people = models.IntegerField(default=1)
    remark = models.TextField(max_length=500, null=True, blank=True, default='')

    updated = models.DateTimeField(auto_now=True)
    created = models.DateTimeField(auto_now_add=True)

    
    

    def __str__(self):
        start_date_local = self.timeslot.start_date
        start_date_local = funUTCtoLocal(start_date_local, self.branch.timezone)
        return self.name + '-' + start_date_local.strftime('%Y-%m-%d_%H:%M')
    
class BookingLog(models.Model):
    logtime = models.DateTimeField()

    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, null=False, blank=False)
    # branch = models.ForeignKey(Branch, on_delete=models.CASCADE, default=Branch.get_default_pk)
    timeslot = models.ForeignKey(TimeSlot, on_delete=models.SET_NULL, null=True, blank=True)
    booking = models.ForeignKey(Booking, on_delete=models.SET_NULL, null=True, blank=True)
    
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    member = models.ForeignKey(Member, on_delete=models.SET_NULL, null=True, blank=True)
    logtext = models.TextField(max_length=200, null=True, blank=True)

    timeslot_action = models.CharField(max_length=100, choices=TimeSlot.ACTION.choices, default=TimeSlot.ACTION.NULL, verbose_name='Time Slot Action')
    booking_status = models.CharField(max_length=100, choices=Booking.STATUS.choices, default=Booking.STATUS.NULL, verbose_name='Booking Status')
    remark = models.TextField(max_length=200, null=True, blank=True)

    created = models.DateTimeField(auto_now_add=True)


class SMS_Log(models.Model):
    branch = models.ForeignKey(Branch, on_delete=models.SET_NULL, blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    sent = models.BooleanField(default=False)
    numSMS = models.IntegerField(default=0)
    ref = models.CharField(max_length=200, blank=True, null=True)
    status = models.IntegerField(default=models.SET_NULL, blank=True, null=True)
    return_code = models.IntegerField(default=models.SET_NULL, blank=True, null=True)
    msg_for = models.CharField(max_length=200, blank=True, null=True)
    errormsg = models.CharField(max_length=200, blank=True, null=True)

    updated = models.DateTimeField(auto_now=True)
    created = models.DateTimeField(auto_now_add=True) # auto_now_add just auto add once (the first created

