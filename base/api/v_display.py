import json
from django.core import serializers
from datetime import datetime, timezone, timedelta
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
# from django.utils import timezone
from django.db.models import Q
from .views import setting_APIlogEnabled, visitor_ip_address, loginapi, funUTCtoLocal, counteractive, checkuser

from base.models import APILog, Branch, CounterStatus, CounterType, DisplayAndVoice, Setting, TicketFormat, TicketTemp, TicketRoute, TicketData, TicketLog, CounterLoginLog, UserProfile, lcounterstatus
from .serializers import displaylistSerivalizer, displaywaitlistSerivalizer, voicelistSerivalizer, lastDisplaySerivalizer
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
       
  
# http://127.0.0.1:8000/api/display5/?app=web&version=8&branchcode=KB&countername=Reception
# version 8.3.0 and above, add :
# "vert_showcounter": true,
# "vert_showlatest": true,
# "vert_latestpagehold": 10,
# "showcounter": true,
# "showlatest": true,
# "latestpagehold": 6
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def getDisplay5(request):

    status = dict({})
    msg = dict({})
    context = dict({})

    # rx_username = request.GET.get('username') if request.GET.get('username') != None else ''
    # rx_password = request.GET.get('password') if request.GET.get('password') != None else ''
    # rx_token = request.GET.get('token') if request.GET.get('token') != None else ''
    rx_app = request.GET.get('app') if request.GET.get('app') != None else ''
    rx_version = request.GET.get('version') if request.GET.get('version') != None else ''
    rx_bcode = request.GET.get('branchcode') if request.GET.get('branchcode') != None else ''
    rx_countername = request.GET.get('countername') if request.GET.get('countername') != None else ''



    #datetime_now = datetime.utcnow()
    datetime_now =datetime.now(timezone.utc)

   
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


    # check user
    if status == dict({}) :
        error, user = checkuser(request.user, branch, '')
        if error !='OK' :
            status = dict({'status': 'Error'})
            msg =  dict({'msg':error})   

    if status == dict({}) :

        servertime = dict({'servertime': datetime_now})
        scrollingtext = dict({'scroll' : countertype.displayscrollingtext})

        vert_showcounter = dict({'vert_showcounter' : countertype.vert_showcounter})
        vert_showlatest = dict({'vert_showlatest' : countertype.vert_showlatest})
        vert_latestpagehold = dict({'vert_latestpagehold' : countertype.vert_latestpagehold})
        showcounter = dict({'showcounter' : countertype.showcounter})
        showlatest = dict({'showlatest' : countertype.showlatest})
        latestpagehold = dict({'latestpagehold' : countertype.latestpagehold})

        pars = servertime | scrollingtext | vert_showcounter | vert_showlatest | vert_latestpagehold | showcounter | showlatest | latestpagehold


        displaylist = DisplayAndVoice.objects.filter (branch=branch, countertype=countertype).order_by('-displaytime')[:5]
        serializers = displaylistSerivalizer(displaylist, many=True)

        context = dict({'ticketlist':serializers.data})
        context = pars | context
        status = dict({'status': 'OK'})

    
    output = status | msg | context
    return Response(output)    

def newdisplayvoice(branch, countertype, counternumber, tickettemp, displaytime, user):
    # find number of waiting
    # ticketobj = TicketTemp.objects.filter(Q(branch=branch) & Q(tickettype=tickettemp.tickettype) & Q(countertype=countertype) & Q(status=lcounterstatus[0]) & Q(locked=False))    
    
    # # for recall a ticket , check if the ticket is in the DisplayAndVoice
    # dvobj = DisplayAndVoice.objects.filter(Q(tickettemp=tickettemp))
    # print (str(dvobj.count()))
    # if dvobj.count() == 0 :
    #     DisplayAndVoice.objects.create(
    #         branch = branch,
    #         countertype = countertype,
    #         counternumber = counternumber,
    #         tickettemp = tickettemp,
    #         displaytime = displaytime,
    #         user = user,
    #         flashtime = branch.displayflashtime,
    #     )
    # elif dvobj.count() >= 1 :
    #     dvobj.delete()
    #     print (str(dvobj.count()))
    #     DisplayAndVoice.objects.create(
    #         branch = branch,
    #         countertype = countertype,
    #         counternumber = counternumber,
    #         tickettemp = tickettemp,
    #         displaytime = displaytime,
    #         user = user,
    #         flashtime = branch.displayflashtime,
    #     )
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
        tr.displasttickettype = tickettemp.tickettype  
        tr.displastticketnumber = tickettemp.ticketnumber
        tr.displastcounter = counternumber
        tr.save()

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def getVoice(request):

    status = dict({})
    msg = dict({})
    context = dict({})

    # rx_username = request.GET.get('username') if request.GET.get('username') != None else ''
    # rx_password = request.GET.get('password') if request.GET.get('password') != None else ''
    # rx_token = request.GET.get('token') if request.GET.get('token') != None else ''
    rx_app = request.GET.get('app') if request.GET.get('app') != None else ''
    rx_version = request.GET.get('version') if request.GET.get('version') != None else ''
    rx_bcode = request.GET.get('branchcode') if request.GET.get('branchcode') != None else ''
    rx_countername = request.GET.get('countername') if request.GET.get('countername') != None else ''



    #datetime_now = datetime.utcnow()
    datetime_now =datetime.now(timezone.utc)

   
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



    # check user
    if status == dict({}) :
        error, user = checkuser(request.user, branch, '')
        if error !='OK' :
            status = dict({'status': 'Error'})
            msg =  dict({'msg':error})   

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
@permission_classes([IsAuthenticated])
def getWaiting(request):

    status = dict({})
    msg = dict({})
    context = dict({})

    # rx_username = request.GET.get('username') if request.GET.get('username') != None else ''
    # rx_password = request.GET.get('password') if request.GET.get('password') != None else ''
    # rx_token = request.GET.get('token') if request.GET.get('token') != None else ''
    rx_app = request.GET.get('app') if request.GET.get('app') != None else ''
    rx_version = request.GET.get('version') if request.GET.get('version') != None else ''
    rx_bcode = request.GET.get('branchcode') if request.GET.get('branchcode') != None else ''
    rx_countername = request.GET.get('countername') if request.GET.get('countername') != None else ''



    #datetime_now = datetime.utcnow()
    datetime_now =datetime.now(timezone.utc)

   
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


    # check user
    if status == dict({}) :
        error, user = checkuser(request.user, branch, '')
        if error !='OK' :
            status = dict({'status': 'Error'})
            msg =  dict({'msg':error})

    

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


# version 8.3.0 and above, add :
# "vert_showcounter": true,
# "vert_showlatest": true,
# "vert_latestpagehold": 10,
# "showcounter": true,
# "showlatest": true,
# "latestpagehold": 6
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def getDisplay(request):

    status = dict({})
    msg = dict({})
    context = dict({})

    # rx_username = request.GET.get('username') if request.GET.get('username') != None else ''
    # rx_password = request.GET.get('password') if request.GET.get('password') != None else ''
    # rx_token = request.GET.get('token') if request.GET.get('token') != None else ''
    rx_app = request.GET.get('app') if request.GET.get('app') != None else ''
    rx_version = request.GET.get('version') if request.GET.get('version') != None else ''
    rx_bcode = request.GET.get('branchcode') if request.GET.get('branchcode') != None else ''
    rx_countername = request.GET.get('countername') if request.GET.get('countername') != None else ''



    #datetime_now = datetime.utcnow()
    datetime_now =datetime.now(timezone.utc)

   
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


    # check user
    if status == dict({}) :
        error, user = checkuser(request.user, branch, '')
        if error !='OK' :
            status = dict({'status': 'Error'})
            msg =  dict({'msg':error})   

    if status == dict({}) :

        starttime = datetime_now + timedelta(minutes=-displaylist_x_mins)

        servertime = dict({'servertime': datetime_now})
        scrollingtext = dict({'scrollingtext' : countertype.displayscrollingtext})
        vert_showcounter = dict({'vert_showcounter' : countertype.vert_showcounter})
        vert_showlatest = dict({'vert_showlatest' : countertype.vert_showlatest})
        vert_latestpagehold = dict({'vert_latestpagehold' : countertype.vert_latestpagehold})
        showcounter = dict({'showcounter' : countertype.showcounter})
        showlatest = dict({'showlatest' : countertype.showlatest})
        latestpagehold = dict({'latestpagehold' : countertype.latestpagehold})

        msg = servertime | scrollingtext | vert_showcounter | vert_showlatest | vert_latestpagehold | showcounter | showlatest | latestpagehold

        displaylist = DisplayAndVoice.objects.filter (branch=branch, countertype=countertype, displaytime__range=[starttime, datetime_now] )
        serializers  = displaylistSerivalizer(displaylist, many=True)
        context = dict({'data':serializers.data})
        status = dict({'status': 'OK'})

    
    output = status | msg | context
    return Response(output)



@api_view(['GET'])
@permission_classes([IsAuthenticated])
def getLastDisplay(request):

    status = dict({})
    msg = dict({})
    context = dict({})

    # rx_username = request.GET.get('username') if request.GET.get('username') != None else ''
    # rx_password = request.GET.get('password') if request.GET.get('password') != None else ''
    # rx_token = request.GET.get('token') if request.GET.get('token') != None else ''
    rx_app = request.GET.get('app') if request.GET.get('app') != None else ''
    rx_version = request.GET.get('version') if request.GET.get('version') != None else ''
    rx_bcode = request.GET.get('branchcode') if request.GET.get('branchcode') != None else ''
    rx_countername = request.GET.get('countername') if request.GET.get('countername') != None else ''



    #datetime_now = datetime.utcnow()
    datetime_now =datetime.now(timezone.utc)

   
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




    # check user
    if status == dict({}) :
        error, user = checkuser(request.user, branch, '')
        if error !='OK' :
            status = dict({'status': 'Error'})
            msg =  dict({'msg':error})



    if status == dict({}) :

        starttime = datetime_now + timedelta(minutes=-displaylist_x_mins)

        servertime = dict({'servertime': datetime_now})
        scrollingtext = dict({'scroll' : countertype.displayscrollingtext})

        msg = servertime | scrollingtext

        displaylist = TicketRoute.objects.filter (branch=branch, countertype=countertype )
        serializers  = lastDisplaySerivalizer(displaylist, many=True)
        context = dict({'ticketlist':serializers.data})
        status = dict({'status': 'OK'})

    
    output = status | msg | context
    return Response(output)