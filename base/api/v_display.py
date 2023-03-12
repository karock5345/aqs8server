import json
from django.core import serializers
from datetime import datetime, timedelta
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.utils import timezone
from django.db.models import Q
from .views import setting_APIlogEnabled, visitor_ip_address, loginapi, funUTCtoLocal, counteractive

from base.models import APILog, Branch, CounterStatus, CounterType, DisplayAndVoice, Setting, TicketFormat, TicketTemp, TicketRoute, TicketData, TicketLog, CounterLoginLog, UserProfile, lcounterstatus
from .serializers import displaylistSerivalizer, displaywaitlistSerivalizer, voicelistSerivalizer, lastDisplaySerivalizer, webdisplaylistSerivalizer
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import asyncio

# displaylist only show within x mins, details : the Displaylist is too long, can not give full list to display app.
displaylist_x_mins = 3
# default_bcode = 'RVD15'
# default_countername = 'Counter'
# default_bcode = 'KB'
# default_countername = 'Reception'

# async def send_message_to_group(group_name, data):
#     channel_layer = get_channel_layer()
#     await async_to_sync(channel_layer.group_send)(
#         group_name,
#         data
#     )
       
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
        if countertype == None :
            displaylist = DisplayAndVoice.objects.filter (branch=branch).order_by('-displaytime')[:5]
        else:
            displaylist = DisplayAndVoice.objects.filter (branch=branch, countertype=countertype).order_by('-displaytime')[:5]
        wdserializers  = webdisplaylistSerivalizer(displaylist, many=True)

        context = {
        'type':'broadcast_message',
        'lastupdate' : str_now,
        'ticketlist' : wdserializers.data,
        }

    else :
        context = {
        'type':'broadcast_message',
        'lastupdate' : str_now,
        'errormsg' : error,
        }

    
    channel_layer = get_channel_layer()
    channel_group_name = 'webtv_' + bcode + '_' + countertypename
    print('channel_group_name:' + channel_group_name + ' sending data -> Channel_Layer:' + str(channel_layer)),
    try:
        async_to_sync (channel_layer.group_send)(channel_group_name, context)
        print('...Done')
    except:
        print('...ERROR:Redis Server is down!')
    
    
    

def newdisplayvoice(branch, countertype, counternumber, tickettemp, displaytime, user):
    # find number of waiting
    # ticketobj = TicketTemp.objects.filter(Q(branch=branch) & Q(tickettype=tickettemp.tickettype) & Q(countertype=countertype) & Q(status=lcounterstatus[0]) & Q(locked=False))    
    
    DisplayAndVoice.objects.create(
        branch = branch,
        countertype = countertype,
        counternumber = counternumber,
        tickettemp = tickettemp,
        displaytime = displaytime,
        user = user,
        flashtime = branch.displayflashtime,
    )

    tr_obj = TicketRoute.objects.filter(branch=branch, tickettype=tickettemp.tickettype, countertype=countertype)
    if tr_obj.count() == 1 :
        tr = tr_obj[0]
        tr.waiting = tr.waiting +1
        tr.displasttickettype = tickettemp.tickettype  
        tr.displastticketnumber = tickettemp.ticketnumber
        tr.displastcounter = counternumber
        tr.save()

@api_view(['GET'])
def getVoice(request):

    status = dict({})
    msg = dict({})
    context = dict({})

    rx_username = request.GET.get('username') if request.GET.get('username') != None else ''
    rx_password = request.GET.get('password') if request.GET.get('password') != None else ''
    rx_token = request.GET.get('token') if request.GET.get('token') != None else ''
    rx_app = request.GET.get('app') if request.GET.get('app') != None else ''
    rx_version = request.GET.get('version') if request.GET.get('version') != None else ''
    rx_bcode = request.GET.get('branchcode') if request.GET.get('branchcode') != None else ''
    rx_countername = request.GET.get('countername') if request.GET.get('countername') != None else ''



    #datetime_now = datetime.utcnow()
    datetime_now =timezone.now()

   
    # check input
    branch = None
    if status == dict({}) :
        if rx_bcode == '' :
            status = dict({'status': 'Error'})
            msg =  dict({'msg':'No branch code'})
        else :
            # check branch        
            branchobj = Branch.objects.filter( Q(bcode=rx_bcode) )
            if branchobj.count() != 1:
                # branch not found
                status = dict({'status': 'Error'})
                msg =  dict({'msg':'Branch not found'})   
            else:
                branch = branchobj[0]        

    if status == dict({}) :
        if branch.voiceenabled == False :
            status = dict({'status': 'Error'})
            msg =  dict({'msg':'Voice function disabled'})

    if status == dict({}) :
        if rx_countername == '' :
            status = dict({'status': 'Error'})
            msg =  dict({'msg':'No counter name'})  

    if status == dict({}) :
        # get the Counter type
        ctypeobj = CounterType.objects.filter( Q(branch=branch) & Q(name=rx_countername) )
        if not(ctypeobj.count() > 0) :
            status = dict({'status': 'Error'})
            msg =  dict({'msg':'Counter Type not found'}) 
        else:
            countertype = ctypeobj[0]

    # Save Api Log
    if setting_APIlogEnabled(branch) == True :
        APILog.objects.create(
            logtime=datetime_now,
            requeststr = request.build_absolute_uri() ,
            ip = visitor_ip_address(request),
            app = rx_app,
            version = rx_version,
            logtext = 'API call : Voice API',
        )




    if status == dict({}) :
        
        loginreply, user = loginapi(request , rx_username, rx_password, rx_token, None)

        if loginreply != 'OK':
            status = dict({'status': 'Error'})
            msg =  dict({'msg':loginreply})    

    if status == dict({}) :

        starttime = datetime_now + timedelta(minutes=-displaylist_x_mins)

        servertime = dict({'servertime': datetime_now})
        lang1 = dict({'language1' : branch.language1})
        lang2 = dict({'language2' : branch.language2})
        lang3 = dict({'language3' : branch.language3})
        lang4 = dict({'language4' : branch.language4})

        msg = servertime | lang1 | lang2 | lang3 | lang4

        voicelist = DisplayAndVoice.objects.filter (branch=branch, countertype=countertype, displaytime__range=[starttime, datetime_now] )
        serializers  = voicelistSerivalizer(voicelist, many=True)
        context = dict({'data':serializers.data})
        status = dict({'status': 'OK'})

    
    output = status | msg | context
    return Response(output)







@api_view(['GET'])
def getWaiting(request):

    status = dict({})
    msg = dict({})
    context = dict({})

    rx_username = request.GET.get('username') if request.GET.get('username') != None else ''
    rx_password = request.GET.get('password') if request.GET.get('password') != None else ''
    rx_token = request.GET.get('token') if request.GET.get('token') != None else ''
    rx_app = request.GET.get('app') if request.GET.get('app') != None else ''
    rx_version = request.GET.get('version') if request.GET.get('version') != None else ''
    rx_bcode = request.GET.get('branchcode') if request.GET.get('branchcode') != None else ''
    rx_countername = request.GET.get('countername') if request.GET.get('countername') != None else ''



    #datetime_now = datetime.utcnow()
    datetime_now =timezone.now()

   
    # check input
    branch = None
    if status == dict({}) :
        if rx_bcode == '' :
            status = dict({'status': 'Error'})
            msg =  dict({'msg':'No branch code'})
        else :
            # check branch        
            branchobj = Branch.objects.filter( Q(bcode=rx_bcode) )
            if branchobj.count() != 1:
                # branch not found
                status = dict({'status': 'Error'})
                msg =  dict({'msg':'Branch not found'})   
            else:
                branch = branchobj[0]        

    if status == dict({}) :
        if branch.displayenabled == False :
            status = dict({'status': 'Error'})
            msg =  dict({'msg':'Display function disabled'})

    if status == dict({}) :
        if rx_countername == '' :
            status = dict({'status': 'Error'})
            msg =  dict({'msg':'No counter name'})  

    if status == dict({}) :
        # get the Counter type
        ctypeobj = CounterType.objects.filter( Q(branch=branch) & Q(name=rx_countername) )
        if not(ctypeobj.count() > 0) :
            status = dict({'status': 'Error'})
            msg =  dict({'msg':'Counter Type not found'}) 
        else:
            countertype = ctypeobj[0]

    # Save Api Log
    if setting_APIlogEnabled(branch) == True :
        APILog.objects.create(
            logtime=datetime_now,
            requeststr = request.build_absolute_uri() ,
            ip = visitor_ip_address(request),
            app = rx_app,
            version = rx_version,
            logtext = 'API call : Display API',
        )




    if status == dict({}) :
        
        loginreply, user = loginapi(request , rx_username, rx_password, rx_token, None)

        if loginreply != 'OK':
            status = dict({'status': 'Error'})
            msg =  dict({'msg':loginreply})    

    if status == dict({}) :


        servertime = dict({'servertime': datetime_now})
        scrollingtext = dict({'scrollingtext' : countertype.displayscrollingtext})

        msg = servertime | scrollingtext

        ticketroute = TicketRoute.objects.filter (branch=branch, countertype=countertype, )
        serializers  = displaywaitlistSerivalizer(ticketroute, many=True)
        context = dict({'data':serializers.data})
        status = dict({'status': 'OK'})

    
    output = status | msg | context
    return Response(output)

@api_view(['GET'])
def getDisplay(request):

    status = dict({})
    msg = dict({})
    context = dict({})

    rx_username = request.GET.get('username') if request.GET.get('username') != None else ''
    rx_password = request.GET.get('password') if request.GET.get('password') != None else ''
    rx_token = request.GET.get('token') if request.GET.get('token') != None else ''
    rx_app = request.GET.get('app') if request.GET.get('app') != None else ''
    rx_version = request.GET.get('version') if request.GET.get('version') != None else ''
    rx_bcode = request.GET.get('branchcode') if request.GET.get('branchcode') != None else ''
    rx_countername = request.GET.get('countername') if request.GET.get('countername') != None else ''



    #datetime_now = datetime.utcnow()
    datetime_now =timezone.now()

   
    # check input
    branch = None
    if status == dict({}) :
        if rx_bcode == '' :
            status = dict({'status': 'Error'})
            msg =  dict({'msg':'No branch code'})
        else :
            # check branch        
            branchobj = Branch.objects.filter( Q(bcode=rx_bcode) )
            if branchobj.count() != 1:
                # branch not found
                status = dict({'status': 'Error'})
                msg =  dict({'msg':'Branch not found'})   
            else:
                branch = branchobj[0]        

    if status == dict({}) :
        if branch.displayenabled == False :
            status = dict({'status': 'Error'})
            msg =  dict({'msg':'Display function disabled'})

    if status == dict({}) :
        if rx_countername == '' :
            status = dict({'status': 'Error'})
            msg =  dict({'msg':'No counter name'})  

    if status == dict({}) :
        # get the Counter type
        ctypeobj = CounterType.objects.filter( Q(branch=branch) & Q(name=rx_countername) )
        if not(ctypeobj.count() > 0) :
            status = dict({'status': 'Error'})
            msg =  dict({'msg':'Counter Type not found'}) 
        else:
            countertype = ctypeobj[0]

    # Save Api Log
    if setting_APIlogEnabled(branch) == True :
        APILog.objects.create(
            logtime=datetime_now,
            requeststr = request.build_absolute_uri() ,
            ip = visitor_ip_address(request),
            app = rx_app,
            version = rx_version,
            logtext = 'API call : Display API',
        )




    if status == dict({}) :
        
        loginreply, user = loginapi(request , rx_username, rx_password, rx_token, None)

        if loginreply != 'OK':
            status = dict({'status': 'Error'})
            msg =  dict({'msg':loginreply})    

    if status == dict({}) :

        starttime = datetime_now + timedelta(minutes=-displaylist_x_mins)

        servertime = dict({'servertime': datetime_now})
        scrollingtext = dict({'scrollingtext' : countertype.displayscrollingtext})

        msg = servertime | scrollingtext

        displaylist = DisplayAndVoice.objects.filter (branch=branch, countertype=countertype, displaytime__range=[starttime, datetime_now] )
        serializers  = displaylistSerivalizer(displaylist, many=True)
        context = dict({'data':serializers.data})
        status = dict({'status': 'OK'})

    
    output = status | msg | context
    return Response(output)



@api_view(['GET'])
def getLastDisplay(request):

    status = dict({})
    msg = dict({})
    context = dict({})

    rx_username = request.GET.get('username') if request.GET.get('username') != None else ''
    rx_password = request.GET.get('password') if request.GET.get('password') != None else ''
    rx_token = request.GET.get('token') if request.GET.get('token') != None else ''
    rx_app = request.GET.get('app') if request.GET.get('app') != None else ''
    rx_version = request.GET.get('version') if request.GET.get('version') != None else ''
    rx_bcode = request.GET.get('branchcode') if request.GET.get('branchcode') != None else ''
    rx_countername = request.GET.get('countername') if request.GET.get('countername') != None else ''



    #datetime_now = datetime.utcnow()
    datetime_now =timezone.now()

   
    # check input
    branch = None
    if status == dict({}) :
        if rx_bcode == '' :
            status = dict({'status': 'Error'})
            msg =  dict({'msg':'No branch code'})
        else :
            # check branch        
            branchobj = Branch.objects.filter( Q(bcode=rx_bcode) )
            if branchobj.count() != 1:
                # branch not found
                status = dict({'status': 'Error'})
                msg =  dict({'msg':'Branch not found'})   
            else:
                branch = branchobj[0]        

    if status == dict({}) :
        if branch.displayenabled == False :
            status = dict({'status': 'Error'})
            msg =  dict({'msg':'Display function disabled'})

    if status == dict({}) :
        if rx_countername == '' :
            status = dict({'status': 'Error'})
            msg =  dict({'msg':'No counter name'})  

    if status == dict({}) :
        # get the Counter type
        ctypeobj = CounterType.objects.filter( Q(branch=branch) & Q(name=rx_countername) )
        if not(ctypeobj.count() > 0) :
            status = dict({'status': 'Error'})
            msg =  dict({'msg':'Counter Type not found'}) 
        else:
            countertype = ctypeobj[0]

    # Save Api Log
    if setting_APIlogEnabled(branch) == True :
        APILog.objects.create(
            logtime=datetime_now,
            requeststr = request.build_absolute_uri() ,
            ip = visitor_ip_address(request),
            app = rx_app,
            version = rx_version,
            logtext = 'API call : Last Display API',
        )




    if status == dict({}) :
        
        loginreply, user = loginapi(request , rx_username, rx_password, rx_token, None)

        if loginreply != 'OK':
            status = dict({'status': 'Error'})
            msg =  dict({'msg':loginreply})    

    if status == dict({}) :

        starttime = datetime_now + timedelta(minutes=-displaylist_x_mins)

        servertime = dict({'servertime': datetime_now})
        scrollingtext = dict({'scrollingtext' : countertype.displayscrollingtext})

        msg = servertime | scrollingtext

        displaylist = TicketRoute.objects.filter (branch=branch, countertype=countertype )
        serializers  = lastDisplaySerivalizer(displaylist, many=True)
        context = dict({'data':serializers.data})
        status = dict({'status': 'OK'})

    
    output = status | msg | context
    return Response(output)