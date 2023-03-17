import json
from django.core import serializers
from datetime import datetime, timedelta
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.utils import timezone
from django.db.models import Q
from base.api.views import setting_APIlogEnabled, visitor_ip_address, loginapi, funUTCtoLocal, counteractive
from base.models import APILog, Branch, CounterStatus, CounterType, DisplayAndVoice, PrinterStatus, Setting, TicketFormat, TicketTemp, TicketRoute, TicketData, TicketLog, CounterLoginLog, UserProfile, lcounterstatus
from base.api.serializers import webdisplaylistSerivalizer, printerstatusSerivalizer
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import asyncio

wsHypertext = 'ws://'

def wssendprinterstatus(bcode):
    error = ''
    branch = None

    if error == '' :
        if bcode == '':
            error = 'No branch code'

    if error == '' :
        branchobj = Branch.objects.filter( Q(bcode=bcode) )
        if branchobj.count() == 1:
            branch = branchobj[0]
        else :
            error = 'Branch not found.'

    if error == '' :
        printerstatuslist = PrinterStatus.objects.filter( Q(branch=branch) ).order_by('-updated')
        serializers  = printerstatusSerivalizer(printerstatuslist, many=True)
        data = dict({'data':serializers.data})
        
        channel_layer = get_channel_layer()
        channel_group_name = 'printerstatus_' + bcode 
        print('channel_group_name:' + channel_group_name + ' sending data -> Channel_Layer:' + str(channel_layer)),
        try:
            async_to_sync (channel_layer.group_send)(channel_group_name, data)
            print('...Done')
        except:
            print('...ERROR:Redis Server is down!')

    if error != '':
        print ('WS send printer status Error:' & error)

    


def wssendql(bcode, countertypename, ticket, cmd):
    # cmd 'add' or 'del'
    context = None
    error = ''
    str_now = '---'

    branch = None
    if error == '' :        
        branchobj = Branch.objects.filter( Q(bcode=bcode) )
        if branchobj.count() == 1:
            branch = branchobj[0]
            datetime_now = timezone.now()
            datetime_now_local = funUTCtoLocal(datetime_now, branch.timezone)
            str_now = datetime_now_local.strftime('%Y-%m-%d %H:%M:%S')
        else :
            error = 'Branch not found.'

    # get the Counter type
    countertype = None
    if error == '' :    
        if countertypename == '' :
            ctypeobj = CounterType.objects.filter( Q(branch=branch) )
        else:
            ctypeobj = CounterType.objects.filter( Q(branch=branch) & Q(name=countertypename) )
        if (ctypeobj.count() > 0) :
            countertype = ctypeobj[0]
        else :
            error = 'Counter Type not found.' 

    if error == '' : 
        if cmd == '':
            cmd = 'add'
        if cmd == 'add' or cmd == 'del':
            pass
        else :
            cmd = 'add'

        try:
            stickettime = ticket.tickettime.strftime('%Y-%m-%dT%H:%M:%S.%fZ')
        except:
            stickettime = ''
        if stickettime == '' :
            try :                
                stickettime = ticket.tickettime.strftime('%Y-%m-%dT%H:%M:%SZ')
            except:
                stickettime = 'error'

        data = {
            'cmd':cmd,
            'tickettype' : ticket.tickettype,
            'ticketnumber' : ticket.ticketnumber,
            'tickettime' : stickettime,
        }
        context = {
        'type':'broadcast_message',
        'data': data,
        }
        channel_layer = get_channel_layer()
        channel_group_name = 'ql_' + bcode + '_' + countertypename
        print('channel_group_name:' + channel_group_name + ' sending data -> Channel_Layer:' + str(channel_layer)),
        try:
            async_to_sync (channel_layer.group_send)(channel_group_name, context)
            print('...Done')
        except:
            print('...ERROR:Redis Server is down!')

    if error != '':
        print ('WS send queue list Error:' & error)

    


def wssendwebtv(bcode, countertypename):
    context = None
    error = ''
    str_now = '---'

    branch = None
    if error == '' :        
        branchobj = Branch.objects.filter( Q(bcode=bcode) )
        if branchobj.count() == 1:
            branch = branchobj[0]
            datetime_now = timezone.now()
            datetime_now_local = funUTCtoLocal(datetime_now, branch.timezone)
            str_now = datetime_now_local.strftime('%Y-%m-%d %H:%M:%S')
        else :
            error = 'Branch not found.'

    # get the Counter type
    countertype = None
    if error == '' :    
        if countertypename == '' :
            ctypeobj = CounterType.objects.filter( Q(branch=branch) )
        else:
            ctypeobj = CounterType.objects.filter( Q(branch=branch) & Q(name=countertypename) )
        if (ctypeobj.count() > 0) :
            countertype = ctypeobj[0]
        else :
            error = 'Counter Type not found.' 

    if error == '' : 

        displaylist = DisplayAndVoice.objects.filter (branch=branch, countertype=countertype).order_by('-displaytime')[:5]
            
        wdserializers  = webdisplaylistSerivalizer(displaylist, many=True)

        context = {
        'type':'broadcast_message',
        'data': {
                'lastupdate' : str_now,
                'ticketlist' : wdserializers.data,
                'scroll' : countertype.displayscrollingtext,
                }
        }
        channel_layer = get_channel_layer()
        channel_group_name = 'webtv_' + bcode + '_' + countertypename
        print('channel_group_name:' + channel_group_name + ' sending data -> Channel_Layer:' + str(channel_layer)),
        try:
            async_to_sync (channel_layer.group_send)(channel_group_name, context)
            print('...Done')
        except:
            print('...ERROR:Redis Server is down!')
    if error != '' :
        print ('WS send webtv Error:' & error)

    

  