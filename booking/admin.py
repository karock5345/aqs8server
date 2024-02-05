from django.contrib import admin
from .models import TimeSlot, Booking, BookingLog

# Register your models here.
class TimeSlotView(admin.ModelAdmin):
    list_display =('branch', 'start_date', 'slot_using', 'slot_available', 'slot_total', 'enabled')
    ordering = ('branch', 'start_date',)

class BookingView(admin.ModelAdmin):
    list_display =('timeslot', 'user', 'member', 'status', 'name', 'email', 'mobilephone', 'remark', 'created')
    ordering = ('-updated', '-created')

class BookingLogView(admin.ModelAdmin):
    list_display =('created', 'timeslot', 'booking', 'user', 'member', 'action', 'logtext', )
    ordering = ('booking', '-created')

admin.site.register(TimeSlot, TimeSlotView)
admin.site.register(Booking, BookingView)
admin.site.register(BookingLog, BookingLogView)