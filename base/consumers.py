import json
from channels.generic.websocket import WebsocketConsumer
from asgiref.sync import async_to_sync
# from models import DisplayAndVoice
from django.db.models import Q
from django.utils import timezone
from .views import  funUTCtoLocal
from .models import Branch, CounterType, DisplayAndVoice
from .api.v_display import wssendwebtv
from .api.serializers import webdisplaylistSerivalizer

class ChatConsumer(WebsocketConsumer):


    def connect(self):
        self.room_group_name = 'g_webtv'

        async_to_sync(self.channel_layer.group_add)(
            self.room_group_name,
            self.channel_name
        )

        self.accept()
        # self.chat_message(self)

        # lastupdate=json.dumps({
        #     'type':'lastupdate',
        #     'last':'testing'
        # })
        # self.send(lastupdate)
        
        wssendwebtv(None, None)

    # def chat_message(self):
    #     # message = event['coin_list']

    #     datetime_now =timezone.now()
    #     datetime_now_local = funUTCtoLocal(datetime_now, branch.timezone)
    #     lastupdate=json.dumps({
    #         'lastupdate':datetime_now_local.strftime('%Y-%m-%d %H:%M:%S')
    #     })
      
    #     output = lastupdate
    #     self.send(output)

    


    def send_webtv(self, event):
        # data = json.loads(event.get('value'))
        # jdata = json.dumps(data)

        # self.send(jdata)
        
        data = json.loads(event.get('value'))
        bcode =data.get('bcode')
        countername =data.get('countertype')

        # bcode = 'KB'
        # countername = 'Reception'
        branch = None
        branchobj = Branch.objects.filter( Q(bcode=bcode) )
        if branchobj.count() == 1:
            branch = branchobj[0]   

        countertype = None
        # get the Counter type
        ctypeobj = CounterType.objects.filter( Q(branch=branch) & Q(name=countername) )
        if (ctypeobj.count() > 0) :
            countertype = ctypeobj[0]
        
        if branch != None and countertype != None :
            displaylist = DisplayAndVoice.objects.filter (branch=branch, countertype=countertype).order_by('-displaytime')[:5]
            serializers  = webdisplaylistSerivalizer(displaylist, many=True)
            context = dict({'ticketlist':serializers.data})

            datetime_now =timezone.now()
            datetime_now_local = funUTCtoLocal(datetime_now, branch.timezone)
            lastupdate=dict({
                'lastupdate':datetime_now_local.strftime('%Y-%m-%d %H:%M:%S')
            })

            output = lastupdate | context
            output = json.dumps(output)

            self.send(output)
            






