from django.contrib import admin
from .models import TimeSlot, Booking, BookingLog, SMS_Log


# Register your models here.
class TimeSlotView(admin.ModelAdmin):
    list_display =('branch', 'start_date', 'slot_using', 'slot_available', 'slot_total', 'enabled')
    ordering = ('branch', 'start_date',)

class BookingView(admin.ModelAdmin):
    list_display =('timeslot', 'branch', 'user', 'member', 'status', 'name', 'email', 'mobilephone', 'remark', 'created')
    ordering = ('-updated', '-created')

class BookingLogView(admin.ModelAdmin):
    list_display =('logtime', 'branch', 'timeslot', 'booking', 'user', 'member', 'timeslot_action', 'booking_status', 'logtext', )
    ordering = ('booking', '-created')

class SMSLogView(admin.ModelAdmin):
    list_display =('created', 'branch', 'phone', 'sent', 'numSMS', 'msg_for', 'errormsg', )
    ordering = ('-created',)

admin.site.register(TimeSlot, TimeSlotView)
admin.site.register(Booking, BookingView)
admin.site.register(BookingLog, BookingLogView)
admin.site.register(SMS_Log, SMSLogView)