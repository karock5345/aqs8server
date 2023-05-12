from datetime import datetime
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db.models import Q
from .views import setting_APIlogEnabled, visitor_ip_address, loginapi_notoken, funUTCtoLocal, counteractive, checkuser
from .v_display import newdisplayvoice
from base.models import APILog, Branch, CounterStatus, CounterType, DisplayAndVoice, Setting, TicketFormat, TicketTemp, TicketRoute, TicketData, TicketLog, CounterLoginLog, UserProfile, lcounterstatus
from .serializers import waitinglistSerivalizer
from base.ws import wssendwebtv, wssendql, wsSendTicketStatus, wssendvoice
from .v_softkey_sub import *

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def postCounterGet(request):
# Counter get ticket by ticket number
# Request :
# 'POST /api/get/?username=xxx&password=xxx&token=xxx&app=xxx&version=xxx&branchcode=xxx&countertype=xxx&counternumber=xxx&tickettype=x&ticketnumber=xxx'
#
# Response :
# {
#    "status":"OK/Error",
#    "msg":"Ticket route not found",
# }
    status = dict({})
    msg = dict({})
    context = dict({})

    rx_username = request.GET.get('username') if request.GET.get('username') != None else ''
    # rx_password = request.GET.get('password') if request.GET.get('password') != None else ''
    # rx_token = request.GET.get('token') if request.GET.get('token') != None else ''
    rx_app = request.GET.get('app') if request.GET.get('app') != None else ''
    rx_version = request.GET.get('version') if request.GET.get('version') != None else ''
    rx_bcode = request.GET.get('branchcode') if request.GET.get('branchcode') != None else ''
    rx_countername = request.GET.get('countername') if request.GET.get('countername') != None else ''
    rx_counternumber = request.GET.get('counternumber') if request.GET.get('counternumber') != None else ''
    
    rx_ticketype = request.GET.get('tickettype') if request.GET.get('tickettype') != None else ''
    rx_ticketnumber = request.GET.get('ticketnumber') if request.GET.get('ticketnumber') != None else ''
#    rx_tickettime =request.GET.get('tickettime') if request.GET.get('tickettime') != None else ''

    datetime_now =timezone.now()
   
    # check input
    if status == dict({}) :
        if rx_countername == '' :
            status = dict({'status': 'Error'})
            msg =  dict({'msg':'No counter name'})  
    if status == dict({}) :
        if rx_counternumber == '' :
            status = dict({'status': 'Error'})
            msg =  dict({'msg':'No counter number'})  

    if status == dict({}) :
        branch = None
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
        if rx_ticketype == '' :
            status = dict({'status': 'Error'})
            msg =  dict({'msg':'No ticket type'})  
    if status == dict({}) :
        if rx_ticketnumber == '' :
            status = dict({'status': 'Error'})
            msg =  dict({'msg':'No ticket number'})  
    # if status == dict({}) :
    #     if rx_tickettime == '' :
    #         status = dict({'status': 'Error'})
    #         msg =  dict({'msg':'No ticket time'})                          

    # Save Api Log
    if setting_APIlogEnabled(branch) == True :
        APILog.objects.create(
            logtime=datetime_now,
            requeststr = request.build_absolute_uri() ,
            ip = visitor_ip_address(request),
            app = rx_app,
            version = rx_version,
            logtext = 'API call : Get Ticket',
        )


    # rx_username should be already login to counter
    if status == dict({}) :
        if rx_username == '' :
            status = dict({'status': 'Error'})
            msg =  dict({'msg':'No username'})
    # check user
    if status == dict({}) :
        error, user = checkuser(request.user, branch, rx_username)
        if error !='OK' :
            status = dict({'status': 'Error'})
            msg =  dict({'msg':error})

    if status == dict({}) :
        userp = None
        obj_userp = UserProfile.objects.filter(user__exact=user)
        if obj_userp.count() == 1 :
            userp = obj_userp[0]            
        if userp == None:
            status = dict({'status': 'Error'})
            msg =  dict({'msg':'User profile not found'})       
    if status == dict({}) :
        # get the Counter type
        ctypeobj = CounterType.objects.filter( Q(branch=branch) & Q(name=rx_countername) )
        if not(ctypeobj.count() > 0) :
            status = dict({'status': 'Error'})
            msg =  dict({'msg':'Counter Type not found'})  
    if status == dict({}) :
        countertype = ctypeobj[0]
        cstatusobj = CounterStatus.objects.filter( Q(countertype=countertype) & Q(counternumber=rx_counternumber) & Q(user=user))
        if not(cstatusobj.count() > 0) :
            status = dict({'status': 'Error'})
            msg =  dict({'msg':'Counter not found / User did not login'})  
    if status == dict({}) :
        counterstatus = cstatusobj[0]
        counterstatus.lastactive = datetime_now
        counterstatus.save()

        # check counter status
        if counterstatus.status != 'waiting' :
            status = dict({'status': 'Error'})
            msg =  dict({'msg':'Counter status is not WAITING'})  
        elif counterstatus.tickettemp != None :
            status = dict({'status': 'Error'})
            msg =  dict({'msg':'Counter status - have ticket'})  





    # if status == dict({}) :

    #     stickettime = ''        
    #     try:
    #         stickettime = str(datetime.strptime(rx_tickettime, '%Y-%m-%dT%H:%M:%S.%fZ'))
    #         rx_tickettime = datetime.strptime(rx_tickettime, '%Y-%m-%dT%H:%M:%S.%f%z' )
    #     except:
    #         stickettime = ''
    #     if stickettime == '' :
    #         try :
    #             stickettime = str(datetime.strptime(rx_tickettime, '%Y-%m-%dT%H:%M:%SZ' )) 
    #             rx_tickettime = datetime.strptime(rx_tickettime, '%Y-%m-%dT%H:%M:%S%z')
    #         except:
    #             stickettime = ''
    #             status = dict({'status': 'Error'})
    #             msg =  dict({'msg':'Ticket time format not correct. Should be : 2022-05-19T23:59:59.123456Z'}) 

    if status == dict({}) :
        status, msg, context = funCounterGet(rx_ticketype, rx_ticketnumber, user, branch, countertype, counterstatus, 'Ticket Get API : ', rx_app, rx_version, datetime_now)

        # websocket to web tv
        wssendwebtv(rx_bcode,countertype.name)




    output = status | msg | context
    return Response(output)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def postCounterVoid(request):
# Request :
# 'POST /api/void/?username=xxx&password=xxx&token=xxx&app=xxx&version=xxx&branchcode=xxx&countertype=xxx&counternumber=xxx&tickettype=x&ticketnumber=xxx&tickettime=xxx'
#
# Response :
# {
#    "status":"OK/Error",
#    "msg":"Ticket route not found",
# }
    status = dict({})
    msg = dict({})
    context = dict({})

    rx_username = request.GET.get('username') if request.GET.get('username') != None else ''
    # rx_password = request.GET.get('password') if request.GET.get('password') != None else ''
    rx_token = request.GET.get('token') if request.GET.get('token') != None else ''
    rx_app = request.GET.get('app') if request.GET.get('app') != None else ''
    rx_version = request.GET.get('version') if request.GET.get('version') != None else ''
    rx_bcode = request.GET.get('branchcode') if request.GET.get('branchcode') != None else ''
    rx_countername = request.GET.get('countername') if request.GET.get('countername') != None else ''
    rx_counternumber = request.GET.get('counternumber') if request.GET.get('counternumber') != None else ''
    
    rx_ticketype = request.GET.get('tickettype') if request.GET.get('tickettype') != None else ''
    rx_ticketnumber = request.GET.get('ticketnumber') if request.GET.get('ticketnumber') != None else ''
    rx_tickettime =request.GET.get('tickettime') if request.GET.get('tickettime') != None else ''

    datetime_now =timezone.now()
   
    # check input
    if status == dict({}) :
        if rx_countername == '' :
            status = dict({'status': 'Error'})
            msg =  dict({'msg':'No counter name'})  
    if status == dict({}) :
        if rx_counternumber == '' :
            status = dict({'status': 'Error'})
            msg =  dict({'msg':'No counter number'})  

    if status == dict({}) :
        branch = None
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
        if rx_ticketype == '' :
            status = dict({'status': 'Error'})
            msg =  dict({'msg':'No ticket type'})  
    if status == dict({}) :
        if rx_ticketnumber == '' :
            status = dict({'status': 'Error'})
            msg =  dict({'msg':'No ticket number'})  
    if status == dict({}) :
        if rx_tickettime == '' :
            status = dict({'status': 'Error'})
            msg =  dict({'msg':'No ticket time'})                          

    # Save Api Log
    if setting_APIlogEnabled(branch) == True :
        APILog.objects.create(
            logtime=datetime_now,
            requeststr = request.build_absolute_uri() ,
            ip = visitor_ip_address(request),
            app = rx_app,
            version = rx_version,
            logtext = 'API call : Void Ticket',
        )

    # rx_username should be already login to counter
    if status == dict({}) :
        if rx_username == '' :
            status = dict({'status': 'Error'})
            msg =  dict({'msg':'No username'})
    # check user
    if status == dict({}) :
        error, user = checkuser(request.user, branch, rx_username)
        if error !='OK' :
            status = dict({'status': 'Error'})
            msg =  dict({'msg':error})



    if status == dict({}) :
        userp = None
        obj_userp = UserProfile.objects.filter(user__exact=user)
        if obj_userp.count() == 1 :
            userp = obj_userp[0]            
        if userp == None:
            status = dict({'status': 'Error'})
            msg =  dict({'msg':'User profile not found'})      
    if status == dict({}) :
        # get the Counter type
        ctypeobj = CounterType.objects.filter( Q(branch=branch) & Q(name=rx_countername) )
        if not(ctypeobj.count() > 0) :
            status = dict({'status': 'Error'})
            msg =  dict({'msg':'Counter Type not found'})  
    if status == dict({}) :
        countertype = ctypeobj[0]
        cstatusobj = CounterStatus.objects.filter( Q(countertype=countertype) & Q(counternumber=rx_counternumber) & Q(user=user))
        if not(cstatusobj.count() > 0) :
            status = dict({'status': 'Error'})
            msg =  dict({'msg':'Counter not found / User did not login'})  
    if status == dict({}) :
        counterstatus = cstatusobj[0]
        counterstatus.lastactive = datetime_now
        counterstatus.save()



    if status == dict({}) :

        stickettime = ''        
        try:
            stickettime = str(datetime.strptime(rx_tickettime, '%Y-%m-%dT%H:%M:%S.%fZ'))
            rx_tickettime = datetime.strptime(rx_tickettime, '%Y-%m-%dT%H:%M:%S.%f%z' )
        except:
            stickettime = ''
        if stickettime == '' :
            try :
                stickettime = str(datetime.strptime(rx_tickettime, '%Y-%m-%dT%H:%M:%SZ' )) 
                rx_tickettime = datetime.strptime(rx_tickettime, '%Y-%m-%dT%H:%M:%S%z')
            except:
                stickettime = ''
                status = dict({'status': 'Error'})
                msg =  dict({'msg':'Ticket time format not correct. Should be : 2022-05-19T23:59:59.123456Z'}) 

    tickett = None
    if status == dict({}) :
        obj_t = TicketTemp.objects.filter(
            tickettype=rx_ticketype,
            ticketnumber=rx_ticketnumber,
            tickettime=rx_tickettime,
            branch=branch,
            status='waiting',
            locked=False)
        if obj_t.count() == 1 :
            tickett = obj_t[0]
        if tickett == None:
            status = dict({'status': 'Error'})
            msg =  dict({'msg':'Ticket not found'}) 

      
        
    if status == dict({}) :
        td = None
        obj_td = TicketData.objects.filter(
            tickettemp=tickett,
            countertype=countertype,
            step=tickett.step,
            branch=branch,
        )
        if obj_td.count() != 1 :
            status = dict({'status': 'Error'})
            msg =  dict({'msg':'TicketData not found ' })
        else:
            td = obj_td[0]
            if td.starttime == None:
                status = dict({'status': 'Error'})
                msg =  dict({'msg':'Ticket time is NONE' })


    if status == dict({}) :
        funVoid(user, tickett, td, datetime_now)

        
        # # update ticket 
        # tickett.user = user
        # tickett.status = 'void'
        # tickett.save()

        # # update ticketdata db
        # td.voidtime = datetime_now
        # td.voiduser = user
        # time_diff = datetime_now - td.starttime
        # tsecs = int(time_diff.total_seconds())
        # td.waitingperiod = tsecs
        # td.save()


        # add ticketlog
        TicketLog.objects.create(
            tickettemp=tickett,
            logtime=datetime_now,
            app = rx_app,
            version = rx_version,
            logtext='Ticket Void API : '  + branch.bcode + '_' + tickett.tickettype + '_'+ tickett.ticketnumber + '_' + datetime_now.strftime('%Y-%m-%dT%H:%M:%S.%fZ') ,
            user=user,
        )



        status = dict({'status': 'OK'})
        msg =  dict({'msg':'Ticket voided.'})  




    output = status | msg | context
    return Response(output)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def postCounterDone(request):
# Request :
# 'POST /api/done/?username=xxx&password=xxx&token=xxx&app=xxx&version=xxx&branchcode=xxx&countertype=xxx&counternumber=xxx&tickettype=x&ticketnumber=xxx&tickettime=xxx'
#
# Response :
# {
#    "status":"OK/Error",
#    "msg":"Ticket route not found",
# }
    status = dict({})
    msg = dict({})
    context = dict({})

    rx_username = request.GET.get('username') if request.GET.get('username') != None else ''
    # rx_password = request.GET.get('password') if request.GET.get('password') != None else ''
    # rx_token = request.GET.get('token') if request.GET.get('token') != None else ''
    rx_app = request.GET.get('app') if request.GET.get('app') != None else ''
    rx_version = request.GET.get('version') if request.GET.get('version') != None else ''
    rx_bcode = request.GET.get('branchcode') if request.GET.get('branchcode') != None else ''
    rx_countername = request.GET.get('countername') if request.GET.get('countername') != None else ''
    rx_counternumber = request.GET.get('counternumber') if request.GET.get('counternumber') != None else ''
    
    rx_ticketype = request.GET.get('tickettype') if request.GET.get('tickettype') != None else ''
    rx_ticketnumber = request.GET.get('ticketnumber') if request.GET.get('ticketnumber') != None else ''
    rx_tickettime = request.GET.get('tickettime') if request.GET.get('tickettime') != None else ''

    datetime_now =timezone.now()
   
    # check input
    if status == dict({}) :
        if rx_countername == '' :
            status = dict({'status': 'Error'})
            msg =  dict({'msg':'No counter name'})  
    if status == dict({}) :
        if rx_counternumber == '' :
            status = dict({'status': 'Error'})
            msg =  dict({'msg':'No counter number'})  

    if status == dict({}) :
        branch = None
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
        if rx_ticketype == '' :
            status = dict({'status': 'Error'})
            msg =  dict({'msg':'No ticket type'})  
    if status == dict({}) :
        if rx_ticketnumber == '' :
            status = dict({'status': 'Error'})
            msg =  dict({'msg':'No ticket number'})  
    if status == dict({}) :
        if rx_tickettime == '' :
            status = dict({'status': 'Error'})
            msg =  dict({'msg':'No ticket time'})                          

    # Save Api Log
    if setting_APIlogEnabled(branch) == True :
        APILog.objects.create(
            logtime=datetime_now,
            requeststr = request.build_absolute_uri() ,
            ip = visitor_ip_address(request),
            app = rx_app,
            version = rx_version,
            logtext = 'API call : Counter waiting list',
        )



    # rx_username should be already login to counter
    if status == dict({}) :
        if rx_username == '' :
            status = dict({'status': 'Error'})
            msg =  dict({'msg':'No username'})
    # check user
    if status == dict({}) :
        error, user = checkuser(request.user, branch, rx_username)
        if error !='OK' :
            status = dict({'status': 'Error'})
            msg =  dict({'msg':error})
    
    
    

    if status == dict({}) :
        userp = None
        obj_userp = UserProfile.objects.filter(user__exact=user)
        if obj_userp.count() == 1 :
            userp = obj_userp[0]            
        if userp == None:
            status = dict({'status': 'Error'})
            msg =  dict({'msg':'User profile not found'})       
    if status == dict({}) :
        # get the Counter type
        ctypeobj = CounterType.objects.filter( Q(branch=branch) & Q(name=rx_countername) )
        if not(ctypeobj.count() > 0) :
            status = dict({'status': 'Error'})
            msg =  dict({'msg':'Counter Type not found'})  
    if status == dict({}) :
        countertype = ctypeobj[0]
        cstatusobj = CounterStatus.objects.filter( Q(countertype=countertype) & Q(counternumber=rx_counternumber) & Q(user=user))
        if not(cstatusobj.count() > 0) :
            status = dict({'status': 'Error'})
            msg =  dict({'msg':'Counter not found / User did not login'})  
    if status == dict({}) :
        counterstatus = cstatusobj[0]
        counterstatus.lastactive = datetime_now
        counterstatus.save()

        # check counter status
        if counterstatus.status != 'processing' :
            status = dict({'status': 'Error'})
            msg =  dict({'msg':'Counter status is not Processing'})  
        elif counterstatus.tickettemp == None :
            status = dict({'status': 'Error'})
            msg =  dict({'msg':'Counter status - no ticket'})  
    if status == dict({}) :
        if counterstatus.tickettemp.tickettype != rx_ticketype :
            status = dict({'status': 'Error'})
            msg =  dict({'msg':'Counter status - ticket is not same'})  
    if status == dict({}) :
        if counterstatus.tickettemp.ticketnumber != rx_ticketnumber :
            status = dict({'status': 'Error'})
            msg =  dict({'msg':'Counter status - ticket is not same'})  
    if status == dict({}) :

        stickettime = ''        
        try:
            stickettime = str(datetime.strptime(rx_tickettime, '%Y-%m-%dT%H:%M:%S.%fZ'))
            rx_tickettime = datetime.strptime(rx_tickettime, '%Y-%m-%dT%H:%M:%S.%f%z' )
        except:
            stickettime = ''
        if stickettime == '' :
            try :
                stickettime = str(datetime.strptime(rx_tickettime, '%Y-%m-%dT%H:%M:%SZ' )) 
                rx_tickettime = datetime.strptime(rx_tickettime, '%Y-%m-%dT%H:%M:%S%z')
            except:
                stickettime = ''
                status = dict({'status': 'Error'})
                msg =  dict({'msg':'Ticket time format not correct. Should be : 2022-05-19T23:59:59.123456Z'}) 
                        
    if status == dict({}) :
        ttime = counterstatus.tickettemp.tickettime
        if ttime != rx_tickettime :            
            status = dict({'status': 'Error'})
            msg =  dict({'msg':'Counter status - ticket time is not same ' 
            + str(ttime.year)
            +'-'
            + str(ttime.month)
            +'-'
            + str(ttime.day)
            +'T'
            + str(ttime.hour)
            +':'
            + str(ttime.minute)
            +':'
            + str(ttime.second)
            +'.'
            + str(ttime.microsecond)
            +'Z'
              })            
        
    if status == dict({}) :
        status, msg = funCounterComplete(user, branch, countertype, counterstatus, 'Ticket Done API : ', rx_app, rx_version, datetime_now)

    output = status | msg | context
    return Response(output)



@api_view(['POST'])
@permission_classes([IsAuthenticated])
def postCounterMiss(request):
# Request :
# 'POST /api/miss/?username=xxx&password=xxx&token=xxx&app=xxx&version=xxx&branchcode=xxx&countertype=xxx&counternumber=xxx&tickettype=x&ticketnumber=xxx&tickettime=xxx'
#
# Response :
# {
#    "status":"OK/Error",
#    "msg":"Ticket route not found",
# }
    status = dict({})
    msg = dict({})
    context = dict({})

    rx_username = request.GET.get('username') if request.GET.get('username') != None else ''
    # rx_password = request.GET.get('password') if request.GET.get('password') != None else ''
    # rx_token = request.GET.get('token') if request.GET.get('token') != None else ''
    rx_app = request.GET.get('app') if request.GET.get('app') != None else ''
    rx_version = request.GET.get('version') if request.GET.get('version') != None else ''
    rx_bcode = request.GET.get('branchcode') if request.GET.get('branchcode') != None else ''
    rx_countername = request.GET.get('countername') if request.GET.get('countername') != None else ''
    rx_counternumber = request.GET.get('counternumber') if request.GET.get('counternumber') != None else ''
    
    rx_ticketype = request.GET.get('tickettype') if request.GET.get('tickettype') != None else ''
    rx_ticketnumber = request.GET.get('ticketnumber') if request.GET.get('ticketnumber') != None else ''
    rx_tickettime = request.GET.get('tickettime') if request.GET.get('tickettime') != None else ''

    datetime_now =timezone.now()
   
    # check input
    if status == dict({}) :
        if rx_countername == '' :
            status = dict({'status': 'Error'})
            msg =  dict({'msg':'No counter name'})  
    if status == dict({}) :
        if rx_counternumber == '' :
            status = dict({'status': 'Error'})
            msg =  dict({'msg':'No counter number'})  

    if status == dict({}) :
        branch = None
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
        if rx_ticketype == '' :
            status = dict({'status': 'Error'})
            msg =  dict({'msg':'No ticket type'})  
    if status == dict({}) :
        if rx_ticketnumber == '' :
            status = dict({'status': 'Error'})
            msg =  dict({'msg':'No ticket number'})  
    if status == dict({}) :
        if rx_tickettime == '' :
            status = dict({'status': 'Error'})
            msg =  dict({'msg':'No ticket time'})                          

    # Save Api Log
    if setting_APIlogEnabled(branch) == True :
        APILog.objects.create(
            logtime=datetime_now,
            requeststr = request.build_absolute_uri() ,
            ip = visitor_ip_address(request),
            app = rx_app,
            version = rx_version,
            logtext = 'API call : Counter waiting list',
        )


    # rx_username should be already login to counter
    if status == dict({}) :
        if rx_username == '' :
            status = dict({'status': 'Error'})
            msg =  dict({'msg':'No username'})
    # check user
    if status == dict({}) :
        error, user = checkuser(request.user, branch, rx_username)
        if error !='OK' :
            status = dict({'status': 'Error'})
            msg =  dict({'msg':error})
    
    
    

    if status == dict({}) :
        userp = None
        obj_userp = UserProfile.objects.filter(user__exact=user)
        if obj_userp.count() == 1 :
            userp = obj_userp[0]            
        if userp == None:
            status = dict({'status': 'Error'})
            msg =  dict({'msg':'User profile not found'})      
    if status == dict({}) :
        # get the Counter type
        ctypeobj = CounterType.objects.filter( Q(branch=branch) & Q(name=rx_countername) )
        if not(ctypeobj.count() > 0) :
            status = dict({'status': 'Error'})
            msg =  dict({'msg':'Counter Type not found'})  
    if status == dict({}) :
        countertype = ctypeobj[0]
        cstatusobj = CounterStatus.objects.filter( Q(countertype=countertype) & Q(counternumber=rx_counternumber) & Q(user=user))
        if not(cstatusobj.count() > 0) :
            status = dict({'status': 'Error'})
            msg =  dict({'msg':'Counter not found / User did not login'})  
    if status == dict({}) :
        counterstatus = cstatusobj[0]
        counterstatus.lastactive = datetime_now
        counterstatus.save()

        # check counter status
        if counterstatus.status != 'calling' :
            status = dict({'status': 'Error'})
            msg =  dict({'msg':'Counter status is not CALLING'})  
        elif counterstatus.tickettemp == None :
            status = dict({'status': 'Error'})
            msg =  dict({'msg':'Counter status - no ticket'})  
    if status == dict({}) :
        if counterstatus.tickettemp.tickettype != rx_ticketype :
            status = dict({'status': 'Error'})
            msg =  dict({'msg':'Counter status - ticket is not same'})  
    if status == dict({}) :
        if counterstatus.tickettemp.ticketnumber != rx_ticketnumber :
            status = dict({'status': 'Error'})
            msg =  dict({'msg':'Counter status - ticket is not same'})  
    if status == dict({}) :

        stickettime = ''        
        try:
            stickettime = str(datetime.strptime(rx_tickettime, '%Y-%m-%dT%H:%M:%S.%fZ'))
            rx_tickettime = datetime.strptime(rx_tickettime, '%Y-%m-%dT%H:%M:%S.%f%z' )
        except:
            stickettime = ''
        if stickettime == '' :
            try :
                stickettime = str(datetime.strptime(rx_tickettime, '%Y-%m-%dT%H:%M:%SZ' )) 
                rx_tickettime = datetime.strptime(rx_tickettime, '%Y-%m-%dT%H:%M:%S%z')
            except:
                stickettime = ''
                status = dict({'status': 'Error'})
                msg =  dict({'msg':'Ticket time format not correct. Should be : 2022-05-19T23:59:59.123456Z'}) 
                        
    if status == dict({}) :
        ttime = counterstatus.tickettemp.tickettime
        if ttime != rx_tickettime :            
            status = dict({'status': 'Error'})
            msg =  dict({'msg':'Counter status - ticket time is not same ' 
            + str(ttime.year)
            +'-'
            + str(ttime.month)
            +'-'
            + str(ttime.day)
            +'T'
            + str(ttime.hour)
            +':'
            + str(ttime.minute)
            +':'
            + str(ttime.second)
            +'.'
            + str(ttime.microsecond)
            +'Z'
              })            
    if status == dict({}) :
        status, msg = funCounterMiss(user, branch, countertype, counterstatus, 'Ticket No Show API : ', rx_app, rx_version, datetime_now)
    
    output = status | msg | context
    return Response(output)



@api_view(['POST'])
@permission_classes([IsAuthenticated])
def postCounterProcess(request):
# Request :
# 'POST /api/process/?username=xxx&password=xxx&token=xxx&app=xxx&version=xxx&branchcode=xxx&countertype=xxx&counternumber=xxx&tickettype=x&ticketnumber=xxx&tickettime=xxx'
#
# Response :
# {
#    "status":"OK/Error",
#    "msg":"Ticket route not found",
# }
    status = dict({})
    msg = dict({})
    context = dict({})

    rx_username = request.GET.get('username') if request.GET.get('username') != None else ''
    # rx_password = request.GET.get('password') if request.GET.get('password') != None else ''
    # rx_token = request.GET.get('token') if request.GET.get('token') != None else ''
    rx_app = request.GET.get('app') if request.GET.get('app') != None else ''
    rx_version = request.GET.get('version') if request.GET.get('version') != None else ''
    rx_bcode = request.GET.get('branchcode') if request.GET.get('branchcode') != None else ''
    rx_countername = request.GET.get('countername') if request.GET.get('countername') != None else ''
    rx_counternumber = request.GET.get('counternumber') if request.GET.get('counternumber') != None else ''
    
    rx_ticketype = request.GET.get('tickettype') if request.GET.get('tickettype') != None else ''
    rx_ticketnumber = request.GET.get('ticketnumber') if request.GET.get('ticketnumber') != None else ''
    rx_tickettime = request.GET.get('tickettime') if request.GET.get('tickettime') != None else ''

    datetime_now =timezone.now()
   
    # check input
    if status == dict({}) :
        if rx_countername == '' :
            status = dict({'status': 'Error'})
            msg =  dict({'msg':'No counter name'})  
    if status == dict({}) :
        if rx_counternumber == '' :
            status = dict({'status': 'Error'})
            msg =  dict({'msg':'No counter number'})  

    if status == dict({}) :
        branch = None
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
        if rx_ticketype == '' :
            status = dict({'status': 'Error'})
            msg =  dict({'msg':'No ticket type'})  
    if status == dict({}) :
        if rx_ticketnumber == '' :
            status = dict({'status': 'Error'})
            msg =  dict({'msg':'No ticket number'})  
    if status == dict({}) :
        if rx_tickettime == '' :
            status = dict({'status': 'Error'})
            msg =  dict({'msg':'No ticket time'})                          

    # Save Api Log
    if setting_APIlogEnabled(branch) == True :
        APILog.objects.create(
            logtime=datetime_now,
            requeststr = request.build_absolute_uri() ,
            ip = visitor_ip_address(request),
            app = rx_app,
            version = rx_version,
            logtext = 'API call : Counter waiting list',
        )



    # rx_username should be already login to counter
    if status == dict({}) :
        if rx_username == '' :
            status = dict({'status': 'Error'})
            msg =  dict({'msg':'No username'})
    # check user
    if status == dict({}) :
        error, user = checkuser(request.user, branch, rx_username)
        if error !='OK' :
            status = dict({'status': 'Error'})
            msg =  dict({'msg':error})  
    
    
    if status == dict({}) :
        userp = None
        obj_userp = UserProfile.objects.filter(user__exact=user)
        if obj_userp.count() == 1 :
            userp = obj_userp[0]            
        if userp == None:
            status = dict({'status': 'Error'})
            msg =  dict({'msg':'User profile not found'})      
    if status == dict({}) :
        # get the Counter type
        ctypeobj = CounterType.objects.filter( Q(branch=branch) & Q(name=rx_countername) )
        if not(ctypeobj.count() > 0) :
            status = dict({'status': 'Error'})
            msg =  dict({'msg':'Counter Type not found'})  
    if status == dict({}) :
        countertype = ctypeobj[0]
        cstatusobj = CounterStatus.objects.filter( Q(countertype=countertype) & Q(counternumber=rx_counternumber) & Q(user=user))
        if not(cstatusobj.count() > 0) :
            status = dict({'status': 'Error'})
            msg =  dict({'msg':'Counter not found / User did not login'})  
    if status == dict({}) :
        counterstatus = cstatusobj[0]
        counterstatus.lastactive = datetime_now
        counterstatus.save()

        # check counter status
        if counterstatus.status != 'calling' :
            status = dict({'status': 'Error'})
            msg =  dict({'msg':'Counter status is not CALLING'})  
        elif counterstatus.tickettemp == None :
            status = dict({'status': 'Error'})
            msg =  dict({'msg':'Counter status - no ticket'})  
    if status == dict({}) :
        if counterstatus.tickettemp.tickettype != rx_ticketype :
            status = dict({'status': 'Error'})
            msg =  dict({'msg':'Counter status - ticket is not same'})  
    if status == dict({}) :
        if counterstatus.tickettemp.ticketnumber != rx_ticketnumber :
            status = dict({'status': 'Error'})
            msg =  dict({'msg':'Counter status - ticket is not same'})  
    if status == dict({}) :

        stickettime = ''        
        try:
            stickettime = str(datetime.strptime(rx_tickettime, '%Y-%m-%dT%H:%M:%S.%fZ'))
            rx_tickettime = datetime.strptime(rx_tickettime, '%Y-%m-%dT%H:%M:%S.%f%z' )
        except:
            stickettime = ''
        if stickettime == '' :
            try :
                stickettime = str(datetime.strptime(rx_tickettime, '%Y-%m-%dT%H:%M:%SZ' )) 
                rx_tickettime = datetime.strptime(rx_tickettime, '%Y-%m-%dT%H:%M:%S%z')
            except:
                stickettime = ''
                status = dict({'status': 'Error'})
                msg =  dict({'msg':'Ticket time format not correct. Should be : 2022-05-19T23:59:59.123456Z'}) 
                        
    if status == dict({}) :
        ttime = counterstatus.tickettemp.tickettime
        if ttime != rx_tickettime :            
            status = dict({'status': 'Error'})
            msg =  dict({'msg':'Counter status - ticket time is not same ' 
            + str(ttime.year)
            +'-'
            + str(ttime.month)
            +'-'
            + str(ttime.day)
            +'T'
            + str(ttime.hour)
            +':'
            + str(ttime.minute)
            +':'
            + str(ttime.second)
            +'.'
            + str(ttime.microsecond)
            +'Z'
              })            
    if status == dict({}) :
        status, msg = funCounterProcess(user, branch, countertype, counterstatus, 'Process ticket API : ', rx_app, rx_version, datetime_now)
    

    output = status | msg | context
    return Response(output)




@api_view(['POST'])
@permission_classes([IsAuthenticated])
def postCounterRecall(request):
# Request :
# 'POST /api/recall/?username=xxx&password=xxx&token=xxx&app=xxx&version=xxx&branchcode=xxx&countertype=xxx&counternumber=xxx&tickettype=x&ticketnumber=xxx&tickettime=xxx'
#
# Response :
# {
#    "status":"OK/Error",
#    "msg":"Ticket route not found",
# }
    status = dict({})
    msg = dict({})
    context = dict({})

    rx_username = request.GET.get('username') if request.GET.get('username') != None else ''
    # rx_password = request.GET.get('password') if request.GET.get('password') != None else ''
    # rx_token = request.GET.get('token') if request.GET.get('token') != None else ''
    rx_app = request.GET.get('app') if request.GET.get('app') != None else ''
    rx_version = request.GET.get('version') if request.GET.get('version') != None else ''
    rx_bcode = request.GET.get('branchcode') if request.GET.get('branchcode') != None else ''
    rx_countername = request.GET.get('countername') if request.GET.get('countername') != None else ''
    rx_counternumber = request.GET.get('counternumber') if request.GET.get('counternumber') != None else ''
    
    rx_ticketype = request.GET.get('tickettype') if request.GET.get('tickettype') != None else ''
    rx_ticketnumber = request.GET.get('ticketnumber') if request.GET.get('ticketnumber') != None else ''
    rx_tickettime = request.GET.get('tickettime') if request.GET.get('tickettime') != None else ''

    datetime_now =timezone.now()
   
    # check input
    if status == dict({}) :
        if rx_countername == '' :
            status = dict({'status': 'Error'})
            msg =  dict({'msg':'No counter name'})  
    if status == dict({}) :
        if rx_counternumber == '' :
            status = dict({'status': 'Error'})
            msg =  dict({'msg':'No counter number'})  

    if status == dict({}) :
        branch = None
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
        if rx_ticketype == '' :
            status = dict({'status': 'Error'})
            msg =  dict({'msg':'No ticket type'})  
    if status == dict({}) :
        if rx_ticketnumber == '' :
            status = dict({'status': 'Error'})
            msg =  dict({'msg':'No ticket number'})  
    if status == dict({}) :
        if rx_tickettime == '' :
            status = dict({'status': 'Error'})
            msg =  dict({'msg':'No ticket time'})                          

    # Save Api Log
    if setting_APIlogEnabled(branch) == True :
        APILog.objects.create(
            logtime=datetime_now,
            requeststr = request.build_absolute_uri() ,
            ip = visitor_ip_address(request),
            app = rx_app,
            version = rx_version,
            logtext = 'API call : Counter waiting list',
        )



    # rx_username should be already login to counter
    if status == dict({}) :
        if rx_username == '' :
            status = dict({'status': 'Error'})
            msg =  dict({'msg':'No username'})
    # check user
    if status == dict({}) :
        error, user = checkuser(request.user, branch, rx_username)
        if error !='OK' :
            status = dict({'status': 'Error'})
            msg =  dict({'msg':error})
    
    

    if status == dict({}) :
        userp = None
        obj_userp = UserProfile.objects.filter(user__exact=user)
        if obj_userp.count() == 1 :
            userp = obj_userp[0]            
        if userp == None:
            status = dict({'status': 'Error'})
            msg =  dict({'msg':'User profile not found'})        
    if status == dict({}) :
        # get the Counter type
        ctypeobj = CounterType.objects.filter( Q(branch=branch) & Q(name=rx_countername) )
        if not(ctypeobj.count() > 0) :
            status = dict({'status': 'Error'})
            msg =  dict({'msg':'Counter Type not found'})  
    if status == dict({}) :
        countertype = ctypeobj[0]
        cstatusobj = CounterStatus.objects.filter( Q(countertype=countertype) & Q(counternumber=rx_counternumber) & Q(user=user))
        if not(cstatusobj.count() > 0) :
            status = dict({'status': 'Error'})
            msg =  dict({'msg':'Counter not found / User did not login'})  
    if status == dict({}) :
        counterstatus = cstatusobj[0]
        counterstatus.lastactive = datetime_now
        counterstatus.save()

        # check counter status
        if counterstatus.status != 'calling' :
            status = dict({'status': 'Error'})
            msg =  dict({'msg':'Counter status is not CALLING'})  
        elif counterstatus.tickettemp == None :
            status = dict({'status': 'Error'})
            msg =  dict({'msg':'Counter status - no ticket'})  
    if status == dict({}) :
        if counterstatus.tickettemp.tickettype != rx_ticketype :
            status = dict({'status': 'Error'})
            msg =  dict({'msg':'Counter status - ticket is not same'})  
    if status == dict({}) :
        if counterstatus.tickettemp.ticketnumber != rx_ticketnumber :
            status = dict({'status': 'Error'})
            msg =  dict({'msg':'Counter status - ticket is not same'})  
    if status == dict({}) :

        stickettime = ''        
        try:
            stickettime = str(datetime.strptime(rx_tickettime, '%Y-%m-%dT%H:%M:%S.%fZ'))
            rx_tickettime = datetime.strptime(rx_tickettime, '%Y-%m-%dT%H:%M:%S.%f%z' )
        except:
            stickettime = ''
        if stickettime == '' :
            try :
                stickettime = str(datetime.strptime(rx_tickettime, '%Y-%m-%dT%H:%M:%SZ' )) 
                rx_tickettime = datetime.strptime(rx_tickettime, '%Y-%m-%dT%H:%M:%S%z')
            except:
                stickettime = ''
                status = dict({'status': 'Error'})
                msg =  dict({'msg':'Ticket time format not correct. Should be : 2022-05-19T23:59:59.123456Z'}) 
                        
    if status == dict({}) :
        ttime = counterstatus.tickettemp.tickettime
        if ttime != rx_tickettime :            
            status = dict({'status': 'Error'})
            msg =  dict({'msg':'Counter status - ticket time is not same ' 
            + str(ttime.year)
            +'-'
            + str(ttime.month)
            +'-'
            + str(ttime.day)
            +'T'
            + str(ttime.hour)
            +':'
            + str(ttime.minute)
            +':'
            + str(ttime.second)
            +'.'
            + str(ttime.microsecond)
            +'Z'
              })            
        
    if status == dict({}) :
        status, msg = funCounterRecall(user, branch, countertype, counterstatus, 'Recalling ticket API : ', rx_app, rx_version, datetime_now)




    output = status | msg | context
    return Response(output)



@api_view(['POST'])
@permission_classes([IsAuthenticated])
def postCounterCall(request):
# Request :
# 'POST /api/call/?username=xxx&password=xxx&token=xxx&app=xxx&version=xxx&branchcode=xxx&countertype=xxx&counternumber=xxx'
#
# Response :
# {
#    "status":"OK/Error",
#    "msg":"Ticket route not found",
#    "data": {
#        "priority": "mask",
#        "mask": "CA",
#        "tickettype": "C",
#        "ticketnumber": "001",
#        "tickettime": "2022-06-06T03:59:00Z"
#    }
# }
    status = dict({})
    msg = dict({})
    context = dict({})

    rx_username = request.GET.get('username') if request.GET.get('username') != None else ''
    # rx_password = request.GET.get('password') if request.GET.get('password') != None else ''
    # rx_token = request.GET.get('token') if request.GET.get('token') != None else ''
    rx_app = request.GET.get('app') if request.GET.get('app') != None else ''
    rx_version = request.GET.get('version') if request.GET.get('version') != None else ''
    rx_bcode = request.GET.get('branchcode') if request.GET.get('branchcode') != None else ''
    rx_countername = request.GET.get('countername') if request.GET.get('countername') != None else ''
    rx_counternumber = request.GET.get('counternumber') if request.GET.get('counternumber') != None else ''

    datetime_now =timezone.now()
   
    # check input
    if status == dict({}) :
        if rx_countername == '' :
            status = dict({'status': 'Error'})
            msg =  dict({'msg':'No counter name'})  
    if status == dict({}) :
        if rx_counternumber == '' :
            status = dict({'status': 'Error'})
            msg =  dict({'msg':'No counter number'})  

    if status == dict({}) :
        branch = None
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

    # Save Api Log
    if setting_APIlogEnabled(branch) == True :
        APILog.objects.create(
            logtime=datetime_now,
            requeststr = request.build_absolute_uri() ,
            ip = visitor_ip_address(request),
            app = rx_app,
            version = rx_version,
            logtext = 'API call : Counter waiting list',
        )



    # rx_username should be already login to counter
    if status == dict({}) :
        if rx_username == '' :
            status = dict({'status': 'Error'})
            msg =  dict({'msg':'No username'})
    # check user
    if status == dict({}) :
        error, user = checkuser(request.user, branch, rx_username)
        if error !='OK' :
            status = dict({'status': 'Error'})
            msg =  dict({'msg':error})

            
    
    if status == dict({}) :
        # get the Counter type
        ctypeobj = CounterType.objects.filter( Q(branch=branch) & Q(name=rx_countername) )
        if not(ctypeobj.count() > 0) :
            status = dict({'status': 'Error'})
            msg =  dict({'msg':'Counter Type not found'})    
    
    if status == dict({}) :
        countertype = ctypeobj[0]
        cstatusobj = CounterStatus.objects.filter( Q(countertype=countertype) & Q(counternumber=rx_counternumber) & Q(user=user))
        if not(cstatusobj.count() > 0) :
            status = dict({'status': 'Error'})
            msg =  dict({'msg':'Counter not found / User did not login'})  
    if status == dict({}) :
        counterstatus = cstatusobj[0]
        counterstatus.lastactive = datetime_now
        counterstatus.save()

        # check counter status
        if counterstatus.status != 'waiting' :
            status = dict({'status': 'Error'})
            msg =  dict({'msg':'Counter status is not WAITING'})  
        elif counterstatus.tickettemp != None :
            status = dict({'status': 'Error'})
            msg =  dict({'msg':'Counter still processing ticket:' + counterstatus.tickettemp.tickettype + counterstatus.tickettemp.ticketnumber})  


    if status == dict({}) :
        # function call ticket
        status, msg, context = funCounterCall(user, branch, countertype, counterstatus, 'Calling ticket API : ', rx_app, rx_version, datetime_now)
    
    output = status | msg | context
    print (output)
    return Response(output)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def getCounterWaitingList(request):
# Request :
# 'GET /api/waiting/?username=xxx&password=xxx&token=xxx&app=xxx&version=xxx&branchcode=xxx&countertype=xxx&counternumber=xxx'
#
# Response :
# {
#    "status":"OK/Error",
#    "msg":"Ticket route not found",
#    "servertime": "2022-06-16T07:13:44.724232Z"
#    "data":[
#         { "tickettype": "A", "ticketnumber": "001", "tickettime":"2022-11-30","bcode":"KB"}   
#    ]
# }
    status = dict({})
    msg = dict({})
    context = dict({})

    rx_username = request.GET.get('username') if request.GET.get('username') != None else ''
    # rx_password = request.GET.get('password') if request.GET.get('password') != None else ''
    # rx_token = request.GET.get('token') if request.GET.get('token') != None else ''
    rx_app = request.GET.get('app') if request.GET.get('app') != None else ''
    rx_version = request.GET.get('version') if request.GET.get('version') != None else ''
    rx_bcode = request.GET.get('branchcode') if request.GET.get('branchcode') != None else ''
    rx_countername = request.GET.get('countername') if request.GET.get('countername') != None else ''
    rx_counternumber = request.GET.get('counternumber') if request.GET.get('counternumber') != None else ''

    datetime_now =timezone.now()
   
    # check input
    if status == dict({}) :
        if rx_countername == '' :
            status = dict({'status': 'Error'})
            msg =  dict({'msg':'No counter name'})  
    if status == dict({}) :
        if rx_counternumber == '' :
            status = dict({'status': 'Error'})
            msg =  dict({'msg':'No counter number'})  

    if status == dict({}) :
        branch = None
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

    # Save Api Log
    if setting_APIlogEnabled(branch) == True :
        APILog.objects.create(
            logtime=datetime_now,
            requeststr = request.build_absolute_uri() ,
            ip = visitor_ip_address(request),
            app = rx_app,
            version = rx_version,
            logtext = 'API call : Counter waiting list',
        )




    # rx_username should be already login to counter
    if status == dict({}) :
        if rx_username == '' :
            status = dict({'status': 'Error'})
            msg =  dict({'msg':'No username'})
    # check user
    if status == dict({}) :
        error, user = checkuser(request.user, branch, rx_username)
        if error !='OK' :
            status = dict({'status': 'Error'})
            msg =  dict({'msg':error})



        
    if status == dict({}) :
        # get the Counter type
        ctypeobj = CounterType.objects.filter( Q(branch=branch) & Q(name=rx_countername) )
        if not(ctypeobj.count() > 0) :
            status = dict({'status': 'Error'})
            msg =  dict({'msg':'Counter Type not found'})  
    if status == dict({}) :
        countertype = ctypeobj[0]
        cstatusobj = CounterStatus.objects.filter( Q(countertype=countertype) & Q(counternumber=rx_counternumber) & Q(user=user))
        if not(cstatusobj.count() > 0) :
            status = dict({'status': 'Error'})
            msg =  dict({'msg':'Counter not found'})  
    if status == dict({}) :
        counterstatus = cstatusobj[0]
        counterstatus.lastactive = datetime_now
        counterstatus.save()

        ticketlist = TicketTemp.objects.filter( Q(branch=branch) & Q(countertype=countertype) & Q(status=lcounterstatus[0]) & Q(locked=False))
        serializers  = waitinglistSerivalizer(ticketlist, many=True)
        context = dict({'data':serializers.data})
        status = dict({'status': 'OK'})
        # msg =  dict({'msg':'Everything will be OK.'})        
    servertime = dict({'servertime': datetime_now})
    output = status | msg | servertime | context
    return Response(output)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def postCounterLogout(request):
# Request :
# 'POST /api/counterlogout/?username=xxx&password=xxx&token=xxx&app=xxx&version=xxx&branchcode=xxx&countertype=xxx&counternumber=xxx'
#
# Response :
# {
#    "status":"OK/Error",
#    "msg":"Ticket route not found",
#    "data":[
#         {"ticket":"A001","tickettime":"2022-11-30","i":"1"}   
#    ]
# }
    status = dict({})
    msg = dict({})
    context = dict({})

    rx_username = request.GET.get('username') if request.GET.get('username') != None else ''
    # rx_password = request.GET.get('password') if request.GET.get('password') != None else ''
    # rx_token = request.GET.get('token') if request.GET.get('token') != None else ''
    rx_app = request.GET.get('app') if request.GET.get('app') != None else ''
    rx_version = request.GET.get('version') if request.GET.get('version') != None else ''
    rx_bcode = request.GET.get('branchcode') if request.GET.get('branchcode') != None else ''
    rx_countername = request.GET.get('countername') if request.GET.get('countername') != None else ''
    rx_counternumber = request.GET.get('counternumber') if request.GET.get('counternumber') != None else ''

    datetime_now =timezone.now()

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


    # check input
    if status == dict({}) :    
        if rx_countername == '' :
            status = dict({'status': 'Error'})
            msg =  dict({'msg':'No counter name'})  
    if status == dict({}) :
        if rx_counternumber == '' :
            status = dict({'status': 'Error'})
            msg =  dict({'msg':'No counter number'})      
   


    # Save Api Log
    if setting_APIlogEnabled(branch) == True :
        APILog.objects.create(
            logtime=datetime_now,
            requeststr = request.build_absolute_uri() ,
            ip = visitor_ip_address(request),
            app = rx_app,
            version = rx_version,
            logtext = 'API call : Counter logout',
        )

    # rx_username should be already login to counter
    if status == dict({}) :
        if rx_username == '' :
            status = dict({'status': 'Error'})
            msg =  dict({'msg':'No username'})
    # check user
    if status == dict({}) :
        error, user = checkuser(request.user, branch, rx_username)
        if error !='OK' :
            status = dict({'status': 'Error'})
            msg =  dict({'msg':error})





    if status == dict({}) :
        # get the Counter type
        ctypeobj = CounterType.objects.filter( Q(branch=branch) & Q(name=rx_countername) )
        if not(ctypeobj.count() > 0) :
            status = dict({'status': 'Error'})
            msg =  dict({'msg':'Counter Type not found'})  
    if status == dict({}) :
        countertype = ctypeobj[0]
        cstatusobj = CounterStatus.objects.filter( Q(countertype=countertype) & Q(counternumber=rx_counternumber) & Q(user=user))
        if not(cstatusobj.count() > 0) :
            status = dict({'status': 'Error'})
            msg =  dict({'msg':'Counter not found'})  
    if status == dict({}) :
            counterstatus = cstatusobj[0]
            status, msg = funCounterLogout(counterstatus, datetime_now)
    output = status | msg | context
    return Response(output)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def postCounterLogin(request):
# Request :
# 'POST /api/counterlogin/?username=xxx&password=xxx&token=xxx&app=xxx&version=xxx&branchcode=xxx&countertype=xxx&counternumber=xxx'

# Response :
# {
#     "status":"OK/Error",
#     "msg":"Ticket route not found",
#     "data": {
#         "name": "Mary Li",
#         "ttype": "ABCDEFGHIJKLMNOPQRSTUVWXYZ",
#         "timezone": 8,
#         "counterstatus": "waiting",
#         "tickettype": "",
#         "ticketnumber": "",
#         "tickettime": "",
#         "ticketnoformat": "000"
#     }
# }
# "tickettype", "ticketnumber", "tickettime", "ticketnoformat" is from counterstatus

    status = dict({})
    msg = dict({})
    context = dict({})

    rx_username = request.GET.get('username') if request.GET.get('username') != None else ''
    rx_password = request.GET.get('password') if request.GET.get('password') != None else ''
    # rx_token = request.GET.get('token') if request.GET.get('token') != None else ''
    rx_app = request.GET.get('app') if request.GET.get('app') != None else ''
    rx_version = request.GET.get('version') if request.GET.get('version') != None else ''
    rx_bcode = request.GET.get('branchcode') if request.GET.get('branchcode') != None else ''
    rx_countername = request.GET.get('countername') if request.GET.get('countername') != None else ''
    rx_counternumber = request.GET.get('counternumber') if request.GET.get('counternumber') != None else ''

    datetime_now =timezone.now()

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

    # check input
    if status == dict({}) :    
        if rx_countername == '' :
            status = dict({'status': 'Error'})
            msg =  dict({'msg':'No counter name'})  
    if status == dict({}) :
        if rx_counternumber == '' :
            status = dict({'status': 'Error'})
            msg =  dict({'msg':'No counter number'}) 


    # Save Api Log
    if setting_APIlogEnabled(branch) == True :
        APILog.objects.create(
            logtime=datetime_now,
            requeststr = request.build_absolute_uri() ,
            ip = visitor_ip_address(request),
            app = rx_app,
            version = rx_version,
            logtext = 'API call : Counter login',
        )


    if status == dict({}) :
        
        loginreply, user = loginapi_notoken(request , rx_username, rx_password, branch)

        if loginreply != 'OK':
            status = dict({'status': 'Error'})
            msg =  dict({'msg':loginreply})   
    if status == dict({}) :

        # get the Counter type
        ctypeobj = CounterType.objects.filter( Q(branch=branch) & Q(name=rx_countername) )
        if not(ctypeobj.count() > 0) :
            status = dict({'status': 'Error'})
            msg =  dict({'msg':'Counter Type not found'})  
        else :
            countertype = ctypeobj[0]
            # check counter type is enabled
            if countertype.enabled == False :
                status = dict({'status': 'Error'})
                msg =  dict({'msg':'Counter Type not disabled'}) 

    if status == dict({}) :
        # find counter type and check the counter type is enabled
        cstatusobj = CounterStatus.objects.filter( Q(countertype=countertype) & Q(counternumber=rx_counternumber) )
        if not(cstatusobj.count() > 0) :
            status = dict({'status': 'Error'})
            msg =  dict({'msg':'Counter not found'})  
        else :
            counterstatus = cstatusobj[0]

    if status == dict({}) :
        status, msg, context = funCounterLogin(datetime_now, user, branch, counterstatus, rx_counternumber, countertype)
                
    output = status | msg | context
    return Response(output)


def checkactive(datetime_now, counterstatus,) :
    # need auto logout ? and then login again
    timediff = datetime_now - counterstatus.lastactive 
    timediff = timediff.seconds / 60
    if timediff >= counteractive : # if the counter keep active > 3 minutes then auto logout and the counter replace the new user    
        user = counterstatus.user
        countertype = counterstatus.countertype
        counternumber = counterstatus.counternumber
        autologoutOK = logcounterlogout(counterstatus.user, counterstatus.countertype, counterstatus.counternumber, counterstatus.logintime, counterstatus.lastactive)
        if autologoutOK == 'OK' :
            logcounterlogin(user, countertype, counternumber, datetime_now)
        else :
            return dict({'status': 'Error'}), dict({'msg':'Counter auto logout fault'}) 
    counterstatus.lastactive = datetime_now
    counterstatus.save()
    return dict({}), dict({})