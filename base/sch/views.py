from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db.models import Q
from base.models import Branch, CounterStatus, CounterType, Ticket, TicketFormat, TicketRoute, SystemLog, DisplayAndVoice, TicketTemp, TicketData, TicketLog, APILog, UserStatusLog
# from .jobs import job_stop
from datetime import datetime, timedelta
import pytz
from django.utils import timezone
from apscheduler.schedulers.background import BackgroundScheduler
from base.api.views import setting_APIlogEnabled, visitor_ip_address, loginapi, funUTCtoLocal, funLocaltoUTC, funLocaltoUTCtime, funUTCtoLocaltime
from base.ws import wssendwebtv, wscounterstatus, wssenddispremoveall
import logging
from .decorators import superuser_required
import time
from django.conf import settings
import os
import shutil

logger = logging.getLogger(__name__)

datetime_now =timezone.now()
system_inited = False
try:
    SystemLog.objects.create(
            logtime=datetime_now,
            logtext =  'System started',
        )
    system_inited = True
except:
    system_inited = False

logger.info('-SCH- Schedule INIT start @ base.sch.view.py -SCH-')
now = timezone.now()
snow = now.strftime("%m/%d/%Y, %H:%M:%S")
logger.info('-SCH- Now:' + snow)
sch = BackgroundScheduler(daemon=True)
sch.start()


# Sch

# Shutdown the branch and run init_branch
# http://127.0.0.1:8000/sch/shutdown/?bcode=KB
@api_view(['GET'])
@permission_classes([IsAuthenticated])
@superuser_required
def getShutdown(request):
    error = ''
    bcode = request.GET.get('bcode') if request.GET.get('bcode') != None else ''
    rx_app = request.GET.get('app') if request.GET.get('app') != None else ''
    rx_version = request.GET.get('version') if request.GET.get('version') != None else ''

    
    if error == '' :
        if bcode == '' :
            error ='Branch code is empty'
    if error == '' :
        try :
            branch = Branch.objects.get(bcode=bcode)
        except :
            error = 'Branch not found'
    
    if error == '' :
        # Save Api Log
        if setting_APIlogEnabled(branch) == True :
            APILog.objects.create(
                logtime=datetime_now,
                requeststr = request.build_absolute_uri() ,
                ip = visitor_ip_address(request),
                app = rx_app,
                version = rx_version,
                logtext = 'API call : Shutdown branch ' + bcode + ' and init',
            )


    if error == '' :
        if branch != None :
            job_shutdown(branch)
        else :
            error = 'Branch not found'
    if error == '' :
        return Response('OK, Branch shutdown and init')
    else :
        return Response(error)


@api_view(['GET'])
def getRoutes(request):
    routes = [
        'This is working on Sch',
    ]
    # job_testing(10, '10 Seconds', ' 0')
    
    return Response(routes)

@api_view(['GET'])
def getJobTesting(request):
    in_time = request.GET.get('time') if request.GET.get('time') != None else ''

    # stickettime = str(datetime.strptime(in_time, '%Y-%m-%dT%H:%M:%SZ' )) 
    rx_tickettime = datetime.strptime(in_time, '%Y-%m-%dT%H:%M:%S%z')


    in_time_u = funLocaltoUTC(rx_tickettime, 8)
    logger.info(in_time_u)
    sch.add_job(job_test_trigger, 'date', run_date=in_time_u) 

    return Response('Job testing')

def job_test_trigger():
    now = timezone.now()
    now_u = funLocaltoUTC(now, 8)
    snow = now_u.strftime("%Y/%m/%d %H:%M:%S")
    logger.info(snow + '!!! Job run !!!')




def job(text,text2):    
    now = timezone.now()
    now_l = funUTCtoLocal(now, 8)
    snow = now_l.strftime("%m/%d/%Y, %H:%M:%S")
    snow2 = now.strftime("%m/%d/%Y, %H:%M:%S")
    text_out = '   -SCH- Now:' + snow2 + ' Local time:' +  snow + ' Testing job - ' + text + text2 + '-SCH-'

    # print ( text_out )    
    logger.info(text_out)

def job_testing(input, text, text2):
    txt_job = 'job_' + text
    sch.add_job(job, 'interval', args=[text,text2], seconds=input, id=txt_job)

def init_branch_reset():
    branch_count = 0    
    datetime_now =timezone.now()

    try:
        branchobj = Branch.objects.all()
        branch_count = branchobj.count()
    except:
        print ('   -SCH- init_branch_reset Error : No Branch')        
        if system_inited == True :
            SystemLog.objects.create(
                logtime=datetime_now,
                logtext ='UTC time:' + datetime_now.strftime('%H:%M:%S') + ' -SCH- init_branch_reset Error : No Branch',
                )

    if branch_count > 0:
        for branch in branchobj:
            sch_shutdown(branch, datetime_now)


def sch_shutdown(branch, nowUTC):
    datetime_now = nowUTC
    localtime_now = funUTCtoLocaltime(datetime_now, branch.timezone )      
    localtime = funUTCtoLocaltime( branch.officehourend, branch.timezone )
    
    slocaltime = timezone.now().strftime('%Y-%m-%d ') + localtime.strftime('%H:%M:%S')
    localtime = datetime.strptime(slocaltime, '%Y-%m-%d %H:%M:%S')
    localtime = pytz.utc.localize(localtime)

    snextreset = timezone.now().strftime('%Y-%m-%d ') + branch.officehourend.strftime('%H:%M:%S')
    nextreset = datetime.strptime(snextreset, '%Y-%m-%d %H:%M:%S')
    nextreset = pytz.utc.localize(nextreset)
    
    logtemp1 = '   -SCH- ' + nextreset.strftime('%Y-%m-%d %H:%M:%S') + ' > ' + now.strftime('%Y-%m-%d %H:%M:%S')            
    if nextreset > now :
        logtemp1 = logtemp1 + ' [Yes]'
        pass                    
    else:
        nextreset  = nextreset + timedelta(hours=24)
        logtemp1 = logtemp1 + ' [No]'

    logtemp2 =  '   -SCH- reset time: ' + branch.officehourend.strftime('%H:%M:%S') + ' Local Time: '+ localtime.strftime('%H:%M:%S') 
    
    nextreset_local = funUTCtoLocal(nextreset, branch.timezone )
    logtemp3 = ' -SCH- Next reset [' + branch.bcode + ']: ' + nextreset.strftime('%Y-%m-%d %H:%M:%S') + ' Local:' + nextreset_local.strftime('%Y-%m-%d %H:%M:%S') 
    
    logger.info(logtemp3)
    logger.info(logtemp2)
    logger.info(logtemp1)

    # print (logtemp3)
    # print (logtemp2)
    # print (logtemp1)

    if system_inited == True :
        SystemLog.objects.create(
            logtime = datetime_now,
            logtext = 'Local time:' + localtime_now.strftime('%H:%M:%S') + logtemp3 + '\n' + logtemp2 + '\n' + logtemp1
            )
    # before add job must check the job is exist or not
    if sch.get_job(branch.bcode) != None :
        # if exist remove it
        sch.remove_job(branch.bcode)        
    sch.add_job(job_shutdown, 'date', run_date=nextreset, id=branch.bcode, args=[branch])


def job_shutdown(branch):
    datetime_now =timezone.now()
    localtime_now = funUTCtoLocaltime(datetime_now, branch.timezone )
    bcode = branch.bcode

    logger.info('   -SCH- Shutdown and reset branch :' + bcode + ' -SCH-')
    if system_inited == True :
        SystemLog.objects.create(
            logtime = datetime_now,
            logtext = 'Local time:' + localtime_now.strftime('%H:%M:%S') + ' -SCH- Shutdown and reset branch :' + bcode + ' -SCH-'
            )   
    
    # delete files /download/bcode/*
    static_root = str(settings.STATICFILES_DIRS[0])
    path = static_root + '/download/' + bcode + '/'
    if os.path.exists(path):
        shutil.rmtree(path)
    
    # reset to branch.ticketnext 1
    branch.ticketnext = 1
    branch.save()

    # reset to ticketformat.ticketnext 1    
    # number of waiting on queue reset to 0
    tfobj = TicketFormat.objects.filter( Q(branch=branch)  )
    for tf in tfobj:
        tf.ticketnext = 1
        tf.save()

    # reset ticketroute waiting = 0
    trobj = TicketRoute.objects.filter(Q(branch=branch))
    for tr in trobj:        
        tr.displastticketnumber = ''
        tr.displastcounter = ''
        tr.waiting = 0        
        tr.save()
        route = tr
        logger.info(route.branch.bcode + '-' + route.countertype.name + '-' + route.tickettype + ' (reset 0) route.waiting = ' + str(route.waiting))

    # all ticket .locked=ture
    ttobj = TicketTemp.objects.filter( Q(branch=branch))
    for tt in ttobj:
        tt.locked = True
        tt.save()

        # copy data from TicketTemp to Ticket
        ticket = tt.ticket
        ticket.tickettype = tt.tickettype
        ticket.ticketnumber = tt.ticketnumber
        ticket.branch = tt.branch        
        ticket.step = tt.step
        ticket.countertype = tt.countertype
        ticket.ticketroute = tt.ticketroute
        ticket.status = tt.status        
        ticket.locked = tt.locked
        ticket.tickettime = tt.tickettime
        ticket.tickettext = tt.tickettext
        ticket.printernumber = tt.printernumber
        ticket.printedtimes = tt.printedtimes
        ticket.user = tt.user
        ticket.remark = tt.remark
        ticket.save()

        # TicketData mark ticket
        tdobj = TicketData.objects.filter(Q(tickettemp=tt))
        for td in tdobj:
            td.ticket = ticket
            td.save()                

        # TicketLog mark ticket
        tlobj = TicketLog.objects.filter(Q(tickettemp=tt))
        for tl in tlobj:
            tl.ticket = ticket
            tl.save() 

    # remove TicketTemp table
    ttobj = TicketTemp.objects.filter( Q(branch=branch) & Q(locked=True))
    for ticket in ttobj:
        ticket.delete()


    # del all DisplayAndVoice branch=branch
    dvobj = DisplayAndVoice.objects.filter( Q(branch=branch))
    for dv in dvobj:
        dv.delete()

    # websocket to web tv
    ctobj = CounterType.objects.filter(Q(branch=branch))
    for countertype in ctobj:
        wssendwebtv(bcode,countertype.name)
        wssenddispremoveall(branch, countertype)

    # counterstatus all reset to 'waiting'
    csobj = CounterStatus.objects.all()
    for counter in csobj:
        if counter.countertype.branch == branch:
            if counter.countertype.countermode == 'normal' :
                # counterstatus all reset to 'waiting'
                if counter.loged == True and counter.user != None :
                    if counter.status != 'waiting':                        
                        counter.status = 'waiting'
                        counter.save()
            else:
                # Call center mode
                # counterstatus all reset to 'AUX'
                if counter.loged == True and counter.user != None :
                    if counter.status != 'AUX':
                        objusl = UserStatusLog.objects.filter( Q(user=counter.user) & Q(endtime=None) & ~Q(status='login') )
                        if objusl.count() > 0 :
                            for usl in objusl:
                                usl.endtime = datetime_now
                                usl.save()  

                        counter.status = 'AUX'
                        counter.save()
                        # add user status log 'walking' status
                        UserStatusLog.objects.create(
                            user = counter.user,
                            starttime = datetime_now,
                            status = 'AUX',
                        )
                        # websocket to web softkey for update counter status
                        wscounterstatus(counter)

    # stop all job
    # sch.remove_all_jobs()
    # branchobj = Branch.objects.all()
    # for b in branchobj:
    #     if b != branch:
    #         sch.remove_job(b.bcode)
    
    # init_branch_reset()


    # add delay 1 second for testing
    # time.sleep(1)

    sch_shutdown(branch, datetime_now)
    


def job(text,text2):    
    now = timezone.now()
    now_l = funUTCtoLocal(now, 8)
    snow = now_l.strftime("%m/%d/%Y, %H:%M:%S")
    snow2 = now.strftime("%m/%d/%Y, %H:%M:%S")
    text_out = '   -SCH- Now:' + snow2 + ' Local time:' +  snow + ' Testing job - ' + text + text2 + '-SCH-'

    # print ( text_out )    
    logger.info(text_out)

def job_testing(input, text, text2):
    txt_job = 'job_' + text
    sch.add_job(job, 'interval', args=[text,text2], seconds=input, id=txt_job)

