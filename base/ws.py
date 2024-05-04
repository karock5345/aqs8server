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
            "tickettype": ticket.tickettype,
            "ticketnumber": ticket.ticketnumber,
            "tickettime": ticket.tickettime.strftime('%Y-%m-%dT%H:%M:%S.%fZ'),
            "displaytime": datetime_now.strftime('%Y-%m-%dT%H:%M:%S.%fZ'),
            "counternumber": counterstatus.counternumber,
            "wait": ticket.ticketroute.waiting,
            "flashtime": branch.flashlighttime,
            "ct_lang1": countertype.lang1,
            "ct_lang2": countertype.lang2,
            "ct_lang3": countertype.lang3,
            "ct_lang4": countertype.lang4,
            "t_lang1": ticket.ticketformat.touchkey_lang1,
            "t_lang2": ticket.ticketformat.touchkey_lang2,
            "t_lang3": ticket.ticketformat.touchkey_lang3,
            "t_lang4": ticket.ticketformat.touchkey_lang4,
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
def wssenddispremoveall(branch,  countertype):
    str_now = '--:--'
    datetime_now =timezone.now()
    datetime_now_local = funUTCtoLocal(datetime_now, branch.timezone)
    str_now = datetime_now_local.strftime('%Y-%m-%d %H:%M:%S')  


    jsontx = {
        "cmd":"removeall",
        "data": {
            "servertime": str_now,
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
# ws to Display Panel cmd waiting number of queue by TicketType 
def wssenddispwait(branch,  countertype, ticket):
    str_now = '--:--'
    datetime_now =timezone.now()
    datetime_now_local = funUTCtoLocal(datetime_now, branch.timezone)
    str_now = datetime_now_local.strftime('%Y-%m-%d %H:%M:%S')  

    jwait = {
            "tickettype": ticket.tickettype,
            "wait": ticket.ticketroute.waiting,
    }

    jsontx = {
        "cmd":"wait",
        "data": {
            "servertime": str_now,
            "waitdata": jwait,
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
    #     "status": "waiting",
    #     "tickettype": "A",
    #     "ticketnumber": "012",
    #     "login": True/False,
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
                'login' : counterstatus.loged,    
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
                'login' : counterstatus.loged,            
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


# For Voice version 8.3.0
# /ws/voice830/BCode/Countertype/
# Channel Group Name: voice830_BCode_Countertype
# voice command
# { "cmd":"voice",
#   "data":
#     {
# 	    "lang":"[ENG]",
# 	    "voice_str":"[A],[0],[0],[5],[C3]"
#     }
# }
# volume command
# { "cmd":"vol",
#   "data":50
# }
def wssendvoice830(bcode, countertypename, counterstatus_id, ttype, tno, cno):
    context = None
    error = ''


    def send(json_tx:str):
        str_tx = json.dumps(json_tx)

        context = {
        'type':'broadcast_message',
        'tx': str_tx,
        }
        
        channel_layer = get_channel_layer()
        channel_group_name = 'voice830_' + bcode + '_' + countertypename
        logger.info('channel_group_name:' + channel_group_name + ' sending data -> Channel_Layer:' + str(channel_layer)),
        try:
            async_to_sync (channel_layer.group_send)(channel_group_name, context)
            logger.info('...Done')
        except Exception as e:
            # error_e = 'WS send voice Error:' + str(e)
            logger.error('...ERROR:Redis Server is down!')


    branch = None
    if error == '' :        
        branchobj = Branch.objects.filter( Q(bcode=bcode) )
        if branchobj.count() == 1:
            branch = branchobj[0]
        else :
            error = 'Branch not found.'
    if error == '' :
        if branch.voiceenabled == False :
            error = 'Voice is not enabled.'
            
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

    counterstatus = None
    if error == '' :
        counterstatus = CounterStatus.objects.get(id=counterstatus_id)
        if counterstatus is None:
            error = 'Counter Status not found.'

    if error == '' : 
        lang_list = []
        for i in range(1,100):
            if branch.language1 == i:
                lang_list.append('[ENG]')
            if branch.language2 == i:
                lang_list.append('[CAN]')
            if branch.language3 == i:
                lang_list.append('[MAN]')
            if branch.language4 == i:
                lang_list.append('[POR]')
        # print('lang_list:', lang_list)

        # voice string
        voice_str = ''
        voice_oh_str = ''
        for c in tno:
            voice_str += '[' + c + '],'        
        voice_oh_str = voice_str.replace('[0]', '[O]')                
        # type sould be uppercase
        counter_voice =counterstatus.voice
        if counter_voice == None:
            counter_voice = ''
        voice_str = '[' + ttype.upper() + '],' + voice_str + counter_voice
        voice_oh_str = '[' + ttype.upper() + '],' + voice_oh_str + counter_voice

        # volume
        volume = branch.voice_volume
        if volume <= 100 and volume >= 0:
            json_tx = {
                'cmd':'vol',
                'data': volume
            }
            send(json_tx)

        # play effect sound
        if len(lang_list) > 0:
            if branch.before_enabled == True:
                sound = branch.before_sound
                if sound != '' or sound != None:
                    json_tx ={
                        'cmd':'voice',
                        'data': {
                                'lang': '[SOUND]',
                                'voice_str': sound,
                                }
                    }
                    send(json_tx)
        # play voice
        for lang in lang_list:
            json_tx = {
                    'cmd':'voice',
                    'data':
                    {
                    'lang': lang,
                    'voice_str': voice_str,
                    }
                }
            if branch.O_Replace_Zero == True and lang == '[ENG]':
                json_tx = {
                    'cmd':'voice',
                    'data':
                    {
                    'lang': lang,
                    'voice_str': voice_oh_str,
                    }
                }
            send(json_tx)
            # str_tx = json.dumps(json_tx)

            # context = {
            # 'type':'broadcast_message',
            # 'tx': str_tx,
            # }
            
            # channel_layer = get_channel_layer()
            # channel_group_name = 'voice830_' + bcode + '_' + countertypename
            # logger.info('channel_group_name:' + channel_group_name + ' sending data -> Channel_Layer:' + str(channel_layer)),
            # try:
            #     async_to_sync (channel_layer.group_send)(channel_group_name, context)
            #     logger.info('...Done')
            # except Exception as e:
            #     # error_e = 'WS send voice Error:' + str(e)
            #     logger.error('...ERROR:Redis Server is down!')
        # play effect sound after voice
        if len(lang_list) > 0:
            if branch.after_enabled == True:
                sound = branch.after_sound
                if sound != '' or sound != None:
                    json_tx ={
                        'cmd':'voice',
                        'data': {
                                'lang': '[SOUND]',
                                'voice_str': sound,
                                }
                    }
                    send(json_tx)                
    if error != '':
        error_e = 'WS send voice830 Error:' + error
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
    if error == '' :
        if branch.voiceenabled == False :
            error = 'Voice is not enabled.'
            
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
    #     "tickettime_local": "23:06:53 2023-03-17",
    #     "tickettime_local_short": "23:06:53 03-17",
    #     "tickettime_local_date": "2023-03-17",
    #     "tickettime_local_time": "23:06:53",
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
        temp_time = funUTCtoLocal(ticket.tickettime, ticket.branch.timezone)
        tickettime_local = temp_time.strftime('%H:%M:%S %Y-%m-%d')
        tickettime_local_short = temp_time.strftime('%H:%M:%S %m-%d')
        tickettime_local_date = temp_time.strftime('%Y-%m-%d')
        tickettime_local_time = temp_time.strftime('%H:%M:%S')

        json_tx = {
            'cmd': cmd,
            'lastupdate': str_now,
            'data': {
                'tickettype' : ticket.tickettype,
                'ticketnumber' : ticket.ticketnumber,
                'tickettime' : stickettime,
                'tickettime_local' : tickettime_local,
                'tickettime_local_short' : tickettime_local_short,
                'tickettime_local_date' : tickettime_local_date,
                'tickettime_local_time' : tickettime_local_time,
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

    

  