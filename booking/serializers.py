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
    def get_week(self, obj):
        start_date = obj.start_date
        start_date = funUTCtoLocal(start_date, obj.branch.timezone)
        iWeek = start_date.strftime('%w')
        week_str = ''
        if iWeek == '0':
            week_str = '星期日 Sun'
        elif iWeek == '1':
            week_str = '星期一 Mon'
        elif iWeek == '2':
            week_str = '星期二 Tue'
        elif iWeek == '3':
            week_str = '星期三 Wed'
        elif iWeek == '4':
            week_str = '星期四 Thu'
        elif iWeek == '5':
            week_str = '星期五 Fri'
        elif iWeek == '6':
            week_str = '星期六 Sat'
        return week_str
