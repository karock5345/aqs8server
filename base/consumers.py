import json
from channels.generic.websocket import AsyncWebsocketConsumer, WebsocketConsumer
from asgiref.sync import async_to_sync
# from models import DisplayAndVoice
from django.db.models import Q
from django.utils import timezone
from .views import  funUTCtoLocal
from .models import Branch, CounterType, DisplayAndVoice
from .api.v_display import wssendwebtv
from .api.serializers import webdisplaylistSerivalizer

class ChatConsumer(AsyncWebsocketConsumer):


    async def connect(self):        
        self.bcode = self.scope['url_route']['kwargs']['bcode']
        self.ct = self.scope['url_route']['kwargs']['ct']
        
        # check bcode and ct (countertype) is not exit do not accept connection
        self.room_group_name = 'webtv_' + self.bcode + '_' + self.ct
        print('connecting:' + self.room_group_name )
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()


    # Receive message from room group
    async def broadcast_message(self, event):
        lastupdate = event['lastupdate']
        ticketlist = event['ticketlist']

        # Send message to WebSocket
        await self.send(text_data=json.dumps({'lastupdate': lastupdate, 'ticketlist':ticketlist}))

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)


        # await wssendwebtv(self.bcode, self.ct)
        # 
        # 
        # 
        # # self.chat_message(self)
        
        # lastupdate=json.dumps({
        #     'type':'lastupdate',
        #     'last':'testing'
        # })
        # self.send(lastupdate)
        
        

    # def chat_message(self):
    #     # message = event['coin_list']

    #     datetime_now =timezone.now()
    #     datetime_now_local = funUTCtoLocal(datetime_now, branch.timezone)
    #     lastupdate=json.dumps({
    #         'lastupdate':datetime_now_local.strftime('%Y-%m-%d %H:%M:%S')
    #     })
      
    #     output = lastupdate
    #     self.send(output)

    


    # def send_webtv(self, event):
    #     # data = json.loads(event.get('value'))
    #     # jdata = json.dumps(data)

    #     # self.send(jdata)
        
    #     data = json.loads(event.get('value'))
    #     bcode =data.get('bcode')
    #     countername =data.get('countertype')

    #     # bcode = 'KB'
    #     # countername = 'Reception'
    #     branch = None
    #     branchobj = Branch.objects.filter( Q(bcode=bcode) )
    #     if branchobj.count() == 1:
    #         branch = branchobj[0]   

    #     countertype = None
    #     # get the Counter type
    #     ctypeobj = CounterType.objects.filter( Q(branch=branch) & Q(name=countername) )
    #     if (ctypeobj.count() > 0) :
    #         countertype = ctypeobj[0]
        
    #     if branch != None and countertype != None :
    #         displaylist = DisplayAndVoice.objects.filter (branch=branch, countertype=countertype).order_by('-displaytime')[:5]
    #         # serializers  = webdisplaylistSerivalizer(displaylist, many=True)
    #         # context = dict({'ticketlist':serializers.data})

    #         datetime_now =timezone.now()
    #         datetime_now_local = funUTCtoLocal(datetime_now, branch.timezone)

    #         context = {
    #         'lastupdate':datetime_now_local.strftime('%Y-%m-%d %H:%M:%S'),
    #         'ticketlist':displaylist,
    #         }

    #         output = json.dumps(context)

    #         self.send(output)
            






