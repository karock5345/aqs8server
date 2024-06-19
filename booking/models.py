from django.db import models
from django.contrib.auth.models import User
from base.models import Branch
from crm.models import Member
from datetime import timedelta
from django.utils.html import format_html, escape
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _
from base.api.views import funUTCtoLocal, funUTCtoLocaltime
from django.core.validators import MaxValueValidator, MinValueValidator

# Create your models here.

# Booking status:
# status : New -> confirmed : confirmed by admin -> Arrived -> start : Start Service     -> completed : completed by admin
#                                                           -> queue : change to queue   -> queue system status : 1. Queue done, 2. Ticket void, 3. Ticket no show
#                                                           If arrived not on time (compare with arrived time and timeslot start time)
#                                                           -> start_ontime : Start Service (force on time) -> completed : completed by admin
#                                                           -> queue_ontime : change to queue (force on time) -> (same as above)
#                                                -> noshow : customer no show
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

class TimeSlot_item(models.Model):
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, null=False, blank=False)
    start_time = models.TimeField(null=False, blank=False)
    service_hours = models.IntegerField(
        default=1,
        validators=[MaxValueValidator(12), MinValueValidator(0)]
     )
    service_mins = models.IntegerField(
        default=0,
        validators=[MaxValueValidator(59), MinValueValidator(0)]
     )

    slot_total = models.IntegerField(default=1)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
     
    updated = models.DateTimeField(auto_now=True)
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        start_date_local = self.start_time
        start_date_local = funUTCtoLocaltime(start_date_local, self.branch.timezone)
        return self.branch.bcode + ' ' + start_date_local.strftime('%H:%M')

class BookingTemplate(models.Model):    
    enabled = models.BooleanField(default=True)

    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, null=False, blank=False)
    name = models.CharField(max_length=100, default='Booking Template')

    sunday = models.BooleanField(default=False)
    monday = models.BooleanField(default=True)
    tuesday = models.BooleanField(default=False)
    wednesday = models.BooleanField(default=False)
    thursday = models.BooleanField(default=False)
    friday = models.BooleanField(default=False)
    saturday = models.BooleanField(default=False)

    items = models.ManyToManyField(TimeSlot_item, blank=True)
    # e.g. Timeslot item time is 6-30 1:00 - 2:00, show_day_before=7, show_period=5, create_before=8
    # at 6-15 (30-7-8), auto create the booking, show between 6-23 to 6-28
    show_day_before = models.FloatField(default=7, help_text='Show the booking before start_date, 7 means 7 days before')
    show_period = models.FloatField(default=5, help_text='Show the booking period, 5 means 5 days')
    create_before = models.FloatField(default=8, help_text='Create the booking before show_day, e.g. booking:6-30 show_day_before=7 create_before=8, then create booking at 6-15')

    def __str__(self):
        return self.branch.bcode + '-' + self.name

class TempLog(models.Model):
    bookingtemplate = models.ForeignKey(BookingTemplate, on_delete=models.CASCADE, null=False, blank=False)
    item = models.ForeignKey(TimeSlot_item, on_delete=models.CASCADE, null=False, blank=False)
    year = models.IntegerField(default=0)
    month = models.IntegerField(default=0)
    day = models.IntegerField(default=0)
    created = models.DateTimeField(auto_now_add=True)


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
    # user is special user who are doing this booking
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    member = models.ForeignKey(Member, on_delete=models.SET_NULL, null=True, blank=True)

    status = models.CharField(max_length=100, choices=STATUS.choices, default=STATUS.NEW, null=True, blank=True, verbose_name='Booking Status')
    name = models.CharField(max_length=100, default='')
    email = models.EmailField(null=True, blank=True, default='')
    mobilephone_country = models.CharField(max_length=200, null=True, blank=True, default='')
    mobilephone = models.CharField(max_length=200, null=True, blank=True, default='')
    people = models.IntegerField(default=1)
    remark = models.TextField(max_length=500, null=True, blank=True, default='')

    arrival_time = models.DateTimeField(null=True, blank=True)    
    lated = models.BooleanField(default=False) # if arrived late or early then True
    force_ontime = models.BooleanField(default=False) # True means Branch force change to ontime
    late_min = models.IntegerField(default=0) # in minutes, if + then late, if - then early
    
    booking_score = models.IntegerField(default=0)
    
    isubtype = models.IntegerField(default=0) # for integer sub ticket type

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

