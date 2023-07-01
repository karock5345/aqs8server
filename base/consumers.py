import json
from channels.generic.websocket import AsyncWebsocketConsumer, WebsocketConsumer
# from asgiref.sync import async_to_sync
from django.db.models import Q
from django.utils import timezone
from .views import funUTCtoLocal
from .models import Branch, CounterType, TicketTemp, CounterStatus
from asgiref.sync import sync_to_async
import logging
from django.core.serializers.json import DjangoJSONEncoder



logger = logging.getLogger(__name__)



class DispPanelConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        @sync_to_async
        def check_input():
            error = ''
            branch = None
            # branchobj = await sync_to_async(Branch.objects.filter, thread_sensitive=True)( Q(bcode=self.bcode) )
            branchobj = Branch.objects.filter(Q(bcode=self.bcode))

            if branchobj.count() == 1:
                branch = branchobj[0]
                pass
            else :
                error = 'Branch not found.'

            if error == '':
                ctobj = CounterType.objects.filter( Q(branch=branch) & Q(name=self.ct) )
                if ctobj.count() == 1:
                    # ct = ctobj[0]
                    pass
                else :
                    error = 'CounterType not found.'

            return error
                
        error = ''
        self.bcode = self.scope['url_route']['kwargs']['bcode']
        self.ct = self.scope['url_route']['kwargs']['ct']
        self.room_group_name = 'disp_' + self.bcode + '_' + self.ct
        logger.info('connecting:' + self.room_group_name )
        
        # check bcode and ct (countertype) is not exit do not accept connection
        error = await check_input()       

        if error == '':        
            await self.channel_layer.group_add(
                self.room_group_name,
                self.channel_name
            )

            await self.accept()
        else :
            logger.info('Error:' + error )
            

    # Receive message from room group
    async def broadcast_message(self, event):
        str_tx = event['tx']

        # Send message to WebSocket
        try:
            await self.send(text_data=str_tx)
        except:
            # If the channel layer is not available, send the data directly to all WebSocket connections in the group
            for connection in await self.get_all_connections():
                await connection.send_data_fallback(str_tx)
    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)
    async def send_data_fallback(self, data):
        # Send the data directly to the WebSocket connection
        await self.send(json.dumps(data, cls=DjangoJSONEncoder))
    async def get_all_connections(self):
        # Get all WebSocket connections in the group
        group_channels = await self.channel_layer.group_channels(self.room_group_name)
        connections = []
        for channel_name in group_channels:
            connection = self.__class__.for_channel(channel_name)
            connections.append(connection)
        return connections


class FlashLightConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        @sync_to_async
        def check_input():
            error = ''
            branch = None
            # branchobj = await sync_to_async(Branch.objects.filter, thread_sensitive=True)( Q(bcode=self.bcode) )
            branchobj = Branch.objects.filter(Q(bcode=self.bcode))

            if branchobj.count() == 1:
                branch = branchobj[0]
                pass
            else :
                error = 'Branch not found.'

            return error
                
        error = ''
        self.bcode = self.scope['url_route']['kwargs']['bcode']
        # self.ct = self.scope['url_route']['kwargs']['ct']
        self.room_group_name = 'flashlight_' + self.bcode
        logger.info('connecting:' + self.room_group_name )
        
        # check bcode and ct (countertype) is not exit do not accept connection
        error = await check_input()       

        if error == '':          
            await self.channel_layer.group_add(
                self.room_group_name,
                self.channel_name
            )

            await self.accept()
        else :
            logger.info('Error:' + error )
            

    # Receive message from room group
    async def broadcast_message(self, event):
        str_tx = event['tx']

        # Send message to WebSocket
        try:
            await self.send(text_data=str_tx)
        except:
            # If the channel layer is not available, send the data directly to all WebSocket connections in the group
            for connection in await self.get_all_connections():
                await connection.send_data_fallback(str_tx)
    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)
    async def send_data_fallback(self, data):
        # Send the data directly to the WebSocket connection
        await self.send(json.dumps(data, cls=DjangoJSONEncoder))
    async def get_all_connections(self):
        # Get all WebSocket connections in the group
        group_channels = await self.channel_layer.group_channels(self.room_group_name)
        connections = []
        for channel_name in group_channels:
            connection = self.__class__.for_channel(channel_name)
            connections.append(connection)
        return connections


class CounterStatusConsumer(AsyncWebsocketConsumer):
    # ws://127.0.0.1:8000/ws/cs/1/
    async def connect(self):
        @sync_to_async
        def check_input():
            error = ''
            counterstatus = None
            counterstatus = CounterStatus.objects.get(id=pk)
            if counterstatus is None:
                error = 'CounterStatus not found.'
           
            return error
                
        error = ''
        self.pk = self.scope['url_route']['kwargs']['pk']

        pk = int(self.pk)
        

        self.room_group_name = 'cs_' + self.pk
        logger.info('connecting:' + self.room_group_name )
        
        # check bcode and ct (countertype) is not exit do not accept connection
        error = await check_input()       

        if error == '':          
            await self.channel_layer.group_add(
                self.room_group_name,
                self.channel_name
            )
            await self.accept()
        else :
            logger.error('Error:' + error )
            

    # Receive message from room group
    async def broadcast_message(self, event):
        str_tx = event['tx']
        # Send message to WebSocket
        try:
            await self.send(text_data=str_tx)
        except:
            # If the channel layer is not available, send the data directly to all WebSocket connections in the group
            for connection in await self.get_all_connections():
                await connection.send_data_fallback(str_tx)
    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)
    async def send_data_fallback(self, data):
        # Send the data directly to the WebSocket connection
        await self.send(json.dumps(data, cls=DjangoJSONEncoder))
    async def get_all_connections(self):
        # Get all WebSocket connections in the group
        group_channels = await self.channel_layer.group_channels(self.room_group_name)
        connections = []
        for channel_name in group_channels:
            connection = self.__class__.for_channel(channel_name)
            connections.append(connection)
        return connections

class SMSConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        @sync_to_async
        def check_input():
            error = ''
            branch = None
            # branchobj = await sync_to_async(Branch.objects.filter, thread_sensitive=True)( Q(bcode=self.bcode) )
            branchobj = Branch.objects.filter(Q(bcode=self.bcode))

            if branchobj.count() == 1:
                branch = branchobj[0]
                pass
            else :
                error = 'Branch not found.'


            return error
                
        error = ''
        self.bcode = self.scope['url_route']['kwargs']['bcode']
        self.room_group_name = 'sms_' + self.bcode 
        logger.info('connecting:' + self.room_group_name )
        
        # check bcode and ct (countertype) is not exit do not accept connection
        error = await check_input()       

        if error == '':          
            await self.channel_layer.group_add(
                self.room_group_name,
                self.channel_name
            )

            await self.accept()
        else :
            logger.info('Error:' + error )
            

    # Receive message from room group
    async def broadcast_message(self, event):
        str_tx = event['tx']

        # Send message to WebSocket
        try:
            await self.send(text_data=str_tx)
        except:
            # If the channel layer is not available, send the data directly to all WebSocket connections in the group
            for connection in await self.get_all_connections():
                await connection.send_data_fallback(str_tx)
    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)
    async def send_data_fallback(self, data):
        # Send the data directly to the WebSocket connection
        await self.send(json.dumps(data, cls=DjangoJSONEncoder))
    async def get_all_connections(self):
        # Get all WebSocket connections in the group
        group_channels = await self.channel_layer.group_channels(self.room_group_name)
        connections = []
        for channel_name in group_channels:
            connection = self.__class__.for_channel(channel_name)
            connections.append(connection)
        return connections
class VoiceConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        @sync_to_async
        def check_input():
            error = ''
            branch = None
            # branchobj = await sync_to_async(Branch.objects.filter, thread_sensitive=True)( Q(bcode=self.bcode) )
            branchobj = Branch.objects.filter(Q(bcode=self.bcode))

            if branchobj.count() == 1:
                branch = branchobj[0]
                pass
            else :
                error = 'Branch not found.'

            if error == '':
                ctobj = CounterType.objects.filter( Q(branch=branch) & Q(name=self.ct) )
                if ctobj.count() == 1:
                    # ct = ctobj[0]
                    pass
                else :
                    error = 'CounterType not found.'

            return error
                
        error = ''
        self.bcode = self.scope['url_route']['kwargs']['bcode']
        self.ct = self.scope['url_route']['kwargs']['ct']
        self.room_group_name = 'voice_' + self.bcode + '_' + self.ct
        logger.info('connecting:' + self.room_group_name )
        
        # check bcode and ct (countertype) is not exit do not accept connection
        error = await check_input()       

        if error == '':          
            await self.channel_layer.group_add(
                self.room_group_name,
                self.channel_name
            )

            await self.accept()
        else :
            logger.info('Error:' + error )
            

    # Receive message from room group
    async def broadcast_message(self, event):
        str_tx = event['tx']

        # Send message to WebSocket
        try:
            await self.send(text_data=str_tx)
        except:
            # If the channel layer is not available, send the data directly to all WebSocket connections in the group
            for connection in await self.get_all_connections():
                await connection.send_data_fallback(str_tx)
    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)
    async def send_data_fallback(self, data):
        # Send the data directly to the WebSocket connection
        await self.send(json.dumps(data, cls=DjangoJSONEncoder))
    async def get_all_connections(self):
        # Get all WebSocket connections in the group
        group_channels = await self.channel_layer.group_channels(self.room_group_name)
        connections = []
        for channel_name in group_channels:
            connection = self.__class__.for_channel(channel_name)
            connections.append(connection)
        return connections

class TicketStatusConsumer(AsyncWebsocketConsumer):
    # ws://127.0.0.1:8000/ws/tstatus/KB/A/123/sc/
    async def connect(self):
        @sync_to_async
        def check_input():
            error = ''
            branch = None
            branchobj = Branch.objects.filter(Q(bcode=self.bcode))

            if branchobj.count() == 1:
                branch = branchobj[0]
                pass
            else :
                error = 'Branch not found.'
            if error == '':
                # find ticket
                tobj = TicketTemp.objects.filter(Q(branch=branch) & Q(tickettype=self.ttype) & Q(ticketnumber=self.tno) & Q(securitycode=self.sc))
                if tobj.count() == 1 :
                    ticket = tobj[0]
                else:
                    error = 'Ticket not found.'
            return error
                
        error = ''
        self.bcode = self.scope['url_route']['kwargs']['bcode']
        self.ttype = self.scope['url_route']['kwargs']['ttype']
        self.tno = self.scope['url_route']['kwargs']['tno']
        self.sc = self.scope['url_route']['kwargs']['sc']

        self.room_group_name = 'ticketstatus_' + self.bcode + '_' + self.ttype + self.tno + '_' + self.sc
        logger.info('connecting:' + self.room_group_name )
        
        # check bcode and ct (countertype) is not exit do not accept connection
        error = await check_input()       

        if error == '':          
            await self.channel_layer.group_add(
                self.room_group_name,
                self.channel_name
            )
            await self.accept()
        else :
            logger.info('Error:' + error )
            

    # Receive message from room group
    async def broadcast_message(self, event):
        str_tx = event['tx']

        # Send message to WebSocket
        try:
            await self.send(text_data=str_tx)
        except:
            # If the channel layer is not available, send the data directly to all WebSocket connections in the group
            for connection in await self.get_all_connections():
                await connection.send_data_fallback(str_tx)
    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)
    async def send_data_fallback(self, data):
        # Send the data directly to the WebSocket connection
        await self.send(json.dumps(data, cls=DjangoJSONEncoder))
    async def get_all_connections(self):
        # Get all WebSocket connections in the group
        group_channels = await self.channel_layer.group_channels(self.room_group_name)
        connections = []
        for channel_name in group_channels:
            connection = self.__class__.for_channel(channel_name)
            connections.append(connection)
        return connections



class PrintConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        @sync_to_async
        def check_input():
            error = ''
            branch = None
            branchobj = Branch.objects.filter(Q(bcode=self.bcode))

            if branchobj.count() == 1:
                branch = branchobj[0]
                pass
            else :
                error = 'Branch not found.'

            return error
                
        error = ''
        self.bcode = self.scope['url_route']['kwargs']['bcode']
        self.room_group_name = 'print_' + self.bcode 
        logger.info('connecting:' + self.room_group_name)
        
        # check bcode and ct (countertype) is not exit do not accept connection
        error = await check_input()       

        if error == '':          
            await self.channel_layer.group_add(
                self.room_group_name,
                self.channel_name
            )
            await self.accept()
        else :
            logger.info('Error:' + error )
            

    # Receive message from room group
    async def broadcast_message(self, event):
        str_tx = event['tx']

        # Send message to WebSocket
        try:
            await self.send(text_data=str_tx)
        except:
            # If the channel layer is not available, send the data directly to all WebSocket connections in the group
            for connection in await self.get_all_connections():
                await connection.send_data_fallback(str_tx)
    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)
    async def send_data_fallback(self, data):
        # Send the data directly to the WebSocket connection
        await self.send(json.dumps(data, cls=DjangoJSONEncoder))
    async def get_all_connections(self):
        # Get all WebSocket connections in the group
        group_channels = await self.channel_layer.group_channels(self.room_group_name)
        connections = []
        for channel_name in group_channels:
            connection = self.__class__.for_channel(channel_name)
            connections.append(connection)
        return connections
class PrinterStatusConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        @sync_to_async
        def check_input():
            error = ''
            branch = None
            branchobj = Branch.objects.filter(Q(bcode=self.bcode))

            if branchobj.count() == 1:
                branch = branchobj[0]
                pass
            else :
                error = 'Branch not found.'

            return error
                
        error = ''
        self.bcode = self.scope['url_route']['kwargs']['bcode']
        self.room_group_name = 'printerstatus_' + self.bcode 
        logger.info('connecting:' + self.room_group_name )
        
        # check bcode and ct (countertype) is not exit do not accept connection
        error = await check_input()       

        if error == '':          
            await self.channel_layer.group_add(
                self.room_group_name,
                self.channel_name
            )
            await self.accept()

        else :
            logger.info('Error:' + error )
            

    # Receive message from room group
    async def broadcast_message(self, event):
        str_tx = event['tx']

        # Send message to WebSocket
        try:
            await self.send(text_data=str_tx)
        except:
            # If the channel layer is not available, send the data directly to all WebSocket connections in the group
            for connection in await self.get_all_connections():
                await connection.send_data_fallback(str_tx)
    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)
    async def send_data_fallback(self, data):
        # Send the data directly to the WebSocket connection
        await self.send(json.dumps(data, cls=DjangoJSONEncoder))
    async def get_all_connections(self):
        # Get all WebSocket connections in the group
        group_channels = await self.channel_layer.group_channels(self.room_group_name)
        connections = []
        for channel_name in group_channels:
            connection = self.__class__.for_channel(channel_name)
            connections.append(connection)
        return connections


class QLConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        @sync_to_async
        def check_input():
            error = ''
            branch = None
            # branchobj = await sync_to_async(Branch.objects.filter, thread_sensitive=True)( Q(bcode=self.bcode) )
            branchobj = Branch.objects.filter(Q(bcode=self.bcode))

            if branchobj.count() == 1:
                branch = branchobj[0]
                pass
            else :
                error = 'Branch not found.'

            if error == '':
                ctobj = CounterType.objects.filter( Q(branch=branch) & Q(name=self.ct) )
                if ctobj.count() == 1:
                    # ct = ctobj[0]
                    pass
                else :
                    error = 'CounterType not found.'

            return error
                
        error = ''
        self.bcode = self.scope['url_route']['kwargs']['bcode']
        self.ct = self.scope['url_route']['kwargs']['ct']
        self.room_group_name = 'ql_' + self.bcode + '_' + self.ct
        logger.info('connecting:' + self.room_group_name )
        
        # check bcode and ct (countertype) is not exit do not accept connection
        error = await check_input()       

        if error == '':          
            await self.channel_layer.group_add(
                self.room_group_name,
                self.channel_name
            )

            await self.accept()
        else :
            logger.error('Error:' + error )
            

    # Receive message from room group
    async def broadcast_message(self, event):
        str_tx = event['tx']

        # Send message to WebSocket
        try:
            await self.send(text_data=str_tx)
        except:
            # If the channel layer is not available, send the data directly to all WebSocket connections in the group
            for connection in await self.get_all_connections():
                await connection.send_data_fallback(str_tx)
    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)
    async def send_data_fallback(self, data):
        # Send the data directly to the WebSocket connection
        await self.send(json.dumps(data, cls=DjangoJSONEncoder))
    async def get_all_connections(self):
        # Get all WebSocket connections in the group
        group_channels = await self.channel_layer.group_channels(self.room_group_name)
        connections = []
        for channel_name in group_channels:
            connection = self.__class__.for_channel(channel_name)
            connections.append(connection)
        return connections

class WebTVConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        @sync_to_async
        def check_input():
            error = ''
            branch = None
            # branchobj = await sync_to_async(Branch.objects.filter, thread_sensitive=True)( Q(bcode=self.bcode) )
            branchobj = Branch.objects.filter(Q(bcode=self.bcode))

            if branchobj.count() == 1:
                branch = branchobj[0]
                pass
            else :
                error = 'Branch not found.'

            if error == '':
                ctobj = CounterType.objects.filter( Q(branch=branch) & Q(name=self.ct) )
                if ctobj.count() == 1:
                    # ct = ctobj[0]
                    pass
                else :
                    error = 'CounterType not found.'

            return error
                
        error = ''
        self.bcode = self.scope['url_route']['kwargs']['bcode']
        self.ct = self.scope['url_route']['kwargs']['ct']
        self.room_group_name = 'webtv_' + self.bcode + '_' + self.ct
        logger.info('connecting:' + self.room_group_name )
        
        # check bcode and ct (countertype) is not exit do not accept connection
        error = await check_input()       

        if error == '':        
            await self.channel_layer.group_add(
                self.room_group_name,
                self.channel_name
            )

            await self.accept()
        else :
            logger.info('Error:' + error )
            

    # Receive message from room group
    async def broadcast_message(self, event):
        str_tx = event['tx']

        # Send message to WebSocket
        try:
            await self.send(text_data=str_tx)
        except:
            # If the channel layer is not available, send the data directly to all WebSocket connections in the group
            for connection in await self.get_all_connections():
                await connection.send_data_fallback(str_tx)
    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)
    async def send_data_fallback(self, data):
        # Send the data directly to the WebSocket connection
        await self.send(json.dumps(data, cls=DjangoJSONEncoder))
    async def get_all_connections(self):
        # Get all WebSocket connections in the group
        group_channels = await self.channel_layer.group_channels(self.room_group_name)
        connections = []
        for channel_name in group_channels:
            connection = self.__class__.for_channel(channel_name)
            connections.append(connection)
        return connections

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
            






