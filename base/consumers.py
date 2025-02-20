# base.consumers.py
import json
from channels.generic.websocket import AsyncWebsocketConsumer, WebsocketConsumer
# from asgiref.sync import async_to_sync
from django.db.models import Q
# from django.utils import timezone
from .views import funUTCtoLocal
from .models import Branch, CounterType, TicketTemp, CounterStatus
from asgiref.sync import sync_to_async
import logging
from django.core.serializers.json import DjangoJSONEncoder
from celery.result import AsyncResult
import asyncio
import redis

logger = logging.getLogger(__name__)
# max. number of WebTVConsumer_pub connected for each branch
ws_connected_dict = {}
ws_connected_max = 200

# dict to store WS connection for each branch
# {'KB':
#       {
#        'webtv':
#            {
#                'pub':
#                    { 'count': 2,
#                        'ip': ['ip1', 'ip2']
#                    },
#                'int':
#                    { 'count': 4,
#                        'ip': ['ip1', 'ip2', 'ip3', 'ip4']
#                    }
#            },
#        'eticket':{...}
#       }
# }
# self.ws_str for key of ws_connected_dict : 
#   Channel : ReportRaw_ProgressConsumer - 'reportraw' for internal ReportRaw use.
#   Channel : FlashLightConsumer - 'flashlight' for internal FlashLight use.
#   Channel : CounterStatusConsumer - 'cs' for internal Softkey use.
#   Channel : SMSConsumer - 'sms' for internal SMS use.
#   Channel : VoiceConsumer - 'voice' for internal VoiceComp use.
#   Channel : TicketStatus - 'eticket' for web online e-ticket for public use.
#   Channel : PrintConsumer - 'print' for internal PrinterControl use.
#   Channel : PrintStatusConsumer - 'printstatus' for internal Softkey use.
#   Channel : QLConsumer - 'ql' for internal Softkey, admin use.
#   Channel : WebTVConsumer - 'webtv' and 'wtv'. 'webtv' for web online tv public use, 'wtv' for interal Disp Penal use.
#   Channel : DispPanelConsumer - 'disp' for internal Disp Penal use.
# print('Count of KB webtv public:' + str(ws_connected_dict['KB']['webtv']['pub']['count']))
# ws_connected_dict['KB']['webtv']['pub']['ip'].append('test')
# print('IP list of KB webtv public:' + str(ws_connected_dict['KB']['webtv']['pub']['ip']))

def new_ws_connected_dict(bcode, ws):

    if bcode not in ws_connected_dict:
        ws_connected_dict[bcode] = {}
    
    ws_connected_dict[bcode][ws] = {}
    ws_connected_dict[bcode][ws]['pub'] = {}
    ws_connected_dict[bcode][ws]['pub']['count'] = 0
    ws_connected_dict[bcode][ws]['pub']['ip'] = []
    ws_connected_dict[bcode][ws]['int'] = {}
    ws_connected_dict[bcode][ws]['int']['count'] = 0
    ws_connected_dict[bcode][ws]['int']['ip'] = []

    return ws_connected_dict

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

        self.ws_str = 'disp'
        # get the url route: 'webtv' or 'wtv'
        self.route = self.scope['path'].split('/')[2]
        self.bcode = self.scope['url_route']['kwargs']['bcode']
        self.ct = self.scope['url_route']['kwargs']['ct']

        if error == '':
            if self.scope['user'].is_authenticated == False:
                error = 'DispConsumer: User not authenticated.'


        # check bcode and ct (countertype) is not exit do not accept connection
        if error == '':
            error = await check_input()       

        if error == '':
            exist = True        
            if self.bcode not in ws_connected_dict :
                exist = False
            elif self.ws_str not in ws_connected_dict[self.bcode]:
                exist = False
            if exist == False:
                new_ws_connected_dict(self.bcode, self.ws_str)

        if error == '':
            try:
                await self.channel_layer.group_add(
                    self.room_group_name,
                    self.channel_name
                )

                await self.accept()

                ip = self.scope['client'][0]
                ws_connected_dict[self.bcode][self.ws_str]['int']['count'] = ws_connected_dict[self.bcode][self.ws_str]['int']['count'] + 1
                ws_connected_dict[self.bcode][self.ws_str]['int']['ip'].append(ip)
                logger.info('IP ' + ip +  ' Connected:' + self.room_group_name + ' [' + str(ws_connected_dict[self.bcode][self.ws_str]['int']['count']) + ']' )
            except:
                error = 'DispPanelConsumer: Error in connect (Redis maybe down).'
        
        if error != '':
            logger.info('Error:' + error )
            try:
                await self.close()
            except:
                pass
            

    # Receive message from room group
    async def broadcast_message(self, event):
        str_tx = event['tx']

        # Send message to WebSocket
        try:
            await self.send(text_data=str_tx)
            # delay 1 second
            # await asyncio.sleep(1)
            # await self.send(text_data=str_tx)
            # # delay 1 second
            # await asyncio.sleep(1)
            # await self.send(text_data=str_tx)
        except:
            # If the channel layer is not available, send the data directly to all WebSocket connections in the group
            for connection in await self.get_all_connections():
                await connection.send_data_fallback(str_tx)
    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

        ip = self.scope['client'][0]
        try:
            ws_connected_dict[self.bcode][self.ws_str]['int']['count'] = ws_connected_dict[self.bcode][self.ws_str]['int']['count'] - 1
            ws_connected_dict[self.bcode][self.ws_str]['int']['ip'].remove(ip)     
            logger.info('Disconnected:' + self.room_group_name + ' Internal [' + str(ws_connected_dict[self.bcode][self.ws_str]['int']['count']) + ']')    
        except:
            logger.info('Disconnected:' + self.room_group_name )
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



class Report_ProgressProcessConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # Retrieve the task_id from the URL query parameter
        self.ptask_id = self.scope['url_route']['kwargs']['task_id']

        self.task_id = self.ptask_id.replace('_', '-')

        self.room_group_name = 'progress_p_' + self.ptask_id
        logger.info('connecting:' + self.room_group_name )
        
        try:
            await self.channel_layer.group_add(
                    self.room_group_name,
                    self.channel_name
                )

            await self.accept()

            # Start polling the task progress
            await self.check_progress()
        except:
            logger.error('Error in connect Report_ProgressProcessConsumer (Redis maybe down).')
    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def check_progress(self):

        # Retrieve the task result using the task_id
        task_result = AsyncResult(self.task_id)
        
        # Log the task_id and task_result for debugging
        # logger.info(f"Task ID: {self.task_id}, Task Result: {task_result}")

        # Loop until the task is complete or not found
        while task_result is not None and not task_result.ready():
            # Get the progress from the task's state
            progress = 0
            if task_result.status == 'SUCCESS':
                progress = 100
            elif task_result.status == 'FAILURE':
                progress = 0
            elif task_result.status == 'PROGRESS':
                progress = task_result.info.get('progress')  # needs to be set by task
            elif task_result.status == 'PENDING':
                progress = 'P'

            # print('Task status:' + task_result.status + ' ' + str(progress))
            await self.send(text_data=json.dumps({'progress': progress}))

            # Sleep to simulate updates (replace with actual progress retrieval)
            await asyncio.sleep(1)

            # Update the task_result for the next iteration
            task_result = AsyncResult(self.task_id)

        # Task is complete or not found, send a final message
        if task_result is None:
            await self.send(text_data=json.dumps({'progress': 100, 'task_complete': False}))
        else:
            await self.send(text_data=json.dumps({'progress': 100, 'task_complete': True}))


class ReportRaw_ProgressConsumer(AsyncWebsocketConsumer):
    async def connect(self):


        error = ''
        # Retrieve the task_id from the URL query parameter
        self.ptask_id = self.scope['url_route']['kwargs']['task_id']
        self.task_id = self.ptask_id.replace('_', '-')
        self.ws_str = 'reportraw'
        # self.bcode is fixed 'ALL_...' for all branch
        self.bcode = 'ALL3DiWk6siJ865kG3Ljgf72g46gfj5kDj4gk'

        self.room_group_name = 'progress_' + self.ptask_id
        logger.info('connecting:' + self.room_group_name )        

        if error == '':
            if self.scope['user'].is_authenticated == False:
                error = 'User not authenticated.'
        if error == '':
            exist = True        
            if self.bcode not in ws_connected_dict :
                exist = False
            elif self.ws_str not in ws_connected_dict[self.bcode]:
                exist = False
            if exist == False:
                new_ws_connected_dict(self.bcode, self.ws_str)   

        if error == '':
            try:        
                await self.channel_layer.group_add(
                        self.room_group_name,
                        self.channel_name
                    )            
                await self.accept()
                ip = self.scope['client'][0]
                ws_connected_dict[self.bcode][self.ws_str]['int']['count'] = ws_connected_dict[self.bcode][self.ws_str]['int']['count'] + 1
                ws_connected_dict[self.bcode][self.ws_str]['int']['ip'].append(ip)
                logger.info('IP ' + ip +  ' Connected:' + self.room_group_name + ' [' + str(ws_connected_dict[self.bcode][self.ws_str]['int']['count']) + ']' )

                # Start polling the task progress
                await self.check_progress()
            except:
                error = 'Error in connect ReportRaw_ProgressConsumer (Redis maybe down).'
        if error != '':        
            logger.error('Error:' + error )
            try:
                await self.close()
            except:
                pass
            

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)
        ip = self.scope['client'][0]
        try:
            ws_connected_dict[self.bcode][self.ws_str]['int']['count'] = ws_connected_dict[self.bcode][self.ws_str]['int']['count'] - 1
            ws_connected_dict[self.bcode][self.ws_str]['int']['ip'].remove(ip)     
            logger.info('Disconnected:' + self.room_group_name + ' Internal [' + str(ws_connected_dict[self.bcode][self.ws_str]['int']['count']) + ']')    
        except:
            logger.info('Disconnected:' + self.room_group_name )

    async def check_progress(self):

        # Retrieve the task result using the task_id
        task_result = AsyncResult(self.task_id)
        
        # Log the task_id and task_result for debugging
        # logger.info(f'Task ID: {self.task_id}, Task Result: {task_result}')

        # Loop until the task is complete or not found
        while task_result is not None and not task_result.ready():
            # Get the progress from the task's state
            progress = 0
            if task_result.status == 'SUCCESS':
                progress = 100
            elif task_result.status == 'FAILURE':
                progress = 0
            elif task_result.status == 'PROGRESS':
                progress = task_result.info.get('progress')  # needs to be set by task
            elif task_result.status == 'PENDING':
                progress = 'P'

            # print('Task status:' + task_result.status + ' ' + str(progress))
            await self.send(text_data=json.dumps({'progress': progress}))

            # Sleep to simulate updates (replace with actual progress retrieval)
            await asyncio.sleep(1)

            # Update the task_result for the next iteration
            task_result = AsyncResult(self.task_id)

        # Task is complete or not found, send a final message
        if task_result is None:
            await self.send(text_data=json.dumps({'progress': 100, 'task_complete': False}))
        else:
            await self.send(text_data=json.dumps({'progress': 100, 'task_complete': True}))



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
        self.ws_str = 'flashlight'

        if error == '':
            if self.scope['user'].is_authenticated == False:
                error = 'FlashLightConsumer: User not authenticated.'


        logger.info('connecting:' + self.room_group_name )
        
        if error == '':
            if self.scope['user'].is_authenticated == False:
                error = 'FlashLightConsumer: User not authenticated.'

        if error == '':
            # check bcode and ct (countertype) is not exit do not accept connection
            error = await check_input()      

        if error == '':
            exist = True        
            if self.bcode not in ws_connected_dict :
                exist = False
            elif self.ws_str not in ws_connected_dict[self.bcode]:
                exist = False
            if exist == False:
                new_ws_connected_dict(self.bcode, self.ws_str) 

        if error == '': 
            try:
                await self.channel_layer.group_add(
                    self.room_group_name,
                    self.channel_name
                )

                await self.accept()
                ip = self.scope['client'][0]
                ws_connected_dict[self.bcode][self.ws_str]['int']['count'] = ws_connected_dict[self.bcode][self.ws_str]['int']['count'] + 1
                ws_connected_dict[self.bcode][self.ws_str]['int']['ip'].append(ip)
                logger.info('IP ' + ip +  ' Connected:' + self.room_group_name + ' [' + str(ws_connected_dict[self.bcode][self.ws_str]['int']['count']) + ']' )
            except:
                error = 'FlashLightConsumer: Error in connect (Redis maybe down).'

        if error != '':
            logger.error('Error:' + error )
            try:
                await self.close()
            except:
                pass
            

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
        ip = self.scope['client'][0]
        try:
            ws_connected_dict[self.bcode][self.ws_str]['int']['count'] = ws_connected_dict[self.bcode][self.ws_str]['int']['count'] - 1
            ws_connected_dict[self.bcode][self.ws_str]['int']['ip'].remove(ip)     
            logger.info('Disconnected:' + self.room_group_name + ' Internal [' + str(ws_connected_dict[self.bcode][self.ws_str]['int']['count']) + ']')    
        except:
            logger.info('Disconnected:' + self.room_group_name )
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
    # ws://127.0.0.1:8000/ws/<APP_NAME>/cs/<BCODE>/1/
    async def connect(self):
        @sync_to_async
        def check_input():
            error = ''
            counterstatus = None
            counterstatus = CounterStatus.objects.get(id=pk)
            if counterstatus is None:
                error = 'CounterStatus not found.'
           
            return error
        # @sync_to_async
        # def get_bcode():
        #     bcode = None
        #     try:
        #         counterstatus = CounterStatus.objects.get(id=pk)
        #         bcode = counterstatus.countertype.branch.bcode
        #     except:
        #         bcode = None
        #     return bcode
        
        error = ''
        self.pk = self.scope['url_route']['kwargs']['pk']
        self.bcode = self.scope['url_route']['kwargs']['bcode']

        pk = int(self.pk)

        # self.bcode = await get_bcode()
        if self.bcode == None:
            error = 'CounterStatusConsumer: Branch not found.'

        self.room_group_name = 'cs_' + self.bcode + '_' + self.pk
        self.ws_str = 'cs'
        logger.info('connecting:' + self.room_group_name )

        if error == '':
            if self.scope['user'].is_authenticated == False:
                error = 'CounterStatusConsumer: User not authenticated.'

        if error == '':
            # check bcode and ct (countertype) is not exit do not accept connection
            error = await check_input()      

        if error == '':
            exist = True        
            if self.bcode not in ws_connected_dict :
                exist = False
            elif self.ws_str not in ws_connected_dict[self.bcode]:
                exist = False
            if exist == False:
                new_ws_connected_dict(self.bcode, self.ws_str)

        if error == '':
            try:
                await self.channel_layer.group_add(
                    self.room_group_name,
                    self.channel_name
                )
                await self.accept()
                ip = self.scope['client'][0]
                ws_connected_dict[self.bcode][self.ws_str]['int']['count'] = ws_connected_dict[self.bcode][self.ws_str]['int']['count'] + 1
                ws_connected_dict[self.bcode][self.ws_str]['int']['ip'].append(ip)
                logger.info('IP ' + ip +  ' Connected:' + self.room_group_name + ' [' + str(ws_connected_dict[self.bcode][self.ws_str]['int']['count']) + ']' )
            except redis.exceptions.ConnectionError:
                error = 'CounterStatusConsumer: Error in connect (Redis maybe down).'
                # await self.send(json.dumps({"error": "Service temporarily unavailable"}))
                await self.close()        
        if error != '': 
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
        try:
            await self.channel_layer.group_discard(self.room_group_name, self.channel_name)        
        except redis.exceptions.ConnectionError:
            pass
        try:
            ip = self.scope['client'][0]
        except:
            ip = ''
        try:
            ws_connected_dict[self.bcode][self.ws_str]['int']['count'] = ws_connected_dict[self.bcode][self.ws_str]['int']['count'] - 1
            ws_connected_dict[self.bcode][self.ws_str]['int']['ip'].remove(ip)     
            logger.info('Disconnected:' + self.room_group_name + ' Internal [' + str(ws_connected_dict[self.bcode][self.ws_str]['int']['count']) + ']')    
        except:
            logger.info('Disconnected:' + self.room_group_name )
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
        self.ws_str = 'sms'
        logger.info('connecting:' + self.room_group_name )
        
        if error == '':
            if self.scope['user'].is_authenticated == False:
                error = 'SMSConsumer: User not authenticated.'

        if error == '':
            # check bcode and ct (countertype) is not exit do not accept connection
            error = await check_input()   

        if error == '':
            exist = True        
            if self.bcode not in ws_connected_dict :
                exist = False
            elif self.ws_str not in ws_connected_dict[self.bcode]:
                exist = False
            if exist == False:
                new_ws_connected_dict(self.bcode, self.ws_str)

        if error == '':
            try:
                await self.channel_layer.group_add(
                    self.room_group_name,
                    self.channel_name
                )
                await self.accept()
                ip = self.scope['client'][0]
                ws_connected_dict[self.bcode][self.ws_str]['int']['count'] = ws_connected_dict[self.bcode][self.ws_str]['int']['count'] + 1
                ws_connected_dict[self.bcode][self.ws_str]['int']['ip'].append(ip)
                logger.info('IP ' + ip +  ' Connected:' + self.room_group_name + ' [' + str(ws_connected_dict[self.bcode][self.ws_str]['int']['count']) + ']' )            
            except:
                error = 'SMSConsumer: Error in connect (Redis maybe down).'
        if error != '':
            logger.error('Error:' + error )
            try:
                await self.close()
            except:
                pass
            

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
        ip = self.scope['client'][0]
        try:
            ws_connected_dict[self.bcode][self.ws_str]['int']['count'] = ws_connected_dict[self.bcode][self.ws_str]['int']['count'] - 1
            ws_connected_dict[self.bcode][self.ws_str]['int']['ip'].remove(ip)     
            logger.info('Disconnected:' + self.room_group_name + ' Internal [' + str(ws_connected_dict[self.bcode][self.ws_str]['int']['count']) + ']')    
        except:
            logger.info('Disconnected:' + self.room_group_name )
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

class Voice830Consumer(AsyncWebsocketConsumer):
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
        self.ws_str = 'voice830'
        self.room_group_name = 'voice830_' + self.bcode + '_' + self.ct
        logger.info('connecting:' + self.room_group_name )
        
        if error == '':
            if self.scope['user'].is_authenticated == False:
                error = 'Voice830Consumer: User not authenticated.'

        if error == '':
            # check bcode and ct (countertype) is not exit do not accept connection
            error = await check_input()       

        if error == '':
            exist = True        
            if self.bcode not in ws_connected_dict :
                exist = False
            elif self.ws_str not in ws_connected_dict[self.bcode]:
                exist = False
            if exist == False:
                new_ws_connected_dict(self.bcode, self.ws_str) 

        if error == '':
            try:
                await self.channel_layer.group_add(
                    self.room_group_name,
                    self.channel_name
                )
                await self.accept()
                ip = self.scope['client'][0]
                ws_connected_dict[self.bcode][self.ws_str]['int']['count'] = ws_connected_dict[self.bcode][self.ws_str]['int']['count'] + 1
                ws_connected_dict[self.bcode][self.ws_str]['int']['ip'].append(ip)
                logger.info('IP ' + ip +  ' Connected:' + self.room_group_name + ' [' + str(ws_connected_dict[self.bcode][self.ws_str]['int']['count']) + ']' )
            except:
                error = 'Voice830Consumer: Error in connect (Redis maybe down).'
        if error != '':
            logger.error('Error:' + error )
            try:
                await self.close()
            except:
                pass
            

    # Receive message from room group
    async def broadcast_message(self, event):
        str_tx = event['tx']

        # Send message to WebSocket
        try:
            await self.send(text_data=str_tx)
            # delay 1 second
            await asyncio.sleep(1)
        except:
            # If the channel layer is not available, send the data directly to all WebSocket connections in the group
            for connection in await self.get_all_connections():
                await connection.send_data_fallback(str_tx)
    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)
        ip = self.scope['client'][0]
        try:
            ws_connected_dict[self.bcode][self.ws_str]['int']['count'] = ws_connected_dict[self.bcode][self.ws_str]['int']['count'] - 1
            ws_connected_dict[self.bcode][self.ws_str]['int']['ip'].remove(ip)     
            logger.info('Disconnected:' + self.room_group_name + ' Internal [' + str(ws_connected_dict[self.bcode][self.ws_str]['int']['count']) + ']')    
        except:
            logger.info('Disconnected:' + self.room_group_name )        
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
        self.ws_str = 'voice'
        self.room_group_name = 'voice_' + self.bcode + '_' + self.ct
        logger.info('connecting:' + self.room_group_name )
        
        if error == '':
            if self.scope['user'].is_authenticated == False:
                error = 'VoiceConsumer: User not authenticated.'

        if error == '':
            # check bcode and ct (countertype) is not exit do not accept connection
            error = await check_input()       

        if error == '':
            exist = True        
            if self.bcode not in ws_connected_dict :
                exist = False
            elif self.ws_str not in ws_connected_dict[self.bcode]:
                exist = False
            if exist == False:
                new_ws_connected_dict(self.bcode, self.ws_str) 

        if error == '':
            try:
                await self.channel_layer.group_add(
                    self.room_group_name,
                    self.channel_name
                )
                await self.accept()
                ip = self.scope['client'][0]
                ws_connected_dict[self.bcode][self.ws_str]['int']['count'] = ws_connected_dict[self.bcode][self.ws_str]['int']['count'] + 1
                ws_connected_dict[self.bcode][self.ws_str]['int']['ip'].append(ip)
                logger.info('IP ' + ip +  ' Connected:' + self.room_group_name + ' [' + str(ws_connected_dict[self.bcode][self.ws_str]['int']['count']) + ']' )
            except:
                error = 'VoiceConsumer: Error in connect (Redis maybe down).'
        if error != '':        
            logger.error('Error:' + error )
            try:
                await self.close()
            except:
                pass
            

    # Receive message from room group
    async def broadcast_message(self, event):
        str_tx = event['tx']

        # Send message to WebSocket
        try:
            await self.send(text_data=str_tx)
            # delay 1 second
            await asyncio.sleep(1)
        except:
            # If the channel layer is not available, send the data directly to all WebSocket connections in the group
            for connection in await self.get_all_connections():
                await connection.send_data_fallback(str_tx)
    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)
        ip = self.scope['client'][0]
        try:
            ws_connected_dict[self.bcode][self.ws_str]['int']['count'] = ws_connected_dict[self.bcode][self.ws_str]['int']['count'] - 1
            ws_connected_dict[self.bcode][self.ws_str]['int']['ip'].remove(ip)     
            logger.info('Disconnected:' + self.room_group_name + ' Internal [' + str(ws_connected_dict[self.bcode][self.ws_str]['int']['count']) + ']')    
        except:
            logger.info('Disconnected:' + self.room_group_name )        
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
        self.ws_str = 'eticket'

        self.room_group_name = 'ticketstatus_' + self.bcode + '_' + self.ttype + self.tno + '_' + self.sc
        logger.info('connecting:' + self.room_group_name )
        
        # if error == '':
        #     if self.scope['user'].is_authenticated == False:
        #         error = 'TicketStatusConsumer: User not authenticated.'

        exist = True        
        if self.bcode not in ws_connected_dict :
            exist = False
        elif self.ws_str not in ws_connected_dict[self.bcode]:
            exist = False
        if exist == False:
            new_ws_connected_dict(self.bcode, self.ws_str)   

        if error == '':
            # check connection is not over max connection
            if ws_connected_dict[self.bcode][self.ws_str]['pub']['count'] >= ws_connected_max:
                error = 'TicketStatusConsumer: Connection is over max [' + str(ws_connected_max) + '] connection. '


        if error == '':
            # check bcode and ct (countertype) is not exit do not accept connection
            error = await check_input()     

        if error == '': 
            try:          
                await self.channel_layer.group_add(
                    self.room_group_name,
                    self.channel_name
                )
                await self.accept()
                ip = self.scope['client'][0]           
                ws_connected_dict[self.bcode][self.ws_str]['pub']['count'] = ws_connected_dict[self.bcode][self.ws_str]['pub']['count'] + 1
                ws_connected_dict[self.bcode][self.ws_str]['pub']['ip'].append(ip)
                logger.info('IP ' + ip +  ' Connected:' + self.room_group_name + ' [' + str(ws_connected_dict[self.bcode][self.ws_str]['pub']['count']) + '/' + str(ws_connected_max) + ']' )
            except:
                error = 'TicketStatusConsumer: Error in connect (Redis maybe down).'
        if error != '':
            logger.error('Error:' + error )
            try:
                await self.close()
            except:
                pass
            

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
        ip = self.scope['client'][0]                  
        ws_connected_dict[self.bcode][self.ws_str]['pub']['count'] = ws_connected_dict[self.bcode][self.ws_str]['pub']['count'] - 1
        # remove ip from list            
        ws_connected_dict[self.bcode][self.ws_str]['pub']['ip'].remove(ip)            
        logger.info('Disconnected:' + self.room_group_name + ' [' + str(ws_connected_dict[self.bcode][self.ws_str]['pub']['count']) + '/' + str(ws_connected_max) + ']' )

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
        self.ws_str = 'print'
        logger.info('connecting:' + self.room_group_name)

        if error == '':
            if self.scope['user'].is_authenticated == False:
                error = 'PrintConsumer: User not authenticated.'

        if error == '':
            # check bcode and ct (countertype) is not exit do not accept connection
            error = await check_input() 

        if error == '':
            exist = True        
            if self.bcode not in ws_connected_dict :
                exist = False
            elif self.ws_str not in ws_connected_dict[self.bcode]:
                exist = False
            if exist == False:
                new_ws_connected_dict(self.bcode, self.ws_str)   

        if error == '':
            try:
                await self.channel_layer.group_add(
                    self.room_group_name,
                    self.channel_name
                )
                await self.accept()
                ip = self.scope['client'][0]           
                ws_connected_dict[self.bcode][self.ws_str]['int']['count'] = ws_connected_dict[self.bcode][self.ws_str]['int']['count'] + 1
                ws_connected_dict[self.bcode][self.ws_str]['int']['ip'].append(ip)
                logger.info('IP ' + ip +  ' Connected:' + self.room_group_name + ' [' + str(ws_connected_dict[self.bcode][self.ws_str]['int']['count']) + ']' )
            except:
                error = 'PrintConsumer: Error in connect (Redis maybe down).'
        if error != '':
            logger.error('Error:' + error )
            try:
                await self.close()
            except:
                pass
            

    # Receive message from room group
    async def broadcast_message(self, event):
        str_tx = event['tx']

        # Send message to WebSocket
        try:
            await self.send(text_data=str_tx)
            # delay 1 second
            await asyncio.sleep(1)
        except:
            # If the channel layer is not available, send the data directly to all WebSocket connections in the group
            for connection in await self.get_all_connections():
                await connection.send_data_fallback(str_tx)
    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)
        ip = self.scope['client'][0]
        try:
            ws_connected_dict[self.bcode][self.ws_str]['int']['count'] = ws_connected_dict[self.bcode][self.ws_str]['int']['count'] - 1
            ws_connected_dict[self.bcode][self.ws_str]['int']['ip'].remove(ip)     
            logger.info('Disconnected:' + self.room_group_name + ' Internal [' + str(ws_connected_dict[self.bcode][self.ws_str]['int']['count']) + ']')    
        except:
            logger.info('Disconnected:' + self.room_group_name )
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
        self.ws_str = 'printstatus'
        logger.info('connecting:' + self.room_group_name )
        
        if error == '':
            if self.scope['user'].is_authenticated == False:
                error = 'PrinterStatusConsumer: User not authenticated.'

        if error == '':
            # check bcode and ct (countertype) is not exit do not accept connection
            error = await check_input()
            
        if error == '':
            exist = True        
            if self.bcode not in ws_connected_dict :
                exist = False
            elif self.ws_str not in ws_connected_dict[self.bcode]:
                exist = False
            if exist == False:
                new_ws_connected_dict(self.bcode, self.ws_str) 

        if error == '':
            try:
                await self.channel_layer.group_add(
                    self.room_group_name,
                    self.channel_name
                )
                await self.accept()
                ip = self.scope['client'][0]
                ws_connected_dict[self.bcode][self.ws_str]['int']['count'] = ws_connected_dict[self.bcode][self.ws_str]['int']['count'] + 1
                ws_connected_dict[self.bcode][self.ws_str]['int']['ip'].append(ip)
                logger.info('IP ' + ip +  ' Connected:' + self.room_group_name + ' [' + str(ws_connected_dict[self.bcode][self.ws_str]['int']['count']) + ']' )
            except redis.exceptions.ConnectionError:
                error = 'PrinterStatusConsumer: Error in connect. (Redis mayb be down)'
                # await self.send(json.dumps({"error": "Service temporarily unavailable"}))
                await self.close()
        if error != '':
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
        try:
            await self.channel_layer.group_discard(self.room_group_name, self.channel_name)        
        except redis.exceptions.ConnectionError:
            pass
        try:
            ip = self.scope['client'][0]
        except:
            ip = ''
        try:
            ws_connected_dict[self.bcode][self.ws_str]['int']['count'] = ws_connected_dict[self.bcode][self.ws_str]['int']['count'] - 1
            ws_connected_dict[self.bcode][self.ws_str]['int']['ip'].remove(ip)     
            logger.info('Disconnected:' + self.room_group_name + ' Internal [' + str(ws_connected_dict[self.bcode][self.ws_str]['int']['count']) + ']')    
        except:
            logger.info('Disconnected:' + self.room_group_name )
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
        self.ws_str = 'ql'
        logger.info('connecting:' + self.room_group_name )
        
        if error == '':
            if self.scope['user'].is_authenticated == False:
                error = 'QLConsumer: User not authenticated.'

        if error == '':
            # check bcode and ct (countertype) is not exit do not accept connection
            error = await check_input()      

        if error == '':
            exist = True        
            if self.bcode not in ws_connected_dict :
                exist = False
            elif self.ws_str not in ws_connected_dict[self.bcode]:
                exist = False
            if exist == False:
                new_ws_connected_dict(self.bcode, self.ws_str)   

        if error == '':
            try:          
                await self.channel_layer.group_add(
                    self.room_group_name,
                    self.channel_name
                )    
                await self.accept()
                ip = self.scope['client'][0]
                ws_connected_dict[self.bcode][self.ws_str]['int']['count'] = ws_connected_dict[self.bcode][self.ws_str]['int']['count'] + 1
                ws_connected_dict[self.bcode][self.ws_str]['int']['ip'].append(ip)
                logger.info('IP ' + ip +  ' Connected:' + self.room_group_name + ' [' + str(ws_connected_dict[self.bcode][self.ws_str]['int']['count']) + ']' )            
            except redis.exceptions.ConnectionError:
                # await self.send(json.dumps({"error": "Service temporarily unavailable"}))
                await self.close()
                error = 'QLConsumer: Error in connect (Redis maybe down).'


        if error != '':
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
        try:
            await self.channel_layer.group_discard(self.room_group_name, self.channel_name)        
        except redis.exceptions.ConnectionError:
            pass
        try:
            ip = self.scope['client'][0]
        except:
            ip = ''
        try:
            ws_connected_dict[self.bcode][self.ws_str]['int']['count'] = ws_connected_dict[self.bcode][self.ws_str]['int']['count'] - 1
            ws_connected_dict[self.bcode][self.ws_str]['int']['ip'].remove(ip)     
            logger.info('Disconnected:' + self.room_group_name + ' Internal [' + str(ws_connected_dict[self.bcode][self.ws_str]['int']['count']) + ']')    
        except:
            logger.info('Disconnected:' + self.room_group_name )        
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


# WebTVConsumer using 2 routes to separate public and internal
# /ws/webtv/[bcode]/[ct] for internal. No connection limited. Need cookie for authentication including web and app.
# /ws/wtv/[bcode]/[ct] for public. Connection limited. For web only.
class WebTVConsumer(AsyncWebsocketConsumer): 
    async def connect(self):
        error = ''
        @sync_to_async
        def check_input():

            error = ''
            branch = None
            if error == '':
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
                
        self.error = ''
        # get the url route: 'webtv' or 'wtv'
        self.route = self.scope['path'].split('/')[2]
        self.bcode = self.scope['url_route']['kwargs']['bcode']
        self.ct = self.scope['url_route']['kwargs']['ct']
        self.room_group_name = 'webtv_' + self.bcode + '_' + self.ct
        self.ws_str = 'webtv'
        logger.info('connecting:' + self.room_group_name )
        
        # get the connected count
        # check key is exist        
        exist = True        
        if self.bcode not in ws_connected_dict :
            exist = False
        elif self.ws_str not in ws_connected_dict[self.bcode]:
            exist = False
        if exist == False:
            new_ws_connected_dict(self.bcode, self.ws_str)                         
        
        if self.route == 'webtv':
            if self.error == '':
                if self.scope['user'].is_authenticated == False:
                    self.error = 'WebTVConsumer: User not authenticated.'

        if self.route == 'wtv':
            if self.error == '':
                # check connection is not over max connection
                if ws_connected_dict[self.bcode][self.ws_str]['pub']['count'] >= ws_connected_max:
                    self.error = 'WebTVConsumer: Connection is over max [' + str(ws_connected_max) + '] connection. '

        if self.error == '':
            # check paramaters is not exit do not accept connection
            self.error = await check_input() 


        if self.error == '':
            try:
                await self.channel_layer.group_add(
                    self.room_group_name,
                    self.channel_name
                )
                await self.accept()
                ip = self.scope['client'][0]

                if self.route == 'wtv':
                    ws_connected_dict[self.bcode][self.ws_str]['pub']['count'] = ws_connected_dict[self.bcode][self.ws_str]['pub']['count'] + 1
                    ws_connected_dict[self.bcode][self.ws_str]['pub']['ip'].append(ip)
                    logger.info('IP ' + ip +  ' Connected:' + self.room_group_name + ' [' + str(ws_connected_dict[self.bcode][self.ws_str]['pub']['count']) + '/' + str(ws_connected_max) + ']' )
                if self.route == 'webtv':
                    ws_connected_dict[self.bcode][self.ws_str]['int']['count'] = ws_connected_dict[self.bcode][self.ws_str]['int']['count'] + 1
                    ws_connected_dict[self.bcode][self.ws_str]['int']['ip'].append(ip)
                    logger.info('IP ' + ip +  ' Connected :' + self.room_group_name + ' Internal [' + str(ws_connected_dict[self.bcode][self.ws_str]['int']['count'])+ ']' )
            except:
                self.error = 'WebTVConsumer: Error in connect (Redis maybe down).'
        if self.error != '':
            logger.error('Error:' + self.error )
            try:
                await self.close()
            except:
                pass
            

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
        if self.error != "":
            logger.error('Rejected:' + self.room_group_name + ' (' + self.error +')')
        else:
            ip = self.scope['client'][0]
            if self.route == 'wtv':            
                ws_connected_dict[self.bcode][self.ws_str]['pub']['count'] = ws_connected_dict[self.bcode][self.ws_str]['pub']['count'] - 1
                # remove ip from list            
                ws_connected_dict[self.bcode][self.ws_str]['pub']['ip'].remove(ip)            
                logger.info('Disconnected:' + self.room_group_name + ' [' + str(ws_connected_dict[self.bcode][self.ws_str]['pub']['count']) + '/' + str(ws_connected_max) + ']' )
            elif self.route == 'webtv':
                ws_connected_dict[self.bcode][self.ws_str]['int']['count'] = ws_connected_dict[self.bcode][self.ws_str]['int']['count'] - 1
                ws_connected_dict[self.bcode][self.ws_str]['int']['ip'].remove(ip)     
                logger.info('Disconnected:' + self.room_group_name + ' Internal [' + str(ws_connected_dict[self.bcode][self.ws_str]['int']['count']) + ']'  )
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

    #     datetime_now =datetime.now(timezone.utc)
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

    #         datetime_now =datetime.now(timezone.utc)
    #         datetime_now_local = funUTCtoLocal(datetime_now, branch.timezone)

    #         context = {
    #         'lastupdate':datetime_now_local.strftime('%Y-%m-%d %H:%M:%S'),
    #         'ticketlist':displaylist,
    #         }

    #         output = json.dumps(context)

    #         self.send(output)
            







# class DispPanelConsumer(AsyncWebsocketConsumer):
#     async def connect(self):
#         @sync_to_async
#         def check_input():
#             error = ''
#             branch = None
#             # branchobj = await sync_to_async(Branch.objects.filter, thread_sensitive=True)( Q(bcode=self.bcode) )
#             branchobj = Branch.objects.filter(Q(bcode=self.bcode))

#             if branchobj.count() == 1:
#                 branch = branchobj[0]
#                 pass
#             else :
#                 error = 'Branch not found.'

#             if error == '':
#                 ctobj = CounterType.objects.filter( Q(branch=branch) & Q(name=self.ct) )
#                 if ctobj.count() == 1:
#                     # ct = ctobj[0]
#                     pass
#                 else :
#                     error = 'CounterType not found.'

#             return error
                
#         error = ''
#         self.bcode = self.scope['url_route']['kwargs']['bcode']
#         self.ct = self.scope['url_route']['kwargs']['ct']
#         self.room_group_name = 'disp_' + self.bcode + '_' + self.ct
#         logger.info('connecting:' + self.room_group_name )
        
#         if error == '':
#             if self.scope['user'].is_authenticated == False:
#                 error = 'DispPanelConsumer: User not authenticated.'

#         if error == '':
#             # check bcode and ct (countertype) is not exit do not accept connection
#             error = await check_input()       

#         if error == '':        
#             await self.channel_layer.group_add(
#                 self.room_group_name,
#                 self.channel_name
#             )
#             await self.accept()
            
#         else :
#             logger.error('Error:' + error )
#             await self.close()
            

#     # Receive message from room group
#     async def broadcast_message(self, event):
#         str_tx = event['tx']

#         # Send message to WebSocket
#         try:
#             await self.send(text_data=str_tx)
#         except:
#             # If the channel layer is not available, send the data directly to all WebSocket connections in the group
#             for connection in await self.get_all_connections():
#                 await connection.send_data_fallback(str_tx)
#     async def disconnect(self, close_code):
#         # Leave room group
#         await self.channel_layer.group_discard(self.room_group_name, self.channel_name)
#     async def send_data_fallback(self, data):
#         # Send the data directly to the WebSocket connection
#         await self.send(json.dumps(data, cls=DjangoJSONEncoder))
#     async def get_all_connections(self):
#         # Get all WebSocket connections in the group
#         group_channels = await self.channel_layer.group_channels(self.room_group_name)
#         connections = []
#         for channel_name in group_channels:
#             connection = self.__class__.for_channel(channel_name)
#             connections.append(connection)
#         return connections
