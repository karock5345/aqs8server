from rest_framework.serializers import ModelSerializer
from rest_framework import serializers
from base.models import Branch, DisplayAndVoice, PrinterStatus, Ticket, TicketRoute, TicketTemp
# from .views import funUTCtoLocal
# from django.contrib.auth.models import User

class webdisplaylistSerivalizer(ModelSerializer):
    tickettype = serializers.CharField(source='tickettemp.tickettype')
    ticketnumber = serializers.CharField(source='tickettemp.ticketnumber')
    lang1 = serializers.CharField(source='countertype.lang1')
    lang2 = serializers.CharField(source='countertype.lang2')
    wait = serializers.CharField(source='tickettemp.ticketroute.waiting')

    class Meta:
        model = DisplayAndVoice
        fields = ('tickettype', 'ticketnumber', 'lang1', 'lang2', 'counternumber', 'wait')


class waitinglistSerivalizer(ModelSerializer):
    bcode = serializers.CharField(source='branch.bcode')
    # localt = serializers.DateTimeField(source='tickettime')
    # localt = funUTCtoLocal(localt)
    class Meta:
        model = TicketTemp
        fields = ('tickettype', 'ticketnumber', 'bcode', 'tickettime')
        
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
        fields = ('printernumber', 'statustext', )

class displaylistSerivalizer(ModelSerializer):
    bcode = serializers.CharField(source='branch.bcode')
    countertype = serializers.CharField(source='countertype.name')
    tickettype = serializers.CharField(source='tickettemp.tickettype')
    ticketnumber = serializers.CharField(source='tickettemp.ticketnumber')
    tickettime = serializers.DateTimeField(source='tickettemp.tickettime')
    
    class Meta:
        model = DisplayAndVoice
        fields = ('bcode', 'countertype', 'tickettype', 'ticketnumber',  'tickettime', 'displaytime', 'counternumber', 'wait', 'flashtime')



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