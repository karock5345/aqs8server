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
import logging

wsHypertext = 'ws://'
logger = logging.getLogger(__name__)

# ws to Display Panel cmd call / recall a ticket
def wssenddispcall(branch, counterstatus, countertype, ticket):
    str_now = '--:--'
    datetime_now =timezone.now()
    datetime_now_local = funUTCtoLocal(datetime_now, branch.timezone)
    str_now = datetime_now_local.strftime('%Y-%m-%d %H:%M:%S')  

    jticket = {
        "ticket" : {
            "tickettype": ticket.tickettype,
            "ticketnumber": ticket.ticketnumber,
            "tickettime": ticket.tickettime.strftime('%Y-%m-%dT%H:%M:%S.%fZ'),
            "displaytime": datetime_now,
            "counternumber": counterstatus.counternumber,
            "wait": ticket.ticketroute.waiting,
            "flashtime": branch.flashlighttime,
            "ct_lang1": countertype.lang1,
            "ct_lang2": countertype.lang2,
            "ct_lang3": countertype.lang3,
            "ct_lang4": countertype.lang4,
            "t_lang1": ticket.ticketformat.lang1,
            "t_lang2": ticket.ticketformat.lang2,
            "t_lang3": ticket.ticketformat.lang3,
            "t_lang4": ticket.ticketformat.lang4,
        }
    }

    jsontx = {
        "cmd":"call",
        "data": {
            "servertime": str_now,
            "scroll": countertype.displayscrollingtext,
            "ticket": jticket,
            }
        }
    str_tx = json.dumps(jsontx)        
    # str_tx = str_tx.replace('"<ticketlist>"', json.dumps(wdserializers.data))

    context = {
    'type':'broadcast_message',
    'tx':str_tx
    }
    channel_layer = get_channel_layer()
    channel_group_name = 'disp_' + branch.bcode + '_' + countertype.name
    logger.info('channel_group_name:' + channel_group_name + ' sending data -> Channel_Layer:' + str(channel_layer)),
    try:
        async_to_sync (channel_layer.group_send)(channel_group_name, context)
        logger.info('...Done')
    except:
        logger.error('...ERROR:Redis Server is down!')
    pass
# ws to Display Panel cmd remove a ticket
# ws to Display Panel cmd clear all ticket
# ws to Display Panel cmd number of queue by TicketType 


def wssendflashlight(branch, countertype, counterstatus, cmd):
    # {"cmd":"light",
    #  "data":
    #    {
    #     "flashid": "1", 
    #     "cmd": "on/off/flash",
    #     "flashtime": "3",
    #     "countertypename": "Counter",
    #     }
    # }
    context = None
    error = ''

    flashid = counterstatus.flashid
    flashtime = branch.flashlighttime

    if error == '' : 
        json_tx = {'cmd': 'light',
            'data': {
                    "flashid": flashid,
                    "flashcmd": cmd,
                    "flashtime": flashtime,
                    "countertypename": countertype.name,
            }
        }
        str_tx = json.dumps(json_tx)

        context = {
        'type':'broadcast_message',
        'tx': str_tx,
        }
        
        channel_layer = get_channel_layer()
        channel_group_name = 'flashlight_' + branch.bcode
        logger.info('channel_group_name:' + channel_group_name + ' sending data -> Channel_Layer:' + str(channel_layer)),
        try:
            async_to_sync (channel_layer.group_send)(channel_group_name, context)
            logger.info('...Done')
        except Exception as e:
            # error_e = 'WS send voice Error:' + str(e)
            logger.error('...ERROR:Redis Server is down!')

    if error != '':
        error_e = 'WS send Flash Light (Control Box Python) Error:' + error
        logger.error(error_e)




def wscounterstatus(counterstatus):
    # {"cmd":"cs",
    #  "lastupdate":now,
    #  "data":
    #    {
    #     "status": "waiting",", 
    #     "tickettype": "A",
    #     "ticketnumber": "012",
    #     }
    # }
    context = None
    str_now = '--:--'
    datetime_now =timezone.now()
    datetime_now_local = funUTCtoLocal(datetime_now, counterstatus.countertype.branch.timezone)
    str_now = datetime_now_local.strftime('%Y-%m-%d %H:%M:%S')  
    if counterstatus.tickettemp is None:
        json_tx = {
            'cmd': 'cs',
            'lastupdate': str_now,
            'data': {
                'status' : counterstatus.status,
                'tickettype' : '',
                'ticketnumber' : '',            
                }
        }
    else:
        json_tx = {
            'cmd': 'cs',
            'lastupdate': str_now,
            'data': {
                'status' : counterstatus.status,
                'tickettype' : counterstatus.tickettemp.tickettype,
                'ticketnumber' : counterstatus.tickettemp.ticketnumber,            
                }
        }
    str_tx = json.dumps(json_tx)

    context = {
    'type':'broadcast_message',
    'tx': str_tx,
    }
    
    channel_layer = get_channel_layer()
    channel_group_name = 'cs_' + str(counterstatus.id)
    logger.info('channel_group_name:' + channel_group_name + ' sending data -> Channel_Layer:' + str(channel_layer)),
    try:
        async_to_sync (channel_layer.group_send)(channel_group_name, context)
        logger.info('...Done')
    except Exception as e:
        error_e = 'Error: ' + str(e)
        logger.error('...ERROR:Redis Server is down!')

   
def wsrochesms(bcode, tel, msg):
    # {"cmd":"sms",
    #  "data":
    #    {
    #     "tel": "+85263555345", 
    #     "msg": "testing123",
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



    if error == '' : 
        json_tx = {'cmd': 'sms',
            'data': {
            'tel' : tel,
            'msg' : msg,            
            }
        }
        str_tx = json.dumps(json_tx)

        context = {
        'type':'broadcast_message',
        'tx': str_tx,
        }
        
        channel_layer = get_channel_layer()
        channel_group_name = 'sms_' + bcode 
        logger.info('channel_group_name:' + channel_group_name + ' sending data -> Channel_Layer:' + str(channel_layer)),
        try:
            async_to_sync (channel_layer.group_send)(channel_group_name, context)
            logger.info('...Done')
        except Exception as e:
            # error_e = 'Error: ' + str(e)
            logger.error('...ERROR:Redis Server is down!')

    if error != '':
        error_e = 'WS send SMS Error:'+ error
        logger.error(error_e)


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
        logger.info('channel_group_name:' + channel_group_name + ' sending data -> Channel_Layer:' + str(channel_layer)),
        try:
            async_to_sync (channel_layer.group_send)(channel_group_name, context)
            logger.info('...Done')
        except Exception as e:
            # error_e = 'WS send voice Error:' + str(e)
            logger.error('...ERROR:Redis Server is down!')

    if error != '':
        error_e = 'WS send voice Error:' + error
        logger.error(error_e)



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
        logger.info('channel_group_name:' + channel_group_name + ' sending data -> Channel_Layer:' + str(channel_layer)),
        try:
            async_to_sync (channel_layer.group_send)(channel_group_name, context)
            logger.info('...Done')
        except Exception as e:
            # e_error = '...Error:' + str(e)
            logger.error('...ERROR:Redis Server is down!')

    if error != '':    
        logger.error('WS send ticket status Error:' + error)      

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
       
        context = {
        'type':'broadcast_message',
        'tx':str_tx
        }

        channel_layer = get_channel_layer()
        channel_group_name = 'print_' + bcode 
        logger.info('channel_group_name:' + channel_group_name + ' sending data -> Channel_Layer:' + str(channel_layer)),
        try:
            async_to_sync (channel_layer.group_send)(channel_group_name, context)
            logger.info('...Done')
        except:
            logger.error('...ERROR:Redis Server is down!')

    if error != '':
        logger.error('WS send print Error:' + error)

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
    str_now = '--:--'

    if error == '' :
        if bcode == '':
            error = 'No branch code'

    if error == '' :
        branchobj = Branch.objects.filter( Q(bcode=bcode) )
        if branchobj.count() == 1:
            branch = branchobj[0]
            datetime_now = timezone.now()
            datetime_now_local = funUTCtoLocal(datetime_now, branch.timezone)
            str_now = datetime_now_local.strftime('%Y-%m-%d %H:%M:%S')
        else :
            error = 'Branch not found.'

    if error == '' :
        printerstatuslist = PrinterStatus.objects.filter( Q(branch=branch) ).order_by('-updated')
        PSserializers  = printerstatusSerivalizer(printerstatuslist, many=True)
        jsontx = {
            "lastupdate":str_now,
            "cmd":"ps",
            "data": "<printerstatus>"
            }
        str_tx = json.dumps(jsontx)           
        str_tx = str_tx.replace('"<printerstatus>"', json.dumps(PSserializers.data))

        context = {
        'type':'broadcast_message',
        'tx':str_tx
        }

        channel_layer = get_channel_layer()
        channel_group_name = 'printerstatus_' + bcode 
        logger.info('channel_group_name:' + channel_group_name + ' sending data -> Channel_Layer:' + str(channel_layer)),
        try:
            async_to_sync (channel_layer.group_send)(channel_group_name, context)
            logger.info('...Done')
        except:
            logger.error('...ERROR:Redis Server is down!')

    if error != '':
        logger.error('WS send printer status Error:' & error)

    


def wssendql(bcode, countertypename, ticket, cmd):
    # {"cmd":"add",
    #  "lastupdate":now,
    #  "data":
    #    {
    #     "tickettype": "A", 
    #     "ticketnumber": "012",
    #     "tickettime": "2023-03-17T15:06:53.337639Z",
    #     "ttid": 1,
    #     }
    # }
    context = None
    error = ''
    str_now = '--:--'
    datetime_now =timezone.now()


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
            datetime_now_local = funUTCtoLocal(datetime_now, countertype.branch.timezone)
            str_now = datetime_now_local.strftime('%Y-%m-%d %H:%M:%S')  
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
        tickettime_local = funUTCtoLocal(ticket.tickettime, ticket.branch.timezone)
        tickettime_local = tickettime_local.strftime('%H:%M:%S %Y-%m-%d')

        json_tx = {
            'cmd': cmd,
            'lastupdate': str_now,
            'data': {
                'tickettype' : ticket.tickettype,
                'ticketnumber' : ticket.ticketnumber,
                'tickettime' : stickettime,
                'tickettime_local' : tickettime_local,
                'ttid' : ticket.id,
                }
        }
        str_tx = json.dumps(json_tx)

        context = {
        'type':'broadcast_message',
        'tx': str_tx,
        }
        
        channel_layer = get_channel_layer()
        channel_group_name = 'ql_' + bcode + '_' + countertypename
        logger.info('channel_group_name:' + channel_group_name + ' sending data -> Channel_Layer:' + str(channel_layer)),
        try:
            async_to_sync (channel_layer.group_send)(channel_group_name, context)
            logger.info('...Done')
        except Exception as e:
            logger.error('...ERROR:Redis Server is down!')

    if error != '':
        logger.error('WS send queue list Error:' & error)

    


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
        # for display in displaylist:
        #     logger.warning('display:' + str(display.tickettemp))
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
        str_tx = str_tx.replace('"<ticketlist>"', json.dumps(wdserializers.data))

        context = {
        'type':'broadcast_message',
        'tx':str_tx
        }
        channel_layer = get_channel_layer()
        channel_group_name = 'webtv_' + bcode + '_' + countertypename
        logger.info('channel_group_name:' + channel_group_name + ' sending data -> Channel_Layer:' + str(channel_layer)),
        try:
            async_to_sync (channel_layer.group_send)(channel_group_name, context)
            logger.info('...Done')
        except:
            logger.error('...ERROR:Redis Server is down!')
    if error != '' :
        logger.error('WS send webtv Error:' & error)

    

  