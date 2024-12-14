from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db.models import Q
from base.models import Branch, CounterStatus, CounterType, Ticket, TicketFormat, TicketRoute, SystemLog, DisplayAndVoice, TicketTemp, TicketData, TicketLog, APILog, UserStatusLog
from base.models import SubTicket
# from .jobs import job_stop
from datetime import datetime, timedelta, timezone
import pytz
# from django.utils import timezone
from apscheduler.schedulers.background import BackgroundScheduler
from base.api.views import setting_APIlogEnabled, visitor_ip_address, loginapi, funUTCtoLocal, funLocaltoUTC, funLocaltoUTCtime, funUTCtoLocaltime
from base.ws import wssendwebtv, wscounterstatus, wssenddispremoveall
import logging
from .decorators import superuser_required
import time
from django.conf import settings
import os
import shutil
from base.sch.jobs import  job_stopall, job_testing
from aqs.settings import APP_NAME, aqs_version
from django.core.management import call_command
from django.core.management.base import CommandError
import base.a_global


logger = logging.getLogger(__name__)

job_defaults = {
    'coalesce': True,
    'misfire_grace_time': None,
    'daemon': True,
    'max_instances': 50,
}
sch = BackgroundScheduler(job_defaults=job_defaults)
# sch = BackgroundScheduler(daemon=True)

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

    datetime_now = datetime.now(timezone.utc)
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
    now = datetime.now(timezone.utc)
    now_u = funLocaltoUTC(now, 8)
    snow = now_u.strftime("%Y/%m/%d %H:%M:%S")
    logger.info(snow + '!!! Job run !!!')






def init_branch_reset():
    branch_count = 0
    datetime_now = datetime.now(timezone.utc)

    try:
        branchobj = Branch.objects.all()
        branch_count = branchobj.count()
    except:
        # print ('   -SCH- init_branch_reset Error : No Branch')
        if base.a_global.system_inited == True :
            SystemLog.objects.create(
                logtime=datetime_now,
                logtext ='UTC time:' + datetime_now.strftime('%H:%M:%S') + ' -SCH- init_branch_reset Error : No Branch',
                )

    if branch_count > 0:
        for branch in branchobj:
            sch_shutdown(branch, datetime_now)
            Reset_SMS(branch, datetime_now)


def Reset_SMS(branch, datetime_now):

    now_local:datetime = funUTCtoLocal(datetime_now, branch.timezone )
    now_str = now_local.strftime('%Y-%m-') + str(branch.SMSResetDay)
    if branch.SMSResetLast != now_str:
        branch.SMSResetLast = now_str
        branch.SMSUsed = 0
        branch.save()
        logger.info('-SCH- Reset SMS Used to 0 [' + branch.bcode + '] -SCH-')

def sch_shutdown(branch_input, nowUTC):
    branch = Branch.objects.get(id=branch_input.id)

    now = datetime.now(timezone.utc)
    datetime_now = nowUTC
    localtime_now = funUTCtoLocaltime(datetime_now, branch.timezone )
    localtime = funUTCtoLocaltime( branch.officehourend, branch.timezone )

    slocaltime = datetime.now(timezone.utc).strftime('%Y-%m-%d ') + localtime.strftime('%H:%M:%S')
    localtime = datetime.strptime(slocaltime, '%Y-%m-%d %H:%M:%S')
    localtime = pytz.utc.localize(localtime)

    snextreset = datetime.now(timezone.utc).strftime('%Y-%m-%d ') + branch.officehourend.strftime('%H:%M:%S')
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

    if base.a_global.system_inited == True :
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
    datetime_now =datetime.now(timezone.utc)
    localtime_now = funUTCtoLocaltime(datetime_now, branch.timezone )
    bcode = branch.bcode

    logger.info('   -SCH- Shutdown and reset branch :' + bcode + ' -SCH-')
    if base.a_global.system_inited == True :
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

    # all ticket .locked=ture
    ttobj = TicketTemp.objects.filter( Q(branch=branch))
    for tt in ttobj:
        tt.locked = True
        tt.save()

        # copy data from TicketTemp to Ticket
        ticket = tt.ticket
        ticket.tickettype = tt.tickettype
        ticket.tickettype_disp = tt.tickettype_disp
        ticket.ticketnumber_disp = tt.ticketnumber_disp

        ticket.ticketnumber = tt.ticketnumber
        ticket.branch = tt.branch
        ticket.step = tt.step
        ticket.countertype = tt.countertype
        ticket.ticketroute = tt.ticketroute

        # Status = 'waiting', 'calling', 'processing' then force to 'miss' (no show)
        # Final status = 'done', 'void', 'miss'
        ticket.status = tt.status
        if tt.status == 'done' or tt.status == 'void' or tt.status == 'miss':
            pass
        else:
            ticket.status = 'miss'
            # TicketData should be add misstime and add TicketLog
            td = None
            try:
                td = TicketData.objects.get(tickettemp=tt)
            except:
                logger.error('@base->sch->views.py->job_shutdown: TicketData not found (' + tt.branch.bcode + '_' + tt.tickettype + '_' + tt.ticketnumber + ')')
            if td != None:
                td.misstime = datetime_now
                # cal waiting time between tickettime and misstime and add to td.waitingperiod
                seconds = (td.misstime - td.starttime).total_seconds()
                td.waitingperiod = seconds
                td.save()
            # cal waiting time between tickettime and misstime and add to td.waitingperiod
            seconds = (td.misstime - td.starttime).total_seconds()
            td.waitingperiod = seconds
            td.save()
            # add TicketLog
            localdate_now = funUTCtoLocal(datetime_now, branch.timezone )
            TicketLog.objects.create(
                ticket = ticket,
                tickettemp = tt,
                app = APP_NAME,
                version = aqs_version,
                logtime = datetime_now,
                logtext = 'Miss ticket by branch shutdown ' + tt.branch.bcode + '_' + tt.tickettype + '_'+ tt.ticketnumber + '_' + localdate_now.strftime('%Y-%m-%d_%H:%M:%S') ,
                user = None,
            )

        ticket.locked = True
        ticket.tickettime = tt.tickettime
        ticket.tickettext = tt.tickettext
        ticket.printernumber = tt.printernumber
        ticket.printedtimes = tt.printedtimes
        ticket.user = tt.user
        ticket.remark = tt.remark

        ticket.booking_tickettype = tt.booking_tickettype
        ticket.booking_ticketnumber = tt.booking_ticketnumber
        ticket.booking_time = tt.booking_time
        ticket.booking_name = tt.booking_name
        ticket.booking_user = tt.booking_user
        ticket.booking_id = tt.booking_id

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

    # remove SubTicket table
    SubTicket.objects.filter(Q(branch=branch)).delete()

    # remove TicketTemp table
    ttobj = TicketTemp.objects.filter( Q(branch=branch) & Q(locked=True)).delete()

    # del all DisplayAndVoice branch=branch
    DisplayAndVoice.objects.filter( Q(branch=branch)).delete()

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
            elif counter.countertype.countermode == 'cc' :
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

    sub_booking_temp(branch, None)

    sch_shutdown(branch, datetime_now)


def sch_bookingtemp(hours):
    sch_id = 'sch_bookingtemp'
    mins = 60 * hours
    sch.add_job(job_booking_temp, 'interval', args=[None,None,mins], minutes=mins, id=sch_id)
    logger.info('-SCH- Add job_booking_temp every ' + str(hours) + ' hours -SCH-')

def job_booking_temp(branch:Branch, input_temp, mins):
    now = datetime.now(timezone.utc)
    # now_l = funUTCtoLocal(now, branch.timezone)
    # snow = now_l.strftime("%m/%d/%Y, %H:%M:%S")
    snow2 = now.strftime("%m/%d/%Y, %H:%M:%S")
    # text_out = '   -SCH- Now:' + snow2 + ' Local time:' +  snow + ' Sch Booking Template - ' +  '-SCH-'
    text_out = '   -SCH- Sch Booking Template (Loop every ' + str(mins) +  ' mins) -SCH-'
    # print ( text_out )
    logger.info(text_out)
    sub_booking_temp(branch, input_temp)


def sub_booking_temp(branch:Branch, input_temp):
    from booking.models import TimeslotTemplate, TempLog, TimeSlot

    if branch == None and input_temp == None:
        temps = TimeslotTemplate.objects.all()
    elif branch != None:
        temps = TimeslotTemplate.objects.filter(branch=branch)
    elif input_temp != None:
        temps = TimeslotTemplate.objects.filter(id=input_temp.id)
    for temp in temps:
            error = ''
            if error == '':
                if temp.branch.enabled == False:
                    error = 'Branch is disabled'
            if error == '':
                if temp.enabled == False:
                    error = 'Timeslot is disabled'
            if error == '':
                if temp.branch.bookingenabled == False:
                    error = 'Booking function is disabled'
            if error == '':
                items = temp.items.all()
                for item in items:
                    error = ''
                    # check item is already make a booking
                    hour = item.start_time.hour
                    minute = item.start_time.minute
                    second = item.start_time.second
                    nowutc = datetime.now(timezone.utc)
                    year = nowutc.year
                    month = nowutc.month
                    day = nowutc.day

                    start_date = datetime(year, month, day, 0, 0, 0)
                    start_date = start_date + timedelta(days=temp.show_day_before + temp.create_before)
                    start_date = start_date + timedelta(hours=hour)
                    start_date = start_date + timedelta(minutes=minute)
                    start_date = start_date + timedelta(seconds=second)
                    start_date = datetime(start_date.year, start_date.month, start_date.day, hour, minute, second)

                    # print('start_date:', start_date)
                    log = TempLog.objects.filter(
                        Q(bookingtemplate=temp) &
                        Q(item=item) &
                        Q(year=year) &
                        Q(month=month) &
                        Q(day=day) &
                        Q(hour=hour) &
                        Q(min=minute) &
                        Q(second=second)
                    )

                    if error == '':
                        if log.count() > 0:
                            error = 'Timeslot is already make a booking'


                    if error == '':
                        # print('start_time:', start_date)
                        # Get the abbreviated day of the week
                        day_of_week = start_date.strftime('%a')
                        # print('day_of_week:', day_of_week)

                        day_of_week_bool = False
                        if day_of_week == 'Mon':
                            if temp.monday == True:
                                day_of_week_bool = True
                        elif day_of_week == 'Tue':
                            if temp.tuesday == True:
                                day_of_week_bool = True
                        elif day_of_week == 'Wed':
                            if temp.wednesday == True:
                                day_of_week_bool = True
                        elif day_of_week == 'Thu':
                            if temp.thursday == True:
                                day_of_week_bool = True
                        elif day_of_week == 'Fri':
                            if temp.friday == True:
                                day_of_week_bool = True
                        elif day_of_week == 'Sat':
                            if temp.saturday == True:
                                day_of_week_bool = True
                        elif day_of_week == 'Sun':
                            if temp.sunday == True:
                                day_of_week_bool = True
                        if day_of_week_bool == False:
                            error = 'Day of week is not selected'

                    if error == '':
                        # make a new timeslot
                        # print('start_date:', start_date)
                        # change to UTC datetime
                        start_date = funLocaltoUTC(start_date, temp.branch.timezone)
                        # print('start_date (UTC):', start_date)
                        end_date = start_date + timedelta(minutes=(item.service_mins + (item.service_hours * 60)))
                        # print('end_date (UTC):', end_date)
                        # print('Minute:', minute)
                        # print('Hour:', hour)
                        # print('Total minute:', minute + (hour * 60))
                        show_date = start_date - timedelta(days=temp.show_day_before)
                        show_end_date = show_date + timedelta(days=temp.show_period)

                        timeslot = TimeSlot.objects.create(
                            branch = temp.branch,
                            start_date = start_date,
                            end_date = end_date,
                            enabled = True,
                            slot_total = item.slot_total,
                            slot_available = item.slot_total,
                            slot_using = 0,
                            show_date = show_date,
                            show_end_date = show_end_date,
                            user = temp.user,
                            created_by_temp = True,
                        )

                        # create new log
                        TempLog.objects.create(
                            bookingtemplate = temp,
                            item = item,
                            year = year,
                            month = month,
                            day = day,
                            hour = hour,
                            min = minute,
                            second = second,
                        )
                    # if error != '':
                    #     print('Error:', error)
                    # else :
                    #     print('Success')

def check_pending_migrations():
    error = ''
    migrations_needed = False
    try:
        # Simulate makemigrations to check for pending migrations without creating them
        call_command('makemigrations', '--dry-run', '--check')
        migrations_needed = False
    except SystemExit as e:
        # If the command exits with a non-zero status, migrations are needed
        if e.code != 0:
            migrations_needed = True
        else:
            migrations_needed = False
    except CommandError as e:
        # Handle other potential errors, such as misconfiguration
        error = 'error : ' + str(e)

    return migrations_needed, error

def main():
    pass

if __name__ != '__main__':
    main()