from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.db.models import Q
from base.models import Branch, CounterStatus, CounterType, Ticket, TicketFormat, TicketRoute, SystemLog, DisplayAndVoice, TicketTemp, TicketData, TicketLog
# from .jobs import job_stop
from datetime import datetime, timedelta
import pytz
from django.utils import timezone
from apscheduler.schedulers.background import BackgroundScheduler
from base.api.views import setting_APIlogEnabled, visitor_ip_address, loginapi, funUTCtoLocal, funLocaltoUTC, funLocaltoUTCtime, funUTCtoLocaltime
from base.ws import wssendwebtv
import logging

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
# print('-SCH- Schedule INIT start @ base.sch.view.py -SCH-')
logger.info('-SCH- Schedule INIT start @ base.sch.view.py -SCH-'
            )
now = timezone.now()
snow = now.strftime("%m/%d/%Y, %H:%M:%S")
# print('-SCH- Now:' + snow)
logger.info('-SCH- Now:' + snow)
sch = BackgroundScheduler(daemon=True)
sch.start()


# Sch
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
    # print(in_time_u)
    logger.info(in_time_u)
    sch.add_job(job_test_trigger, 'date', run_date=in_time_u) 

    return Response('Job testing')

def job_test_trigger():
    now = timezone.now()
    now_u = funLocaltoUTC(now, 8)
    snow = now_u.strftime("%Y/%m/%d %H:%M:%S")
    logger.info(snow + '!!! Job run !!!')
    # print(snow + '!!! Job run !!!')


def init_branch_reset():
    branch_count = 0    

    try:
        branchobj = Branch.objects.all()
        branch_count = branchobj.count()
    except:
        print ('   -SCH- init_branch_reset Error : No Branch')        
        if system_inited == True :
            SystemLog.objects.create(
                logtime=datetime_now,
                logtext ='Local time:' + localtime_now.strftime('%H:%M:%S') + ' -SCH- init_branch_reset Error : No Branch',
                )

    now = timezone.now()    
    if branch_count > 0:
        for branch in branchobj:
            datetime_now =timezone.now()
            localtime_now = funUTCtoLocaltime(datetime_now, branch.timezone )

            # print(branch.officehourend, branch.timezone)        
            localtime = funUTCtoLocaltime( branch.officehourend, branch.timezone )
            
            # print('hello ' + str(type( branch.officehourend)  )) # <class 'datetime.time'>
            # print('hello ' + str(type( localtime )  )) # <class 'datetime.time'>
            slocaltime = timezone.now().strftime('%Y-%m-%d ') + localtime.strftime('%H:%M:%S')
            localtime = datetime.strptime(slocaltime, '%Y-%m-%d %H:%M:%S')
            localtime = pytz.utc.localize(localtime)

            snextreset = timezone.now().strftime('%Y-%m-%d ') + branch.officehourend.strftime('%H:%M:%S')
            nextreset = datetime.strptime(snextreset, '%Y-%m-%d %H:%M:%S')
            nextreset = pytz.utc.localize(nextreset)
            
            logtemp1 = '   -SCH- ' + nextreset.strftime('%Y-%m-%d %H:%M:%S') + ' > ' + now.strftime('%Y-%m-%d %H:%M:%S')            
            if nextreset > now :
                logtemp1 = logtemp1 + ' [Yes]'
                # print('reset is ' + snextreset)
                pass                    
            else:
                # print('reset is +24h of ' + snextreset)
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
            sch.add_job(job_shutdown, 'date', run_date=nextreset, id=branch.bcode, args=[branch])

def job_shutdown(branch):
    datetime_now =timezone.now()
    localtime_now = funUTCtoLocaltime(datetime_now, branch.timezone )
    bcode = branch.bcode

    print('   -SCH- Shutdown and reset branch :' , bcode, ' -SCH-')
    if system_inited == True :
        SystemLog.objects.create(
            logtime = datetime_now,
            logtext = 'Local time:' + localtime_now.strftime('%H:%M:%S') + ' -SCH- Shutdown and reset branch :' + bcode + ' -SCH-'
            )   
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


    # counterstatus all reset to 'waiting'
    csobj = CounterStatus.objects.all()
    for counter in csobj:
        if counter.countertype.branch == branch:
            counter.status = 'waiting'
            counter.save()


    # add new job
    branchobj = Branch.objects.all()
    for b in branchobj:
        if b != branch:
            sch.remove_job(b.bcode)
    
    init_branch_reset()


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

