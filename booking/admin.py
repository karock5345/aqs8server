from django.contrib import admin
from .models import TimeSlot, Booking, BookingLog, SMS_Log, TimeSlot_item, TimeslotTemplate, TempLog


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

class TimeSlot_itemView(admin.ModelAdmin):
    list_display =('branch', 'start_time', 'service_hours', 'service_mins', 'slot_total', 'user', )
    ordering = ('branch', 'start_time',)
class TimeslotTemplateView(admin.ModelAdmin):
    list_display =('branch', 'name', )
    # ordering = ('name')
class TempLogView(admin.ModelAdmin):
    list_display =('bookingtemplate', 'item', 'year', 'month', 'day' )
    ordering = ('-created',)

admin.site.register(TimeSlot, TimeSlotView)
admin.site.register(Booking, BookingView)
admin.site.register(BookingLog, BookingLogView)
admin.site.register(SMS_Log, SMSLogView)
admin.site.register(TimeSlot_item, TimeSlot_itemView)
admin.site.register(TimeslotTemplate, TimeslotTemplateView)
admin.site.register(TempLog, TempLogView)