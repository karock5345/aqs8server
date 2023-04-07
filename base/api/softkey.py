from datetime import datetime
from django.utils import timezone
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.db.models import Q
from .views import setting_APIlogEnabled, visitor_ip_address, loginapi, funUTCtoLocal, counteractive
from .v_display import newdisplayvoice
from base.models import APILog, Branch, CounterStatus, CounterType, DisplayAndVoice, Setting, TicketFormat, TicketTemp, TicketRoute, TicketData, TicketLog, CounterLoginLog, UserProfile, lcounterstatus
from .serializers import waitinglistSerivalizer
from base.ws import wssendwebtv, wssendql, wsSendTicketStatus, wssendvoice

# q: how to get pk from url in html?


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
        'countertype':counterstatus.countertype.name, 
        'counternumber':counterstatus.counternumber,
        'name': user.first_name + ' ' + user.last_name , 
        'ttype': userp.tickettype, 
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