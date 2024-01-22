from django.contrib import admin
from .models import TimeSlot, Booking

# Register your models here.
class TimeSlotView(admin.ModelAdmin):
    list_display =('branch', 'booking_date', 'status', 'enabled')
    ordering = ('branch', 'booking_date',)

class BookingView(admin.ModelAdmin):
    list_display =('timeslot', 'user', 'member', 'status', 'name', 'email', 'mobilephone', 'remark', 'created')
    ordering = ('-updated', '-created')

admin.site.register(TimeSlot, TimeSlotView)
admin.site.register(Booking, BookingView)