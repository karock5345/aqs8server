from datetime import datetime
from django.utils import timezone
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.db.models import Q
from .views import setting_APIlogEnabled, visitor_ip_address, loginapi, funUTCtoLocal, counteractive
from .v_display import newdisplayvoice
from base.models import APILog, Branch, CounterStatus, CounterType, DisplayAndVoice, Setting, TicketFormat, TicketTemp, TicketRoute, TicketData, TicketLog, CounterLoginLog, UserProfile, lcounterstatus
from .serializers import waitinglistSerivalizer
from base.ws import wssendwebtv, wssendql, wsSendTicketStatus, wssendvoice, wscounterstatus

softkey_version = '8.0.2.0'

def funCounterCall(user, branch, countertype, counterstatus, logtext, rx_app, rx_version, datetime_now):
    status = dict({})
    msg = dict({})
    context = dict({})

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
            # remove all space in mask_b
            mask_b = mask_b.replace(' ', '')
            u_tt = userp.tickettype
            u_tt = u_tt.replace(' ', '')

            istart = 0
            for i in range(len(mask_b)):
                if mask_b[i] == ',':
                    tt = mask_b[istart:i+1]
                    istart = i +1
                    if u_tt.find(tt) != -1 :
                        new_mask  = new_mask +tt
            mask = new_mask
        if priority == 'bmask' or priority == 'umask' :
            priority = 'mask'
    if status == dict({}) :
        # get the Counter type
        ctypeobj = CounterType.objects.filter( Q(branch=branch) & Q(name=countertype.name) )
        if not(ctypeobj.count() > 0) :
            status = dict({'status': 'Error'})
            msg =  dict({'msg':'Counter Type not found'})  
    if status == dict({}) :
        countertype = ctypeobj[0]
        cstatusobj = CounterStatus.objects.filter( Q(countertype=countertype) & Q(counternumber=counterstatus.counternumber) & Q(user=user))
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
                tt = ticket.tickettype + ','
                if mask.find(tt) != -1:
                    # call this ticket
                    context = {'priority': priority, 'mask': mask, 'tickettype': ticket.tickettype, 'ticketnumber': ticket.ticketnumber , 'tickettime': ticket.tickettime}
                    break
        elif priority == 'mask':
            ticketlist = TicketTemp.objects.filter( Q(branch=branch) & Q(countertype=countertype) & Q(status=lcounterstatus[0])  & Q(locked=False)   ).order_by('tickettime')
            istart = 0
            for i in range(len(mask)):
                if mask[i] == ',':
                    tt = mask[istart:i+1] # tt = 'A,'
                    istart = i + 1
                    for ticket in ticketlist:
                        if tt == ticket.tickettype + ',':
                            # call this ticket
                            context = {'priority': priority, 'mask': mask, 'tickettype': ticket.tickettype, 'ticketnumber': ticket.ticketnumber , 'tickettime': ticket.tickettime}
                            break
                    if context != dict({}):
                        break

            # for tt in mask:
            #     for ticket in ticketlist:
            #         if tt == ticket.tickettype:
            #             # call this ticket
            #             context = {'priority': priority, 'mask': mask, 'tickettype': ticket.tickettype, 'ticketnumber': ticket.ticketnumber , 'tickettime': ticket.tickettime}
            #             break
            #     if context != dict({}):
            #         break
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
                ticket.ticketroute.waiting = ticket.ticketroute.waiting - 1
                ticket.ticketroute.save()
                ticket.save()

                # add ticketlog
                TicketLog.objects.create(
                    tickettemp=ticket,
                    logtime=datetime_now,
                    app = rx_app,
                    version = rx_version,
                    logtext= logtext + branch.bcode + '_' + ticket.tickettype + '_'+ ticket.ticketnumber + '_' + datetime_now.strftime('%Y-%m-%dT%H:%M:%S.%fZ') ,
                    user=user,
                )

                # do display and voice temp db
                newdisplayvoice(branch, countertype, counterstatus.counternumber, ticket, datetime_now, user)

                # websocket to web tv
                wssendwebtv(branch.bcode ,countertype.name)
                # websocket to softkey (update Queue List)
                wssendql(branch.bcode, countertype.name, ticket, 'del')
                # websocket to web my ticket
                wsSendTicketStatus(branch.bcode, ticket.tickettype, ticket.ticketnumber, ticket.securitycode)
                # websocket to voice com
                wssendvoice(branch.bcode, countertype.name, ticket.tickettype, ticket.ticketnumber, counterstatus.counternumber)
                # websocket to web softkey for update counter status
                wscounterstatus(counterstatus)

        context = dict({'data':context})
        status = dict({'status': 'OK'})
        # msg =  dict({'msg':'Everything will be OK.'})        

    return status, msg, context

def funCounterProcess(user, branch, countertype, counterstatus, logtext, rx_app, rx_version, datetime_now):
    status = dict({})
    msg = dict({})

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
            logtext= logtext + branch.bcode + '_' + ticket.tickettype + '_'+ ticket.ticketnumber + '_' + datetime_now.strftime('%Y-%m-%dT%H:%M:%S.%fZ') ,
            user=user,
        )
        # websocket to web softkey for update counter status
        wscounterstatus(counterstatus)

        status = dict({'status': 'OK'})
        msg =  dict({'msg':'Process ticket.'})
    return status, msg

def funCounterComplete(user, branch, countertype, counterstatus, logtext, rx_app, rx_version, datetime_now):
    status = dict({})
    msg = dict({})

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
        routeobj = TicketRoute.objects.filter(branch=branch, step=nextstep, tickettype=ticket.tickettype)       

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
                logtext=logtext + branch.bcode + '_' + ticket.tickettype + '_'+ ticket.ticketnumber + '_' + datetime_now.strftime('%Y-%m-%dT%H:%M:%S.%fZ') ,
                user=user,
            )

        else:
            # next step
            route = routeobj[0] 
            route.waiting = route.waiting + 1
            route.save()

            countertype = route.countertype
            ticket.countertype = countertype
            ticket.ticketroute = routeobj[0]
            ticket.status = lcounterstatus[0]
            ticket.step = nextstep
            ticket.save()

            # websocket to softkey (update Queue List)
            wssendql(branch.bcode, countertype.name, ticket, 'add')
            # websocket to webtv
            wssendwebtv(branch.bcode, countertype.name)

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
                logtext= 'Next step ' + logtext + branch.bcode + '_' + ticket.tickettype + '_'+ ticket.ticketnumber + '_' + datetime_now.strftime('%Y-%m-%dT%H:%M:%S.%fZ') ,
                user=user,
            )
        # websocket to web my ticket
        wsSendTicketStatus(branch.bcode, ticket.tickettype, ticket.ticketnumber, ticket.securitycode)
        # websocket to web softkey for update counter status
        wscounterstatus(counterstatus)

        status = dict({'status': 'OK'})
        msg =  dict({'msg':'Ticket done.'})
    return status, msg

def funCounterMiss(user, branch, countertype, counterstatus, logtext, rx_app, rx_version, datetime_now):
    status = dict({})
    msg = dict({})

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
            logtext=logtext + branch.bcode + '_' + ticket.tickettype + '_'+ ticket.ticketnumber + '_' + datetime_now.strftime('%Y-%m-%dT%H:%M:%S.%fZ') ,
            user=user,
        )

        # websocket to web my ticket
        wsSendTicketStatus(branch.bcode, ticket.tickettype, ticket.ticketnumber, ticket.securitycode)
        # websocket to web softkey for update counter status
        wscounterstatus(counterstatus)

        status = dict({'status': 'OK'})
        msg =  dict({'msg':'Ticket no show.'})  
    return status, msg

def funCounterRecall(user, branch, countertype, counterstatus, logtext, rx_app, rx_version, datetime_now):
    status = dict({})
    msg = dict({})

    if status == dict({}) :
        # add ticketlog
        ticket = counterstatus.tickettemp 
        TicketLog.objects.create(
            tickettemp=ticket,
            logtime=datetime_now,
            app = rx_app,
            version = rx_version,
            logtext=logtext + branch.bcode + '_' + ticket.tickettype + '_'+ ticket.ticketnumber + '_' + datetime_now.strftime('%Y-%m-%dT%H:%M:%S.%fZ') ,
            user=user,
        )

        # do display and voice temp db
        newdisplayvoice(branch, countertype, counterstatus.counternumber, ticket, datetime_now, user)
        # websocket to web tv
        wssendwebtv(branch.bcode, countertype.name)
        # websocket to voice com
        wssendvoice(branch.bcode, countertype.name, ticket.tickettype, ticket.ticketnumber, counterstatus.counternumber)

        status = dict({'status': 'OK'})
        msg =  dict({'msg':'Recall ticket.'}) 
    return status, msg

def funCounterGet(getticket, getttype, gettnumber, user, branch, countertype, counterstatus, logtext, rx_app, rx_version, datetime_now):
    status = dict({})
    msg = dict({})
    context = dict({})
    ticket = None
    gettt = ''
    gettno = ''

    if getticket == '' :
        gettt = getttype
        gettno = gettnumber
    else:
        if status == dict({}) :
            if getticket == '':
                status = dict({'status': 'Error'})
                msg =  dict({'msg':'Please input ticket'})
        if status == dict({}) :
            # split getticket to gettt and gettno
            for i in range(len(getticket)):
                if getticket[i].isalpha() == False:
                    gettt = getticket[0:i]
                    gettno = getticket[i:]
                    break
    if status == dict({}) :
        if gettt == '':
            status = dict({'status': 'Error'})
            msg =  dict({'msg':'Please input ticket type.'})
    # check gettt is letter only
    if status == dict({}) :
        if gettt.isalpha() == False:
            status = dict({'status': 'Error'})
            msg =  dict({'msg':'Ticket type must be letter only.'})
    if status == dict({}) :
        if gettno == '':
            status = dict({'status': 'Error'})
            msg =  dict({'msg':'Please input ticket number.'})
    if status == dict({}) :
        # check gettno is number only
        if gettno.isnumeric() == False:
            status = dict({'status': 'Error'})
            msg =  dict({'msg':'Ticket number must be number only.'})        
    if status == dict({}) :
        # change gettno to "000" format and convert to string
        tformat = counterstatus.countertype.branch.ticketnoformat 
        gettno = tformat + str(gettno)
        # get gettno string right 3 char
        gettno = gettno[-len(tformat):]



    if status == dict({}) :
        # find ticket in waiting list
        objt = TicketTemp.objects.filter(
            tickettype=gettt,
            ticketnumber=gettno,
            branch=branch,
            status='waiting',
            locked=False).order_by('-tickettime')
        if objt.count() >= 1 :
            ticket = objt[0]
        else:
            # find ticket in miss list
            objt = TicketTemp.objects.filter(
                tickettype=gettt,
                ticketnumber=gettno,
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
        
        # waiting on queue
        if ticket.status == 'waiting':
            ticket.ticketroute.waiting = ticket.ticketroute.waiting - 1
            ticket.ticketroute.save()
            # websocket to softkey (update Queue List)
            wssendql(branch.bcode, countertype.name, ticket, 'del')
        ticket.user = user
        ticket.status = 'calling'
        ticket.save()
        

        # add ticketlog
        TicketLog.objects.create(
            tickettemp=ticket,
            logtime=datetime_now,
            app = rx_app,
            version = rx_version,
            logtext=logtext  + branch.bcode + '_' + ticket.tickettype + '_'+ ticket.ticketnumber + '_' + ticket.tickettime.strftime('%Y-%m-%dT%H:%M:%S.%fZ') ,
            user=user,
        )

        # do display and voice temp db
        newdisplayvoice(branch, countertype, counterstatus.counternumber, ticket, datetime_now, user)
        # websocket to web my ticket
        wsSendTicketStatus(branch.bcode, ticket.tickettype, ticket.ticketnumber, ticket.securitycode)
        # websocket to voice com
        wssendvoice(branch.bcode, countertype.name, ticket.tickettype, ticket.ticketnumber, counterstatus.counternumber)
        # websocket to web softkey for update counter status
        wscounterstatus(counterstatus)

        context = {'tickettype': ticket.tickettype, 
                   'ticketnumber': ticket.ticketnumber , 
                   'tickettime': ticket.tickettime}
        context = dict({'data':context})
        status = dict({'status': 'OK'})
        msg =  dict({'msg':'Ticket Get.'})
    return status, msg, context

def funCounterLogout(counterstatus, datetime_now):
    logoutOK = logcounterlogout(counterstatus.user, counterstatus.countertype, counterstatus.counternumber, counterstatus.logintime, datetime_now)
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
    return status, msg

def funCounterLogin(datetime_now, user, branch, counterstatus, rx_counternumber, countertype):
    status = dict({})
    msg = dict({})
    context = dict({})
    

    if status == dict({}) :
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
    
    ttype=''
    tno = ''
    ttime=''
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


                    if counterstatus.tickettemp != None:
                        ttype = counterstatus.tickettemp.tickettype
                        tno = counterstatus.tickettemp.ticketnumber
                        ttime = counterstatus.tickettemp.tickettime

                    # context = {'name': user.first_name + ' ' + user.last_name , 'ttype': userp.tickettype, 'timezone': branch.timezone,
                    # 'counterstatus':counterstatus.status, 'tickettype':ttype, 'ticketnumber':tno, 'tickettime':ttime,
                    # 'ticketnoformat':branch.ticketnoformat,
                    # }
                    # context = dict({'data':context})    
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

                    if counterstatus.tickettemp != None:
                        ttype = counterstatus.tickettemp.tickettype
                        tno = counterstatus.tickettemp.ticketnumber
                        ttime = counterstatus.tickettemp.tickettime

                    # context = {'name': user.first_name + ' ' + user.last_name , 'ttype': userp.tickettype, 'timezone': branch.timezone,
                    # 'counterstatus':counterstatus.status, 'tickettype':ttype, 'ticketnumber':tno, 'tickettime':ttime,
                    # 'ticketnoformat':branch.ticketnoformat,
                    # }
                    # context = dict({'data':context})    
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

                if counterstatus.tickettemp != None:
                    ttype = counterstatus.tickettemp.tickettype
                    tno = counterstatus.tickettemp.ticketnumber
                    ttime = counterstatus.tickettemp.tickettime

    context = {
        'branch':branch.name,
        'bcode':branch.bcode,
        'countertype':counterstatus.countertype.name, 
        'counternumber':counterstatus.counternumber,
        'name': user.first_name + ' ' + user.last_name , 
        'userttype': userp.tickettype, 
        'timezone': branch.timezone,
        'counterstatus':counterstatus.status, 
        'tickettype':ttype, 
        'ticketnumber':tno, 
        'tickettime':ttime,
        }
    context = dict({'data':context})
    return status, msg, context


def funVoid(user, tickett, td, datetime_now):
    # update ticket 
    # waiting on queue
    if tickett.status == 'waiting':
        tickett.ticketroute.waiting = tickett.ticketroute.waiting - 1
        tickett.ticketroute.save()
    tickett.user = user
    tickett.status = 'void'
    tickett.save()

    # update ticketdata db
    td.voidtime = datetime_now
    td.voiduser = user
    time_diff = datetime_now - td.starttime
    tsecs = int(time_diff.total_seconds())
    td.waitingperiod = tsecs
    td.save()

    # websocket to softkey (update Queue List)
    wssendql(tickett.branch.bcode , tickett.countertype.name, tickett, 'del')
    # websocket to web tv
    wssendwebtv(tickett.branch.bcode, tickett.countertype.name)
    # websocket to web my ticket
    wsSendTicketStatus(tickett.branch.bcode, tickett.tickettype, tickett.ticketnumber, tickett.securitycode)


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