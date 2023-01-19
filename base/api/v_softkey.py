from datetime import datetime
from django.utils import timezone
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.db.models import Q
from .views import setting_APIlogEnabled, visitor_ip_address, loginapi, funUTCtoLocal, counteractive
from .v_display import newdisplayvoice
from base.models import APILog, Branch, CounterStatus, CounterType, DisplayAndVoice, Setting, TicketFormat, TicketTemp, TicketRoute, TicketData, TicketLog, CounterLoginLog, UserProfile, lcounterstatus
from .serializers import waitinglistSerivalizer
from .v_display import wssendwebtv

@api_view(['POST'])
def postCounterGet(request):
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
    rx_password = request.GET.get('password') if request.GET.get('password') != None else ''
    rx_token = request.GET.get('token') if request.GET.get('token') != None else ''
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



    if status == dict({}) :
        
        loginreply, user = loginapi(request , rx_username, rx_password, rx_token, branch)

        if loginreply != 'OK':
            status = dict({'status': 'Error'})
            msg =  dict({'msg':loginreply})   
    
    
    

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

    ticket = None
    if status == dict({}) :
        # find ticket in waiting list
        objt = TicketTemp.objects.filter(
            tickettype=rx_ticketype,
            ticketnumber=rx_ticketnumber,
            branch=branch,
            status='waiting',
            locked=False).order_by('-tickettime')
        if objt.count() >= 1 :
            ticket = objt[0]
        else:
            # find ticket in miss list
            objt = TicketTemp.objects.filter(
                tickettype=rx_ticketype,
                ticketnumber=rx_ticketnumber,
                branch=branch,
                status='miss',
                locked=False).order_by('-tickettime')
            if objt.count() >= 1 :
                ticket = objt[0]
        if ticket == None:
            status = dict({'status': 'Error'})
            msg =  dict({'msg':'Ticket not found'}) 

      
        
    if status == dict({}) :

        # update ticketdata db
        objtd = TicketData.objects.filter(
            tickettemp=ticket,
            countertype=countertype,
            step=ticket.step,
            branch=branch,
        )
        td = None
        if objtd.count() == 1 :
            td = objtd[0]
        else:
            status = dict({'status': 'Error'})
            msg =  dict({'msg':'TicketData is multi ' })   
        if td == None:                 
            status = dict({'status': 'Error'})
            msg =  dict({'msg':'TicketData not found ' })
        else:
            if td.starttime == None:
                status = dict({'status': 'Error'})
                msg =  dict({'msg':'Ticket time is NONE' })
            else :
                td.calltime = datetime_now
                td.calluser = user
                time_diff = datetime_now - td.starttime
                tsecs = int(time_diff.total_seconds())
                td.waitingperiod = tsecs
                td.save()

    if status == dict({}) :
        # update counterstatus db 
        counterstatus.tickettemp = ticket
        counterstatus.status = lcounterstatus[1]
        counterstatus.save()

        # update ticket 
        ticket.user = user
        ticket.status = 'calling'
        ticket.save()
        

        # add ticketlog
        TicketLog.objects.create(
            tickettemp=ticket,
            logtime=datetime_now,
            app = rx_app,
            version = rx_version,
            logtext='Ticket Get API : '  + branch.bcode + '_' + ticket.tickettype + '_'+ ticket.ticketnumber + '_' + ticket.tickettime.strftime('%Y-%m-%dT%H:%M:%S.%fZ') ,
            user=user,
        )

        # do display and voice temp db
        newdisplayvoice(branch, countertype, rx_counternumber, ticket, datetime_now, user)



        context = {'tickettype': ticket.tickettype, 'ticketnumber': ticket.ticketnumber , 'tickettime': ticket.tickettime}
        context = dict({'data':context})
        status = dict({'status': 'OK'})
        msg =  dict({'msg':'Ticket Get.'})  

        # websocket to web tv
        wssendwebtv(rx_bcode,countertype.name)




    output = status | msg | context
    return Response(output)


@api_view(['POST'])
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
    rx_password = request.GET.get('password') if request.GET.get('password') != None else ''
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



    if status == dict({}) :
        
        loginreply, user = loginapi(request , rx_username, rx_password, rx_token, branch)

        if loginreply != 'OK':
            status = dict({'status': 'Error'})
            msg =  dict({'msg':loginreply})   
    
    
    

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

    #     # check counter status
    #     if counterstatus.status != 'waiting' :
    #         status = dict({'status': 'Error'})
    #         msg =  dict({'msg':'Counter status is not WAITING'})  
    #     elif counterstatus.tickettemp == None :
    #         status = dict({'status': 'Error'})
    #         msg =  dict({'msg':'Counter status - no ticket'})  
    # if status == dict({}) :
    #     if counterstatus.tickettemp.tickettype != rx_ticketype :
    #         status = dict({'status': 'Error'})
    #         msg =  dict({'msg':'Counter status - ticket is not same'})  
    # if status == dict({}) :
    #     if counterstatus.tickettemp.ticketnumber != rx_ticketnumber :
    #         status = dict({'status': 'Error'})
    #         msg =  dict({'msg':'Counter status - ticket is not same'})  



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

        # update ticketdata db
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
            else :
                td.voidtime = datetime_now
                td.voiduser = user
                time_diff = datetime_now - td.starttime
                tsecs = int(time_diff.total_seconds())
                td.waitingperiod = tsecs
                td.save()

    if status == dict({}) :
        # # update counterstatus db 
        # counterstatus.tickettemp = None
        # counterstatus.status = lcounterstatus[0]
        # counterstatus.save()

        # update ticket 
        tickett.user = user
        tickett.status = 'void'
        tickett.save()
        

        # add ticketlog
        TicketLog.objects.create(
            tickettemp=tickett,
            logtime=datetime_now,
            app = rx_app,
            version = rx_version,
            logtext='Ticket Void API : '  + branch.bcode + '_' + tickett.tickettype + '_'+ tickett.ticketnumber + '_' + datetime_now.strftime('%Y-%m-%dT%H:%M:%S.%fZ') ,
            user=user,
        )

        # websocket to web tv
        wssendwebtv(rx_bcode,countertype.name)

        status = dict({'status': 'OK'})
        msg =  dict({'msg':'Ticket voided.'})  




    output = status | msg | context
    return Response(output)



@api_view(['POST'])
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
    rx_password = request.GET.get('password') if request.GET.get('password') != None else ''
    rx_token = request.GET.get('token') if request.GET.get('token') != None else ''
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



    if status == dict({}) :
        
        loginreply, user = loginapi(request , rx_username, rx_password, rx_token, branch)

        if loginreply != 'OK':
            status = dict({'status': 'Error'})
            msg =  dict({'msg':loginreply})   
    
    
    

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

        ticket = counterstatus.tickettemp 

        # update ticketdata db
        td = None
        obj_td = TicketData.objects.filter(
            tickettemp=ticket,
            countertype=countertype,
            step=ticket.step,
            branch=branch,
        )
        if obj_td.count() == 1 :
            td = obj_td[0]
        else:
            status = dict({'status': 'Error'})
            msg =  dict({'msg':'TicketData is multi ' })   
        if td == None:        
            status = dict({'status': 'Error'})
            msg =  dict({'msg':'TicketData not found ' })            
        elif td.calltime == None or td.walkingperiod == None or td.waitingperiod == None :
            status = dict({'status': 'Error'})
            msg =  dict({'msg':'TicketData - data not correct'})


    if status == dict({}) :
        td.donetime = datetime_now
        td.doneuser = user
        time_diff = datetime_now - td.calltime
        tsecs = int(time_diff.total_seconds())
        td.processingperiod = tsecs
        total = tsecs + td.walkingperiod + td.waitingperiod
        td.totalperiod = total
        td.save()

        # update counterstatus db 
        counterstatus.tickettemp = None
        counterstatus.status = lcounterstatus[0]
        counterstatus.save()

        # check ticket next step
        step = ticket.step
        nextstep = step +1
        routeobj = TicketRoute.objects.filter(branch=branch, step=nextstep, tickettype=rx_ticketype)       

        if routeobj.count() != 1 :
            # no next step
            ticket.status = lcounterstatus[3]  #'done'
            ticket.save()

            # add ticketlog
            TicketLog.objects.create(
                tickettemp=ticket,
                logtime=datetime_now,
                app = rx_app,
                version = rx_version,
                logtext='Ticket Done API : '  + branch.bcode + '_' + ticket.tickettype + '_'+ ticket.ticketnumber + '_' + datetime_now.strftime('%Y-%m-%dT%H:%M:%S.%fZ') ,
                user=user,
            )

        else:
            # next step
            route = routeobj[0] 
            countertype = route.countertype
            ticket.countertype = countertype
            ticket.status = lcounterstatus[0]
            ticket.step = nextstep
            ticket.save()

            # new ticket data
            TicketData.objects.create(
                tickettemp=ticket,
                branch = branch,
                countertype=countertype,
                step=ticket.step,
                starttime = datetime_now,
                startuser=user,
            )

            # add ticketlog
            TicketLog.objects.create(
                tickettemp=ticket,
                logtime=datetime_now,
                app = rx_app,
                version = rx_version,
                logtext='Ticket Done API (next step): '  + branch.bcode + '_' + ticket.tickettype + '_'+ ticket.ticketnumber + '_' + datetime_now.strftime('%Y-%m-%dT%H:%M:%S.%fZ') ,
                user=user,
            )
        
        status = dict({'status': 'OK'})
        msg =  dict({'msg':'Ticket done.'})  

    output = status | msg | context
    return Response(output)



@api_view(['POST'])
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
    rx_password = request.GET.get('password') if request.GET.get('password') != None else ''
    rx_token = request.GET.get('token') if request.GET.get('token') != None else ''
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



    if status == dict({}) :
        
        loginreply, user = loginapi(request , rx_username, rx_password, rx_token, branch)

        if loginreply != 'OK':
            status = dict({'status': 'Error'})
            msg =  dict({'msg':loginreply})   
    
    
    

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

        ticket = counterstatus.tickettemp 

        # update ticketdata db
        td = None
        obj_td = TicketData.objects.filter(
            tickettemp=ticket,
            countertype=countertype,
            step=ticket.step,
            branch=branch,
        )
        if obj_td.count() == 1 :
            td = obj_td[0]
        else:
            status = dict({'status': 'Error'})
            msg =  dict({'msg':'TicketData is multi ' })     
        if td == None :
            status = dict({'status': 'Error'})
            msg =  dict({'msg':'TicketData not found ' })            
        elif td.calltime == None:
            status = dict({'status': 'Error'})
            msg =  dict({'msg':'TicketData : call time is None'})  

    if status == dict({}) :
        td.misstime = datetime_now
        td.missuser = user
        time_diff = datetime_now - td.calltime
        tsecs = int(time_diff.total_seconds())
        td.walkingperiod = tsecs
        td.save()

        # update counterstatus db 
        counterstatus.tickettemp = None
        counterstatus.status = lcounterstatus[0]
        counterstatus.save()

        # update ticket 
        ticket.user = user
        ticket.status = 'miss'
        ticket.save()
        

        # add ticketlog
        TicketLog.objects.create(
            tickettemp=ticket,
            logtime=datetime_now,
            app = rx_app,
            version = rx_version,
            logtext='Ticket No Show API : '  + branch.bcode + '_' + ticket.tickettype + '_'+ ticket.ticketnumber + '_' + datetime_now.strftime('%Y-%m-%dT%H:%M:%S.%fZ') ,
            user=user,
        )


        status = dict({'status': 'OK'})
        msg =  dict({'msg':'Ticket no show.'})  




    output = status | msg | context
    return Response(output)



@api_view(['POST'])
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
    rx_password = request.GET.get('password') if request.GET.get('password') != None else ''
    rx_token = request.GET.get('token') if request.GET.get('token') != None else ''
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



    if status == dict({}) :
        
        loginreply, user = loginapi(request , rx_username, rx_password, rx_token, branch)

        if loginreply != 'OK':
            status = dict({'status': 'Error'})
            msg =  dict({'msg':loginreply})   
    
    
    
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

        ticket = counterstatus.tickettemp 

        # update ticketdata db
        td = None
        obj_td = TicketData.objects.filter(
            tickettemp=ticket,            
            countertype=countertype,
            step=ticket.step,
            branch=branch,
        )
        if obj_td.count() == 1 :
            td = obj_td[0]
        else:
            status = dict({'status': 'Error'})
            msg =  dict({'msg':'TicketData is multi ' })  

        if td == None :
            status = dict({'status': 'Error'})
            msg =  dict({'msg':'TicketData not found ' })            
        elif td.calltime == None:
            status = dict({'status': 'Error'})
            msg =  dict({'msg':'TicketData: calltime not found'})  
    if status == dict({}) :            
        td.processtime = datetime_now
        td.processuser = user        
        time_diff = datetime_now - td.calltime
        tsecs = int(time_diff.total_seconds())
        td.walkingperiod = tsecs
        td.save()

        # update counterstatus db 
        counterstatus.tickettemp = ticket
        counterstatus.status = lcounterstatus[2]
        counterstatus.save()

        # update ticket 
        ticket.user = user
        ticket.status = lcounterstatus[2]
        ticket.save()
        
        # add ticketlog
        TicketLog.objects.create(
            tickettemp=ticket,
            logtime=datetime_now,
            app = rx_app,
            version = rx_version,
            logtext='Process ticket API : '  + branch.bcode + '_' + ticket.tickettype + '_'+ ticket.ticketnumber + '_' + datetime_now.strftime('%Y-%m-%dT%H:%M:%S.%fZ') ,
            user=user,
        )

        status = dict({'status': 'OK'})
        msg =  dict({'msg':'Process ticket.'})

    output = status | msg | context
    return Response(output)




@api_view(['POST'])
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
    rx_password = request.GET.get('password') if request.GET.get('password') != None else ''
    rx_token = request.GET.get('token') if request.GET.get('token') != None else ''
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



    if status == dict({}) :
        
        loginreply, user = loginapi(request , rx_username, rx_password, rx_token, branch)

        if loginreply != 'OK':
            status = dict({'status': 'Error'})
            msg =  dict({'msg':loginreply})   
    
    
    

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


        # add ticketlog
        ticket = counterstatus.tickettemp 
        TicketLog.objects.create(
            tickettemp=ticket,
            logtime=datetime_now,
            app = rx_app,
            version = rx_version,
            logtext='Recalling ticket API : '  + branch.bcode + '_' + ticket.tickettype + '_'+ ticket.ticketnumber + '_' + datetime_now.strftime('%Y-%m-%dT%H:%M:%S.%fZ') ,
            user=user,
        )

        # do display and voice temp db
        newdisplayvoice(branch, countertype, rx_counternumber, ticket, datetime_now, user)

        # websocket to web tv
        wssendwebtv(rx_bcode,countertype.name)

        status = dict({'status': 'OK'})
        msg =  dict({'msg':'Recall ticket.'})  




    output = status | msg | context
    return Response(output)



@api_view(['POST'])
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
    rx_password = request.GET.get('password') if request.GET.get('password') != None else ''
    rx_token = request.GET.get('token') if request.GET.get('token') != None else ''
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



    if status == dict({}) :
        
        loginreply, user = loginapi(request , rx_username, rx_password, rx_token, branch)

        if loginreply != 'OK':
            status = dict({'status': 'Error'})
            msg =  dict({'msg':loginreply})   
    
    
    
    # check call priority
    # if priority = 'time' / 'umask' user mask / 'bmask' branch mask
    priority = ''
    mask = ''
    if status == dict({}) :
        userp = None
        obj_userp = UserProfile.objects.filter(user__exact=user)
        if obj_userp.count() == 1 :
            userp = obj_userp[0]            
        if userp == None:
            status = dict({'status': 'Error'})
            msg =  dict({'msg':'User profile not found'})  
    if status == dict({}) :
        qp = userp.queuepriority
        if qp == 'time':
            mask = userp.tickettype
            priority = 'time'
        if qp == 'user':            
            mask = userp.tickettype
            priority = 'umask'
        if qp == 'mask':
            # branch mask               
            mask = branch.queuemask
            priority = 'bmask'
        if qp == 'branch':
            qp = branch.queuepriority
            if qp == 'time':
                priority = 'time'
                mask = userp.tickettype
            if qp == 'mask':
                priority = 'bmask'
                mask = branch.queuemask 
            if qp == 'user':
                priority = 'umask'
                mask = userp.tickettype 
        if mask == '' or priority == '' :
            status = dict({'status': 'Error'})
            msg =  dict({'msg':'Queue priority not found (qp:' + qp + ') '+ mask + '<-mask , priority->' + priority})   
        if mask != '' and priority == 'bmask' :
            new_mask=''
            mask_b = mask            
            for tt in mask_b:
                if userp.tickettype.find(tt) != -1:
                    new_mask = new_mask + tt
            mask = new_mask
        if priority == 'bmask' or priority == 'umask' :
            priority = 'mask'
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

        ticket = None

        if priority== 'time':
            # found the waiting ticket by time
            ticketlist = TicketTemp.objects.filter( Q(branch=branch) & Q(countertype=countertype) & Q(status=lcounterstatus[0])  & Q(locked=False)   ).order_by('tickettime')            
            for ticket in ticketlist:
                if mask.find(ticket.tickettype) != -1:
                    # call this ticket
                    context = {'priority': priority, 'mask': mask, 'tickettype': ticket.tickettype, 'ticketnumber': ticket.ticketnumber , 'tickettime': ticket.tickettime}
                    break
        elif priority == 'mask':
            ticketlist = TicketTemp.objects.filter( Q(branch=branch) & Q(countertype=countertype) & Q(status=lcounterstatus[0])  & Q(locked=False)   ).order_by('tickettime')
            for tt in mask:
                for ticket in ticketlist:
                    if tt == ticket.tickettype:
                        # call this ticket
                        context = {'priority': priority, 'mask': mask, 'tickettype': ticket.tickettype, 'ticketnumber': ticket.ticketnumber , 'tickettime': ticket.tickettime}
                        break
                if context != dict({}):
                    break
        if context != dict({}) and ticket != None :


            # update ticketdata db
            td = None
            if status == dict({}) :
                obj_td = TicketData.objects.filter(
                    tickettemp=ticket,
                    countertype=countertype,
                    step=ticket.step,
                    branch=branch,
                )
                if obj_td.count() == 1 :
                    td = obj_td[0]
                else:
                    status = dict({'status': 'Error'})
                    msg =  dict({'msg':'TicketData is multi ' })  
                if td == None :
                    status = dict({'status': 'Error'})
                    msg =  dict({'msg':'TicketData not found ' }) 

            if status == dict({}) :
                td.calltime = datetime_now
                td.calluser = user
                time_diff = datetime_now - td.starttime
                tsecs = int(time_diff.total_seconds())
                td.waitingperiod = tsecs
                td.save()

                # update counterstatus db 
                counterstatus.tickettemp = ticket
                counterstatus.status = lcounterstatus[1]
                counterstatus.save()

                # update ticket 
                ticket.user = user
                ticket.status = lcounterstatus[1]
                ticket.save()

                # add ticketlog
                TicketLog.objects.create(
                    tickettemp=ticket,
                    logtime=datetime_now,
                    app = rx_app,
                    version = rx_version,
                    logtext='Calling ticket API : '  + branch.bcode + '_' + ticket.tickettype + '_'+ ticket.ticketnumber + '_' + datetime_now.strftime('%Y-%m-%dT%H:%M:%S.%fZ') ,
                    user=user,
                )

            # do display and voice temp db
            newdisplayvoice(branch, countertype, rx_counternumber, ticket, datetime_now, user)

            # websocket to web tv
            wssendwebtv(rx_bcode,countertype.name)


        context = dict({'data':context})
        status = dict({'status': 'OK'})
        # msg =  dict({'msg':'Everything will be OK.'})        

    output = status | msg | context
    return Response(output)


@api_view(['GET'])
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
#         {"ticket":"A001","tickettime":"2022-11-30","i":"1"}   
#    ]
# }
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



    if status == dict({}) :
        
        loginreply, user = loginapi(request , rx_username, rx_password, rx_token, branch)

        if loginreply != 'OK':
            status = dict({'status': 'Error'})
            msg =  dict({'msg':loginreply})   
        
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
    rx_password = request.GET.get('password') if request.GET.get('password') != None else ''
    rx_token = request.GET.get('token') if request.GET.get('token') != None else ''
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
        
        loginreply, user = loginapi(request , rx_username, rx_password, rx_token, branch)

        if loginreply != 'OK':
            status = dict({'status': 'Error'})
            msg =  dict({'msg':loginreply})   
        else:

            # get the Counter type
            ctypeobj = CounterType.objects.filter( Q(branch=branch) & Q(name=rx_countername) )
            if not(ctypeobj.count() > 0) :
                status = dict({'status': 'Error'})
                msg =  dict({'msg':'Counter Type not found'})  
            else :
                countertype = ctypeobj[0]
                cstatusobj = CounterStatus.objects.filter( Q(countertype=countertype) & Q(counternumber=rx_counternumber) & Q(user=user))
                if not(cstatusobj.count() > 0) :
                    status = dict({'status': 'Error'})
                    msg =  dict({'msg':'Counter not found'})  
                else :
                    counterstatus = cstatusobj[0]
                    logoutOK = logcounterlogout(counterstatus.user, countertype, rx_counternumber, counterstatus.logintime, datetime_now)
                    if logoutOK == 'OK' :
                        # counter replace new user
                        counterstatus.user = None
                        counterstatus.loged = False
                        counterstatus.logintime = None
                        counterstatus.lastactive = None
                        counterstatus.status = lcounterstatus[0]
                        counterstatus.tickettemp = None
                        counterstatus.save()

                        status = dict({'status': 'OK'})
                        msg =  dict({'msg':'Logout completed'})  
                    else:
                        status = dict({'status': 'Error'})
                        msg =  dict({'msg':logoutOK})  
    output = status | msg | context
    return Response(output)

@api_view(['POST'])
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
    rx_token = request.GET.get('token') if request.GET.get('token') != None else ''
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
        
        loginreply, user = loginapi(request , rx_username, rx_password, rx_token, branch)

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
        # check the counter is free?
        cstatusobj = CounterStatus.objects.filter( Q(countertype=countertype) & Q(counternumber=rx_counternumber) )
        if not(cstatusobj.count() > 0) :
            status = dict({'status': 'Error'})
            msg =  dict({'msg':'Counter not found'})  
        else :
            counterstatus = cstatusobj[0]

            # check the counter is enabled
            if counterstatus.enabled == False :
                status = dict({'status': 'Error'})
                msg =  dict({'msg':'Counter is disabled'})  

    # get user profiles
    if status == dict({}) :
        userp = None
        obj_userp =UserProfile.objects.filter(user__exact=user)
        if obj_userp.count() == 1 :
            userp = obj_userp[0]
        if userp == None :
            status = dict({'status': 'Error'})
            msg =  dict({'msg':'user profile not found or more then one'})       

    # check the user is already login 
    if status == dict({}) :
        if branch.usersinglelogin == True :
            csobj = CounterStatus.objects.filter( Q(loged=True) & ~Q(counternumber=rx_counternumber) & Q(user=user) )
            if csobj.count() > 0 :
                    status = dict({'status': 'Error'})
                    msg =  dict({'msg':'User already logged-in'})    

    # check the counter is already login 
    if status == dict({}) :
        if counterstatus.loged == True :
            # need auto logout ? and then login again
            timediff = datetime_now - counterstatus.lastactive 
            timediff = timediff.seconds / 60
            if timediff >= counteractive : # if the counter keep active > 3 minutes then auto logout and the counter replace the new user
                # auto logout and counter replace new user
                autologoutOK = logcounterlogout(counterstatus.user, countertype, rx_counternumber, counterstatus.logintime, counterstatus.lastactive)
                if autologoutOK == 'OK' :
                    # counter replace new user
                    counterstatus.user = user
                    counterstatus.loged = True
                    counterstatus.logintime = datetime_now
                    counterstatus.lastactive = datetime_now
                    counterstatus.save()

                    logcounterlogin(user, countertype, rx_counternumber, datetime_now)
                    status = dict({'status': 'OK'})
                    msg =  dict({'msg':'Have a nice day'})  

                    ttype=''
                    tno = ''
                    ttime=''
                    if counterstatus.tickettemp != None:
                        ttype = counterstatus.tickettemp.tickettype
                        tno = counterstatus.tickettemp.ticketnumber
                        ttime = counterstatus.tickettemp.tickettime

                    context = {'name': user.first_name + ' ' + user.last_name , 'ttype': userp.tickettype, 'timezone': branch.timezone,
                    'counterstatus':counterstatus.status, 'tickettype':ttype, 'ticketnumber':tno, 'tickettime':ttime,
                    'ticketnoformat':branch.ticketnoformat,
                    }
                    context = dict({'data':context})    
                else:
                    status = dict({'status': 'Error'})
                    msg =  dict({'msg':'Counter auto logout fault'}) 
            else :
                # no need create new Counter Login Log
                # check is same user
                if counterstatus.user == user:
                    counterstatus.lastactive = datetime_now
                    counterstatus.save()
                    status = dict({'status': 'OK'})
                    msg =  dict({'msg':'Have a nice day'})  

                                        
                    ttype=''
                    tno = ''
                    ttime=''
                    if counterstatus.tickettemp != None:
                        ttype = counterstatus.tickettemp.tickettype
                        tno = counterstatus.tickettemp.ticketnumber
                        ttime = counterstatus.tickettemp.tickettime

                    context = {'name': user.first_name + ' ' + user.last_name , 'ttype': userp.tickettype, 'timezone': branch.timezone,
                    'counterstatus':counterstatus.status, 'tickettype':ttype, 'ticketnumber':tno, 'tickettime':ttime,
                    'ticketnoformat':branch.ticketnoformat,
                    }
                    context = dict({'data':context})    
                else :
                    status = dict({'status': 'Error'})
                    msg =  dict({'msg':'Counter already logged-in'})  
        else:
            if status == dict({}) :
                # login 
                counterstatus.user = user
                counterstatus.loged = True
                counterstatus.logintime = datetime_now
                counterstatus.lastactive = datetime_now
                counterstatus.save()       

                logcounterlogin(user, countertype, rx_counternumber, datetime_now)
                status = dict({'status': 'OK'})
                msg =  dict({'msg':'Have a nice day'})  

                ttype=''
                tno = ''
                ttime=''
                if counterstatus.tickettemp != None:
                    ttype = counterstatus.tickettemp.tickettype
                    tno = counterstatus.tickettemp.ticketnumber
                    ttime = counterstatus.tickettemp.tickettime

                context = {'name': user.first_name + ' ' + user.last_name , 'ttype': userp.tickettype, 'timezone': branch.timezone,
                'counterstatus':counterstatus.status, 'tickettype':ttype, 'ticketnumber':tno, 'tickettime':ttime,}
                context = dict({'data':context})                    
                
    output = status | msg | context
    return Response(output)

def logcounterlogout (user, countertype, counternumber, logintime, logouttime) -> str :
    sOut = 'Error'

    obj = CounterLoginLog.objects.filter( Q(user=user) & Q(countertype=countertype)  & Q(counternumber=counternumber)  & Q(logintime=logintime) )
    if not(obj.count() > 0) :
        sOut = 'Counter Login Log not find ' + countertype.name + ',' + str(counternumber) + ',' + str(logintime)
    else :        
        loginlog = obj[0]
        loginlog.logouttime = logouttime
        loginlog.save()
        sOut = 'OK'

    return sOut

def logcounterlogin (user, countertype, counternumber, logintime) -> str :

    CounterLoginLog.objects.create(
            countertype=countertype,
            counternumber = counternumber ,
            user = user,
            logintime = logintime,
        )
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