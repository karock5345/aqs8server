from rest_framework.serializers import ModelSerializer
from rest_framework import serializers
from base.models import Branch, DisplayAndVoice, PrinterStatus, TicketFormat, TicketRoute, TicketTemp
from booking.models import TimeSlot
from base.api.views import funUTCtoLocal


class tsSerializer(ModelSerializer):
    
    date = serializers.SerializerMethodField()
    time = serializers.SerializerMethodField()
    week = serializers.SerializerMethodField()

    class Meta:
        model = TimeSlot
        fields = ('id', 'date', 'time', 'week')
    def get_date(self, obj):
        start_date = obj.start_date
        start_date = funUTCtoLocal(start_date, obj.branch.timezone)
        date_str = start_date.strftime('%Y-%m-%d')
        return date_str
    def get_time(self, obj):
        start_date = obj.start_date
        start_date = funUTCtoLocal(start_date, obj.branch.timezone)
        time_str = start_date.strftime('%I:%M %p')
        return time_str
    def get_week(self, obj,):
        from booking.views import funWeekStr
        start_date = obj.start_date
        start_date = funUTCtoLocal(start_date, obj.branch.timezone)
        out = funWeekStr(start_date)
        return out
        
