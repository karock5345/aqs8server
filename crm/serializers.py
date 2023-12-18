from rest_framework.serializers import ModelSerializer
from rest_framework import serializers
from base.models import Branch, DisplayAndVoice, PrinterStatus, TicketFormat, TicketRoute, TicketTemp
from crm.models import Member, Company, MemberItem


class MemberItemListSerivalizer(ModelSerializer):
    # price = serializers.FloatField(source='price')
    dis_price = serializers.FloatField(source='discount_price')
    mp = serializers.IntegerField(source='member_points')
    
    class Meta:
        model = MemberItem
        fields = ('id', 'name', 'des', 'price' , 'dis_price', 'mp')
