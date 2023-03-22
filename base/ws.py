import json
from django.core import serializers
from datetime import datetime, timedelta
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.utils import timezone
from django.db.models import Q
from base.api.views import setting_APIlogEnabled, visitor_ip_address, loginapi, funUTCtoLocal, counteractive
from base.models import APILog, Branch, CounterStatus, CounterType, DisplayAndVoice, PrinterStatus, Setting, TicketFormat, TicketTemp, TicketRoute, TicketData, TicketLog, CounterLoginLog, UserProfile, lcounterstatus
from base.api.serializers import displaylistSerivalizer, printerstatusSerivalizer
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import asyncio

wsHypertext = 'ws://'

def wssendvoice(bcode, countertypename, ttype, tno, cno):
    # {"cmd":"voice",
    #  "data":
    #    {
    #     "tickettype": "A", 
    #     "ticketnumber": "012",
    #     "counterno": "1"
    #     }
    # }
    context = None
    error = ''

    branch = None
    if error == '' :        
        branchobj = Branch.objects.filter( Q(bcode=bcode) )
        if branchobj.count() == 1:
            branch = branchobj[0]
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
        json_tx = {'cmd': 'voice',
            'data': {
            'tickettype' : ttype,
            'ticketnumber' : tno,
            'counternumber' : cno,
            }
        }
        str_tx = json.dumps(json_tx)

        context = {
        'type':'broadcast_message',
        'tx': str_tx,
        }
        
        channel_layer = get_channel_layer()
        channel_group_name = 'voice_' + bcode + '_' + countertypename
        print('channel_group_name:' + channel_group_name + ' sending data -> Channel_Layer:' + str(channel_layer)),
        try:
            async_to_sync (channel_layer.group_send)(channel_group_name, context)
            print('...Done')
        except Exception as e:
            print('...Error:'),
            print(e)

    if error != '':
        print ('WS send voice Error:' & error)



def wsSendTicketStatus(bcode, tickettype, ticketnumber, sc):
    # {
    #     "cmd": "tstatus",
    #     "data": 
    #         {
    #             "status": "waiting",
    #             "counternumber": "1",
    #             "counterlang1": "Counter",
    #             "counterlang2": "櫃台",
    #         }
    # }  
    error = ''
    branch = None
    counterno = '---'

    if error == '' :
        if bcode == '':
            error = 'No branch code'
    if error == '' :
        if tickettype == '':
            error = 'No ticket type'
    if error == '' :
        if ticketnumber == '':
            error = 'No ticket number'       
    if error == '' :
        if sc == '':
            error = 'No Securitycode'
    if error == '' :
        branchobj = Branch.objects.filter( Q(bcode=bcode) )
        if branchobj.count() == 1:
            branch = branchobj[0]
        else :
            error = 'Branch not found.'
    if error == '':
        tobj = TicketTemp.objects.filter(Q(branch=branch) & Q(tickettype=tickettype) & Q(ticketnumber=ticketnumber) & Q(securitycode=sc))
        if tobj.count() == 1 :
            ticket = tobj[0]
        else:
            error = 'Ticket not found.'
    if error == '':
        csobj = CounterStatus.objects.filter(Q(tickettemp=ticket)) 
        if csobj.count() == 1:
            counterstatus = csobj[0]
            counterno = counterstatus.counternumber

    if error == '':
        json_tx = {'cmd': 'tstatus',
            'data': {
                "status": ticket.status,
                "counternumber": counterno,
                "counterlang1": ticket.countertype.lang1,
                "counterlang2": ticket.countertype.lang2,
            }
        }
        str_tx = json.dumps(json_tx)

        context = {
        'type':'broadcast_message',
        'tx': str_tx,
        }
        
        channel_layer = get_channel_layer()
        channel_group_name = 'ticketstatus_' + bcode + '_' + tickettype + ticketnumber + '_' + sc
        print('channel_group_name:' + channel_group_name + ' sending data -> Channel_Layer:' + str(channel_layer)),
        try:
            async_to_sync (channel_layer.group_send)(channel_group_name, context)
            print('...Done')
        except Exception as e:
            print('...Error:'),
            print(e)

    if error != '':
        print ('WS send ticket status Error:' & error)            

    pass

def wsSendPrintTicket(bcode, tickettype, ticketnumber, tickettime, tickettext, printernumber):
    # {
    #     "cmd": "prt",
    #     "data": 
    #         {
    #             "tickettype": "A",
    #             "ticketnumber": "001",
    #             "bcode": "KB",
    #             "tickettime": "2023-03-20T09:26:20Z",
    #             "tickettext": "<CEN>\r\n<LOGO>\r\n<TEXT>歡迎光臨，請稍候<LINE>\r\n<TEXT>Welcome, please wait to be served<LINE>\r\n<LINE>\r\n<B_FONT>\r\n<TEXT>票 號<LINE>\r\n<TEXT>Ticket number<LINE>\r\n<D_FONT><TEXT>A001<LINE>\r\n<N_FONT>\r\n<TEXT>17:26:20 20-03-2023\r\n<QR>http://192.168.1.22:8000/my/?tt=A&no=001&bc=KB&sc=EwC<LINE>\r\n<TEXT>Scan QR code for your e-ticket<LINE>\r\n<TEXT>掃描QR查看您的網上飛仔<LINE>\r\n<CUT>",
    #             "printernumber": "<pno>P1</pno>"
    #         }
    # }
    error = ''
    branch = None

    if error == '' :
        if bcode == '':
            error = 'No branch code'
    if error == '' :
        if tickettype == '':
            error = 'No ticket type'
    if error == '' :
        if ticketnumber== '':
            error = 'No ticket number'
    if error == '' :
        if tickettime== '':
            error = 'No ticket time'
    if error == '':
        stickettime = '' 
        try:
            stickettime = tickettime.strftime('%Y-%m-%dT%H:%M:%S.%fZ')
        except:
            stickettime = ''
        if stickettime == '' :
            try :
                stickettime = tickettime.strftime('%Y-%m-%dT%H:%M:%SZ')
            except:
                stickettime = ''
                error =  'Ticket time format not correct. Should be : 2022-05-19T23:59:59.123456Z'
    if error == '' :
        if tickettext== '':
            error = 'No ticket text'                        
    if error == '' :
        branchobj = Branch.objects.filter( Q(bcode=bcode) )
        if branchobj.count() == 1:
            branch = branchobj[0]
        else :
            error = 'Branch not found.'
    if error == '':
        jsontx = {
            "cmd":"prt",
            "data": 
                {
                    "tickettype": tickettype,
                    "ticketnumber": ticketnumber,
                    "bcode": bcode,
                    "tickettime": stickettime,
                    "tickettext": tickettext,
                    "printernumber": printernumber,
                },
        }
        str_tx = json.dumps(jsontx)
        # print(str_tx)             
       

        context = {
        'type':'broadcast_message',
        'tx':str_tx
        }

        channel_layer = get_channel_layer()
        channel_group_name = 'print_' + bcode 
        print('channel_group_name:' + channel_group_name + ' sending data -> Channel_Layer:' + str(channel_layer)),
        try:
            async_to_sync (channel_layer.group_send)(channel_group_name, context)
            print('...Done')
        except:
            print('...ERROR:Redis Server is down!')

    if error != '':
        print ('WS send print Error:'),
        print (error)

def wssendprinterstatus(bcode):
    # {
    #    "cmd":"ps",
    #    "data":[
    #       {
    #          "printernumber":"P1",
    #          "statustext":"good",
    #          "status":"<P_FINE>"
    #       },
    #       {
    #          "printernumber":"P2",
    #          "statustext":"Paper out",
    #          "status":"<P_FINE>"
    #       }
    #    ]
    # }
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
        PSserializers  = printerstatusSerivalizer(printerstatuslist, many=True)
        jsontx = {
            "cmd":"ps",
            "data": "<printerstatus>"
            }
        str_tx = json.dumps(jsontx)
        # print(str_tx)             
        str_tx = str_tx.replace('"<printerstatus>"', json.dumps(PSserializers.data))
        # print(str_tx)

        context = {
        'type':'broadcast_message',
        'tx':str_tx
        }

        channel_layer = get_channel_layer()
        channel_group_name = 'printerstatus_' + bcode 
        print('channel_group_name:' + channel_group_name + ' sending data -> Channel_Layer:' + str(channel_layer)),
        try:
            async_to_sync (channel_layer.group_send)(channel_group_name, context)
            print('...Done')
        except:
            print('...ERROR:Redis Server is down!')

    if error != '':
        print ('WS send printer status Error:' & error)

    


def wssendql(bcode, countertypename, ticket, cmd):
    # {"cmd":"add",
    #  "data":
    #    {
    #     "tickettype": "A", 
    #     "ticketnumber": "012",
    #     "tickettime": "2023-03-17T15:06:53.337639Z"
    #     }
    # }
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

        json_tx = {'cmd': cmd,
            'data': {
            'tickettype' : ticket.tickettype,
            'ticketnumber' : ticket.ticketnumber,
            'tickettime' : stickettime,
            }
        }
        str_tx = json.dumps(json_tx)

        context = {
        'type':'broadcast_message',
        'tx': str_tx,
        }
        
        channel_layer = get_channel_layer()
        channel_group_name = 'ql_' + bcode + '_' + countertypename
        print('channel_group_name:' + channel_group_name + ' sending data -> Channel_Layer:' + str(channel_layer)),
        try:
            async_to_sync (channel_layer.group_send)(channel_group_name, context)
            print('...Done')
        except Exception as e:
            print('...Error:'),
            print(e)

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
            
        wdserializers = displaylistSerivalizer(displaylist, many=True)
        jsontx = {
            "cmd":"list5",
            "data": {
                "lastupdate": str_now,
                "ticketlist": "<ticketlist>",
                "scroll": countertype.displayscrollingtext,
                }
            }
        str_tx = json.dumps(jsontx)
        # print(str_tx)             
        str_tx = str_tx.replace('"<ticketlist>"', json.dumps(wdserializers.data))
        print(str_tx)

        context = {
        'type':'broadcast_message',
        'tx':str_tx
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

    

  