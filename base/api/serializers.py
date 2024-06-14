from rest_framework.serializers import ModelSerializer
from rest_framework import serializers
from base.models import Branch, DisplayAndVoice, PrinterStatus, TicketFormat, TicketRoute, TicketTemp
import pytz


# from base.api.views import funUTCtoLocal
# from django.contrib.auth.models import User

# class webdisplaylistSerivalizer(ModelSerializer):
#     tickettype = serializers.CharField(source='tickettemp.tickettype')
#     ticketnumber = serializers.CharField(source='tickettemp.ticketnumber')
#     ct_lang1 = serializers.CharField(source='countertype.lang1')
#     ct_lang2 = serializers.CharField(source='countertype.lang2')
#     ct_lang3 = serializers.CharField(source='countertype.lang3')
#     ct_lang4 = serializers.CharField(source='countertype.lang4')
#     wait = serializers.CharField(source='tickettemp.ticketroute.waiting')
#     t_lang1 = serializers.CharField(source='tickettemp.ticketformat.touchkey_lang1')
#     t_lang2 = serializers.CharField(source='tickettemp.ticketformat.touchkey_lang2')
#     t_lang3 = serializers.CharField(source='tickettemp.ticketformat.touchkey_lang3')
#     t_lang4 = serializers.CharField(source='tickettemp.ticketformat.touchkey_lang4')
#     class Meta:
#         model = DisplayAndVoice
#         fields = ('tickettype', 'ticketnumber', 'ct_lang1', 'ct_lang2', 'ct_lang3', 'ct_lang4', 'counternumber', 'wait', 't_lang1', 't_lang2', 't_lang3', 't_lang4',)


class waitinglistSerivalizer(ModelSerializer):
    

    # create new field is_booking
    booking_time_local = serializers.SerializerMethodField()
    late_min = serializers.SerializerMethodField()
    disp_tt = serializers.SerializerMethodField()
    disp_tno = serializers.SerializerMethodField()

    class Meta:
        model = TicketTemp
        fields = ('disp_tt', 'disp_tno', 'tickettype', 'ticketnumber', 'tickettime', 'id', 'booking_id', 'booking_name', 'booking_time', 'booking_time_local', 'booking_tickettype', 'booking_ticketnumber', 'late_min')
    def get_disp_tno(self, obj):
        from base.api.v_touch import funGetTicketNumber
        if obj.branch is None:
            out = None
        else:
            temp , out = funGetTicketNumber(obj)
        return out
    def get_disp_tt(self, obj):
        from base.api.v_touch import funGetTicketNumber
        if obj.branch is None:
            out = None
        else:
            out , temp = funGetTicketNumber(obj)
        return out    
    def get_booking_time_local(self, obj):
        date_str = None
        bdate = obj.booking_time
        if bdate is not None:             
            local_tz = pytz.timezone(obj.branch.timezone)
            local_datetime = bdate.replace(tzinfo=pytz.utc).astimezone(local_tz)
            date_str = local_datetime.strftime('%H:%M %Y-%m-%d')
        return date_str
    def get_late_min(self, obj):
        from booking.models import Booking
        if obj.booking_id is None:
            out = None        
        else:
            booking = Booking.objects.get(id=obj.booking_id)
            out = booking.late_min
        return out
        
class branchSerivalizer(ModelSerializer):
    class Meta:
        model = Branch
        fields = '__all__'

      
class ticketlistSerivalizer(ModelSerializer):
    bcode = serializers.CharField(source='branch.bcode')

    class Meta:
        model = TicketTemp
        fields = ('tickettype', 'ticketnumber', 'bcode', 'tickettime' , 'tickettext', 'printernumber')

class rocheticketlistSerivalizer(ModelSerializer):
    # bcode = serializers.CharField(source='branch.bcode')

    class Meta:
        model = TicketTemp
        fields = ('tickettype', 'ticketnumber', 'tickettime')

class printerstatusSerivalizer(ModelSerializer):
    # bcode = serializers.CharField(source='branch.bcode')

    class Meta:
        model = PrinterStatus
        fields = ('id', 'printernumber', 'statustext', 'status')

class displaylistSerivalizer(ModelSerializer):
    # bcode = serializers.CharField(source='branch.bcode')
    # countertype = serializers.CharField(source='countertype.name')
    tickettype = serializers.CharField(source='tickettemp.tickettype')
    ticketnumber = serializers.CharField(source='tickettemp.ticketnumber')
    tickettime = serializers.DateTimeField(source='tickettemp.tickettime')
    ct_lang1 = serializers.CharField(source='countertype.lang1')
    ct_lang2 = serializers.CharField(source='countertype.lang2')
    ct_lang3 = serializers.CharField(source='countertype.lang3')
    ct_lang4 = serializers.CharField(source='countertype.lang4')
    wait = serializers.CharField(source='tickettemp.ticketroute.waiting')
    t_lang1 = serializers.CharField(source='tickettemp.ticketformat.touchkey_lang1')
    t_lang2 = serializers.CharField(source='tickettemp.ticketformat.touchkey_lang2')
    t_lang3 = serializers.CharField(source='tickettemp.ticketformat.touchkey_lang3')
    t_lang4 = serializers.CharField(source='tickettemp.ticketformat.touchkey_lang4')

    class Meta:
        model = DisplayAndVoice
        fields = ('tickettype', 'ticketnumber',  'tickettime', 'displaytime', 'counternumber', 'wait', 'flashtime', 'ct_lang1', 'ct_lang2', 'ct_lang3', 'ct_lang4', 't_lang1', 't_lang2', 't_lang3', 't_lang4',)



class displaywaitlistSerivalizer(ModelSerializer):
    bcode = serializers.CharField(source='branch.bcode')
    countertype = serializers.CharField(source='countertype.name')
    
    class Meta:
        model = TicketRoute
        fields = ('bcode', 'countertype', 'tickettype', 'waiting',)

class voicelistSerivalizer(ModelSerializer):
    bcode = serializers.CharField(source='branch.bcode')
    countertype = serializers.CharField(source='countertype.name')
    tickettype = serializers.CharField(source='tickettemp.tickettype')
    ticketnumber = serializers.CharField(source='tickettemp.ticketnumber')
    tickettime = serializers.DateTimeField(source='tickettemp.tickettime')
    
    class Meta:
        model = DisplayAndVoice
        fields = ('bcode', 'countertype', 'tickettype', 'ticketnumber',  'tickettime', 'displaytime', 'counternumber')



class lastDisplaySerivalizer(ModelSerializer):
    bcode = serializers.CharField(source='branch.bcode')
    countertype = serializers.CharField(source='countertype.name')
    
    class Meta:
        model = TicketRoute
        fields = ('bcode', 'countertype', 'displasttickettype', 'displastticketnumber', 'displastcounter', 'waiting',)

class touchkeysSerivalizer(ModelSerializer):
    # bcode = serializers.CharField(source='branch.bcode')
    tickettype = serializers.CharField(source='ttype')
    class Meta:
        model = TicketFormat
        fields = ('tickettype', 'touchkey_lang1', 'touchkey_lang2', 'touchkey_lang3', 'touchkey_lang4')

# # User Serializer
# class UserSerializer(ModelSerializer):
#     class Meta:
#         model = User
#         fields = ('id', 'username', 'email')

# # Register Serializer
# class RegisterSerializer(ModelSerializer):
#     class Meta:
#         model = User
#         fields = ('id', 'username', 'email', 'password')
#         extra_kwargs = {'password': {'write_only': True}}

#     def create(self, validated_data):
#         user = User.objects.create_user(validated_data['username'], validated_data['email'], validated_data['password'])

#         return user        




