from django.contrib import admin
from .models import TimeSlot, Booking, BookingLog

# Register your models here.
class TimeSlotView(admin.ModelAdmin):
    list_display =('branch', 'booking_date', 'slot_available', 'status', 'enabled')
    ordering = ('branch', 'booking_date',)

class BookingView(admin.ModelAdmin):
    list_display =('timeslot', 'user', 'member', 'status', 'name', 'email', 'mobilephone', 'remark', 'created')
    ordering = ('-updated', '-created')

class BookingLogView(admin.ModelAdmin):
    list_display =('created', 'timeslot', 'booking', 'user', 'member', 'logtext', )
    ordering = ('booking', '-created')

admin.site.register(TimeSlot, TimeSlotView)
admin.site.register(Booking, BookingView)
admin.site.register(BookingLog, BookingLogView)