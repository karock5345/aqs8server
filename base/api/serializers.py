from rest_framework.serializers import ModelSerializer
from rest_framework import serializers
from base.models import Branch, DisplayAndVoice, PrinterStatus, Ticket, TicketRoute, TicketTemp
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
    # bcode = serializers.CharField(source='branch.bcode')
    # localt = serializers.DateTimeField(source='tickettime')
    # tickettime_local = funUTCtoLocal(localt,'Asia/HongKong')
    # tickettime_local = tickettime_local.strftime('%Y-%m-%d %H:%M:%S')
    class Meta:
        model = TicketTemp
        fields = ('tickettype', 'ticketnumber', 'tickettime', 'id')
        
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
        fields = ('printernumber', 'statustext', 'status')

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




