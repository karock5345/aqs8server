import threading

from base.models import *
import csv
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import User, Group
from django.db import connection
import logging
import pytz
from dateutil import tz

logger = logging.getLogger(__name__)


# Convert Locate datetime to UTC
# def funLocaltoUTC(dInput, zone) -> datetime :    
#     # ts = datetime.mktime(dInput.timetuple())
#     # utc = datetime.utcfromtimestamp(ts) 
#     UTC_zone = tz.gettz('UTC')
#     local_zone = tz.gettz(zone)
    
#     localtime = dInput.replace(tzinfo=local_zone)

#     utc = localtime.astimezone(UTC_zone)

#     return utc
class MigrateDBThreadtst(threading.Thread):

    def __init__(self, branch, staff_file, maindb_file, userlog_file):
        self.branch = branch
        self.staff_file = staff_file
        self.maindb_file = maindb_file
        self.userlog_file = userlog_file
        threading.Thread.__init__(self)
    
    def run(self):        
        try:
            for index in range(1, 2):
                error = ''
                bcode = ''
                staff_file = ''
                maindb_file = ''
                userlog_file = ''
                if index == 1:
                    bcode = 'HHT'

                    staff_file = './base/api/tst/staff.csv'
                    maindb_file = './base/api/tst/main.csv'
                    userlog_file = './base/api/tst/userlog.csv'


                if error == '':
                    try:
                        branch = Branch.objects.get(bcode=bcode)
                    except:
                        error = 'Branch not found' + bcode
                if error == '':
                    try:
                        f = open(staff_file)
                    except:
                        error = 'File not found:' + staff_file
                if error == '':
                    try:
                        f = open(maindb_file)
                    except:
                        error = 'File not found:' + maindb_file
                if error == '':
                    try:
                        f = open(userlog_file)
                    except:
                        error = 'File not found:' + userlog_file

                if error == '':
               
                    # first step create user if not exist

                    # Hash the password using Django's default algorithm (PBKDF2)
                    password = '1234'
                    password_hash = make_password(password)
                    today = datetime.datetime.now()
                    group = Group.objects.get(name='frontline')

                    logger.info("MigrateDBThread: run()")
                    logger.info('Start migrating staff data...' + staff_file)

                    with open(staff_file, 'r') as file:
                        reader = csv.reader(file)

                        # Iterate over each row in the CSV file and insert into the PostgreSQL table
                        for row in reader:
                            staffno, name, password, ttype, winuser, adminright, blank = row

                            # check if user exist
                            user = None
                            try:
                                user = User.objects.get(username=staffno)
                            except User.DoesNotExist:
                                user = None
                            if user == None:
                                # create user
                                user = User.objects.create(username=staffno, password=password_hash, first_name=name, last_name=branch.bcode, email='', is_staff=False, is_active=False, is_superuser=False, last_login=today, date_joined=today)
                                user.groups.add(group)

                                # add userprofile
                                userprofile = UserProfile.objects.create(user=user)
                                userprofile.branchs.add(branch)
                            # break  # for test
                    logger.info('Completed migrating staff data...' + staff_file)
                    # close file
                    file.close()

                
                    
                    ########################################
                    # second step migrate UserLog data
                    logger.info('Start migrating UserLog data...' + userlog_file)
                    with open(userlog_file, 'r') as file:
                        reader = csv.reader(file)
                        # print total rows
                        totalrow = len(list(reader))
                        logger.info('Total records:' + str(totalrow))
                        # Iterate over each row in the CSV file and insert into the PostgreSQL table
                    file.close()

                    # reader go first row
                    with open(userlog_file, 'r') as file:
                        reader = csv.reader(file)
                        # logger.info('Line number:' +  str(reader.line_num))
                        i = 0
                        per = 0
                        for row in reader:
                            i = i + 1
                            if per < int(i / totalrow * 100) :
                                per = int(i / totalrow * 100)
                                logger.info('UserLog ('  + branch.bcode + ') Progress:' + str(per) + '%')

                            error = ''
                            # Cols : UserID, Type, STime, ETime, TotalTime
                            staffno, logtype, starttime, endtime, totaltime, blank = row

                            # check if user exist
                            user = None
                            slogtype = ''
                            try:
                                user = User.objects.get(username=staffno)
                            except:
                                error = 'User not found'
                            if error == '':
                                ilogtype = int(logtype)
                                if ilogtype < 7 and ilogtype >=0 :
                                    if ilogtype == 0 :
                                        slogtype = 'login'
                                    elif ilogtype == 1 :    
                                        slogtype = 'ready'
                                    elif ilogtype == 2 :
                                        slogtype = 'waiting'
                                    elif ilogtype == 3 :
                                        slogtype = 'walking'
                                    elif ilogtype == 4 :
                                        slogtype = 'processing'
                                    elif ilogtype == 5 :
                                        slogtype = 'ACW'
                                    elif ilogtype == 6 :
                                        slogtype = 'AUX'
                                if slogtype == '' :
                                    error = 'Log type not found'
                            if error == '':
                                # convert starttime and endtime to datetime and UTC
                                try:
                                    dstarttime = datetime.datetime.strptime(starttime, '%Y-%m-%d %H:%M:%S')
                                    dendtime = datetime.datetime.strptime(endtime, '%Y-%m-%d %H:%M:%S')
                                    utcstarttime = pytz.timezone(branch.timezone).localize(dstarttime)
                                    utcendtime = pytz.timezone(branch.timezone).localize(dendtime)
                                    # utcstarttime2 = funLocaltoUTC(dstarttime, branch.timezone)
            
                                except:
                                    error = 'Start or End time format error'
                            if error == '':
                                # migrate data to UserStatusLog
                                try:
                                    userstatuslog = UserStatusLog.objects.create(user=user, status=slogtype, starttime=utcstarttime, endtime=utcendtime )
                                except:
                                    error = 'Create UserStatusLog error'
                                pass
                            if error != '':
                                logger.error(error)
                            # break  # for test
                    logger.info('Completed migrating Userlog data...' + userlog_file)
                    # close file
                    file.close()            
                    
            
                    ########################################
                    # second step migrate main data
                    logger.info('Start migrating Ticket data...' + maindb_file)
                    with open(maindb_file, 'r') as file:
                        reader = csv.reader(file)
                        # print total rows
                        totalrow = len(list(reader))
                        logger.info('Total records:' + str(totalrow))
                        # Iterate over each row in the CSV file and insert into the PostgreSQL table
                    file.close()

                    # reader go first row
                    with open(maindb_file, 'r') as file:
                        reader = csv.reader(file)
                        error = ''
                        # logger.info('Line number:' +  str(reader.line_num))
                        i = 0
                        per = 0
                        countertype = None
                        try:
                            countertype = CounterType.objects.get(branch=branch, name='c')
                        except:
                            error = 'CounterType not found'
                        step = 1
                        ticketroute = None

                        if error == '':
                            for row in reader:
                                i = i + 1
                                if per < int(i / totalrow * 100) :
                                    per = int(i / totalrow * 100)
                                    logger.info('Main DB ('  + branch.bcode + ') Progress:' + str(per) + '%')

                                error = ''
                            
                                #   - table Main : Type, Number, TicketTime, CallTime, ProcessTime, DoneTime, AddTime1, AddTime2, AddTime3, AddTime4, 
                                #                  WaitPeriod, WalkPeriod, ProcessPeriod, TotalPeriod, AddPeriod1, AddPeriod2, AddPeriod3, AddPeriod4, TicketDate, By,
                                #                  Remark, WinUser
                                ttype, tno, stickettime, scalltime, sprocesstime, sdonetime, saddtime1, saddtime2, saddtime3, saddtime4, swaitperiod, swalkperiod, sprocessperiod, stotalperiod, saddperiod1, saddperiod2, saddperiod3, saddperiod4, sticketdate, username, remark, winuser, blank = row
                                
                                status = 'miss'
                                if ttype == None or ttype == '':
                                    error = 'Type is empty'
                                # Old data may not have some ticket type
                                if error == '':
                                    try:
                                        ticketroute = TicketRoute.objects.get(branch=branch, tickettype=ttype, step=step)
                                    except:
                                        ticketroute = None

                                if error == '':
                                    if tno == None or tno == '':
                                        error = 'Number is empty'
                                if error == '':
                                    if stickettime == None or stickettime == '':
                                        error = 'TicketTime is empty'
                                if error == '':
                                    if sticketdate == None or sticketdate == '':
                                        error = 'TicketDate is empty'
                                if error == '':
                                    if username == None or username == '':
                                        error = 'Username (by) is empty'
                                if error == '':
                                    try:
                                        user = User.objects.get(username=username)
                                    except:
                                        error = 'User not found'
                                utctickettime = None
                                if error == '':
                                    # process data
                                    stemp = sticketdate + ' ' + stickettime
                                    # convert stemp to datetime and UTC
                                    try:
                                        dtickettime = datetime.datetime.strptime(stemp, '%Y-%m-%d %H:%M:%S')
                                        utctickettime = pytz.timezone(branch.timezone).localize(dtickettime)
                                    except:
                                        error = 'TicketTime format error'
                                utccalltime = None
                                if error == '':
                                    stemp = sticketdate + ' ' + scalltime
                                    # convert stemp to datetime and UTC
                                    try:
                                        dcalltime = datetime.datetime.strptime(stemp, '%Y-%m-%d %H:%M:%S')
                                        utccalltime = pytz.timezone(branch.timezone).localize(dcalltime)
                                    except:
                                        pass
                                utcprocesstime = None
                                if error == '':
                                    stemp = sticketdate + ' ' + sprocesstime
                                    # convert stemp to datetime and UTC
                                    try:
                                        dprocesstime = datetime.datetime.strptime(stemp, '%Y-%m-%d %H:%M:%S')
                                        utcprocesstime = pytz.timezone(branch.timezone).localize(dprocesstime)
                                    except:
                                        pass
                                utcdonetime = None
                                if error == '':
                                    stemp = sticketdate + ' ' + sdonetime
                                    # convert stemp to datetime and UTC
                                    try:
                                        ddonetime = datetime.datetime.strptime(stemp, '%Y-%m-%d %H:%M:%S')
                                        utcdonetime = pytz.timezone(branch.timezone).localize(ddonetime)
                                        status = 'done'
                                    except:
                                        pass
                                waitperiod = None
                                if error == '':
                                    try:
                                        waitperiod = int(swaitperiod)
                                    except:
                                        pass
                                walkperiod = None
                                if error == '':
                                    try:
                                        walkperiod = int(swalkperiod)
                                    except:
                                        pass
                                processperiod = None
                                if error == '':
                                    try:
                                        processperiod = int(sprocessperiod)
                                    except:
                                        pass
                                totalperiod = None
                                if error == '':
                                    try:
                                        totalperiod = int(stotalperiod)
                                    except:
                                        pass
                                utcvoidtime = None
                                utcmisstime = None
                                ticket = None
                                if error == '':
                                    try:
                                        ticket = Ticket.objects.create(
                                            tickettype=ttype, 
                                            ticketnumber=tno,
                                            branch=branch,
                                            step=step,
                                            countertype=countertype,
                                            ticketroute=ticketroute,
                                            ticketformat=None,
                                            status=status,
                                            locked=True,
                                            tickettime=utctickettime,
                                            tickettext='',
                                            printernumber='',
                                            printedtimes=1,
                                            user=user,
                                            remark='Old',
                                            createdby=user,
                                            )
                                    except:
                                        error = 'Create Ticket error'
                                if error == '':
                                    try:
                                        ticketdata = TicketData.objects.create(
                                            ticket = ticket,
                                            tickettemp=None,
                                            branch=branch,
                                            countertype=countertype,
                                            step=step,
                                            starttime=utctickettime,
                                            startuser=user,
                                            calltime=utccalltime,
                                            calluser=user,
                                            processtime=utcprocesstime,
                                            processuser=user,
                                            donetime=utcdonetime,
                                            doneuser=user,
                                            misstime=utcmisstime,
                                            missuser=None,
                                            voidtime=utcvoidtime,
                                            voiduser=None,
                                            waitingperiod=waitperiod,
                                            walkingperiod=walkperiod,
                                            processingperiod=processperiod,
                                            totalperiod=totalperiod,
                                        )
                                    except Exception as e:
                                        error = 'Create TicketData error' + str(e)
                                        # remove ticket from Ticket
                                        ticket.delete()



                                if error != '':
                                    logger.error(error)
                        if error != '':
                                    logger.error(error)    
                    
                    logger.info('Completed migrating main ticket data...' + maindb_file)
                    # close file
                    file.close()           






        except Exception as e:
            logger.error("MigrateDBThread: run() Exception: ", e)

class MigrateDBThread(threading.Thread):

    def __init__(self, branch, staff_file, maindb_file, userlog_file):
        self.branch = branch
        self.staff_file = staff_file
        self.maindb_file = maindb_file
        self.userlog_file = userlog_file
        threading.Thread.__init__(self)
    
    def run(self):        
        try:
            for index in range(1, 3):
                error = ''
                bcode = ''
                staff_file = ''
                maindb_file = ''
                userlog_file = ''
                if index == 2:
                    bcode = 'SCP'

                    staff_file = './base/api/shatin/staff.csv'
                    maindb_file = './base/api/shatin/main.csv'
                    userlog_file = './base/api/shatin/userlog.csv'
                elif index == 1:
                    bcode = 'WTT'

                    staff_file = './base/api/sheungwan/staff.csv'
                    maindb_file = './base/api/sheungwan/main.csv'
                    userlog_file = './base/api/sheungwan/userlog.csv'

                if error == '':
                    try:
                        branch = Branch.objects.get(bcode=bcode)
                    except:
                        error = 'Branch not found' + bcode
                if error == '':
                    try:
                        f = open(staff_file)
                    except:
                        error = 'File not found:' + staff_file
                if error == '':
                    try:
                        f = open(maindb_file)
                    except:
                        error = 'File not found:' + maindb_file
                if error == '':
                    try:
                        f = open(userlog_file)
                    except:
                        error = 'File not found:' + userlog_file

                if error == '':
               
                    # first step create user if not exist

                    # Hash the password using Django's default algorithm (PBKDF2)
                    password = '1234'
                    password_hash = make_password(password)
                    today = datetime.datetime.now()
                    group = Group.objects.get(name='frontline')

                    logger.info("MigrateDBThread: run()")
                    logger.info('Start migrating staff data...' + staff_file)

                    with open(staff_file, 'r') as file:
                        reader = csv.reader(file)

                        # Iterate over each row in the CSV file and insert into the PostgreSQL table
                        for row in reader:
                            staffno, name, password, ttype, winuser, adminright, blank = row

                            # check if user exist
                            user = None
                            try:
                                user = User.objects.get(username=staffno)
                            except User.DoesNotExist:
                                user = None
                            if user == None:
                                # create user
                                user = User.objects.create(username=staffno, password=password_hash, first_name=name, last_name=branch.bcode, email='', is_staff=False, is_active=False, is_superuser=False, last_login=today, date_joined=today)
                                user.groups.add(group)

                                # add userprofile
                                userprofile = UserProfile.objects.create(user=user)
                                userprofile.branchs.add(branch)
                            # break  # for test
                    logger.info('Completed migrating staff data...' + staff_file)
                    # close file
                    file.close()

                
                    
                    ########################################
                    # second step migrate UserLog data
                    logger.info('Start migrating UserLog data...' + userlog_file)
                    with open(userlog_file, 'r') as file:
                        reader = csv.reader(file)
                        # print total rows
                        totalrow = len(list(reader))
                        logger.info('Total records:' + str(totalrow))
                        # Iterate over each row in the CSV file and insert into the PostgreSQL table
                    file.close()

                    # reader go first row
                    with open(userlog_file, 'r') as file:
                        reader = csv.reader(file)
                        # logger.info('Line number:' +  str(reader.line_num))
                        i = 0
                        per = 0
                        for row in reader:
                            i = i + 1
                            if per < int(i / totalrow * 100) :
                                per = int(i / totalrow * 100)
                                logger.info('UserLog ('  + branch.bcode + ') Progress:' + str(per) + '%')

                            error = ''
                            # Cols : UserID, Type, STime, ETime, TotalTime
                            staffno, logtype, starttime, endtime, totaltime, blank = row

                            # check if user exist
                            user = None
                            slogtype = ''
                            try:
                                user = User.objects.get(username=staffno)
                            except:
                                error = 'User not found'
                            if error == '':
                                ilogtype = int(logtype)
                                if ilogtype < 7 and ilogtype >=0 :
                                    if ilogtype == 0 :
                                        slogtype = 'login'
                                    elif ilogtype == 1 :    
                                        slogtype = 'ready'
                                    elif ilogtype == 2 :
                                        slogtype = 'waiting'
                                    elif ilogtype == 3 :
                                        slogtype = 'walking'
                                    elif ilogtype == 4 :
                                        slogtype = 'processing'
                                    elif ilogtype == 5 :
                                        slogtype = 'ACW'
                                    elif ilogtype == 6 :
                                        slogtype = 'AUX'
                                if slogtype == '' :
                                    error = 'Log type not found'
                            if error == '':
                                # convert starttime and endtime to datetime and UTC
                                try:
                                    dstarttime = datetime.datetime.strptime(starttime, '%Y-%m-%d %H:%M:%S')
                                    dendtime = datetime.datetime.strptime(endtime, '%Y-%m-%d %H:%M:%S')
                                    utcstarttime = pytz.timezone(branch.timezone).localize(dstarttime)
                                    utcendtime = pytz.timezone(branch.timezone).localize(dendtime)
                                    # utcstarttime2 = funLocaltoUTC(dstarttime, branch.timezone)
            
                                except:
                                    error = 'Start or End time format error'
                            if error == '':
                                # migrate data to UserStatusLog
                                try:
                                    userstatuslog = UserStatusLog.objects.create(user=user, status=slogtype, starttime=utcstarttime, endtime=utcendtime )
                                except:
                                    error = 'Create UserStatusLog error'
                                pass
                            if error != '':
                                logger.error(error)
                            # break  # for test
                    logger.info('Completed migrating Userlog data...' + userlog_file)
                    # close file
                    file.close()            
                    
            
                    ########################################
                    # second step migrate main data
                    logger.info('Start migrating Ticket data...' + maindb_file)
                    with open(maindb_file, 'r') as file:
                        reader = csv.reader(file)
                        # print total rows
                        totalrow = len(list(reader))
                        logger.info('Total records:' + str(totalrow))
                        # Iterate over each row in the CSV file and insert into the PostgreSQL table
                    file.close()

                    # reader go first row
                    with open(maindb_file, 'r') as file:
                        reader = csv.reader(file)
                        error = ''
                        # logger.info('Line number:' +  str(reader.line_num))
                        i = 0
                        per = 0
                        countertype = None
                        try:
                            countertype = CounterType.objects.get(branch=branch, name='c')
                        except:
                            error = 'CounterType not found'
                        step = 1
                        ticketroute = None

                        if error == '':
                            for row in reader:
                                i = i + 1
                                if per < int(i / totalrow * 100) :
                                    per = int(i / totalrow * 100)
                                    logger.info('Main DB ('  + branch.bcode + ') Progress:' + str(per) + '%')

                                error = ''
                            
                                #   - table Main : Type, Number, TicketTime, CallTime, ProcessTime, DoneTime, AddTime1, AddTime2, AddTime3, AddTime4, 
                                #                  WaitPeriod, WalkPeriod, ProcessPeriod, TotalPeriod, AddPeriod1, AddPeriod2, AddPeriod3, AddPeriod4, TicketDate, By,
                                #                  Remark, WinUser
                                ttype, tno, stickettime, scalltime, sprocesstime, sdonetime, saddtime1, saddtime2, saddtime3, saddtime4, swaitperiod, swalkperiod, sprocessperiod, stotalperiod, saddperiod1, saddperiod2, saddperiod3, saddperiod4, sticketdate, username, remark, winuser, blank = row
                                
                                status = 'miss'
                                if ttype == None or ttype == '':
                                    error = 'Type is empty'
                                # Old data may not have some ticket type
                                if error == '':
                                    try:
                                        ticketroute = TicketRoute.objects.get(branch=branch, tickettype=ttype, step=step)
                                    except:
                                        ticketroute = None

                                if error == '':
                                    if tno == None or tno == '':
                                        error = 'Number is empty'
                                if error == '':
                                    if stickettime == None or stickettime == '':
                                        error = 'TicketTime is empty'
                                if error == '':
                                    if sticketdate == None or sticketdate == '':
                                        error = 'TicketDate is empty'
                                if error == '':
                                    if username == None or username == '':
                                        error = 'Username (by) is empty'
                                if error == '':
                                    try:
                                        user = User.objects.get(username=username)
                                    except:
                                        error = 'User not found'
                                utctickettime = None
                                if error == '':
                                    # process data
                                    stemp = sticketdate + ' ' + stickettime
                                    # convert stemp to datetime and UTC
                                    try:
                                        dtickettime = datetime.datetime.strptime(stemp, '%Y-%m-%d %H:%M:%S')
                                        utctickettime = pytz.timezone(branch.timezone).localize(dtickettime)
                                    except:
                                        error = 'TicketTime format error'
                                utccalltime = None
                                if error == '':
                                    stemp = sticketdate + ' ' + scalltime
                                    # convert stemp to datetime and UTC
                                    try:
                                        dcalltime = datetime.datetime.strptime(stemp, '%Y-%m-%d %H:%M:%S')
                                        utccalltime = pytz.timezone(branch.timezone).localize(dcalltime)
                                    except:
                                        pass
                                utcprocesstime = None
                                if error == '':
                                    stemp = sticketdate + ' ' + sprocesstime
                                    # convert stemp to datetime and UTC
                                    try:
                                        dprocesstime = datetime.datetime.strptime(stemp, '%Y-%m-%d %H:%M:%S')
                                        utcprocesstime = pytz.timezone(branch.timezone).localize(dprocesstime)
                                    except:
                                        pass
                                utcdonetime = None
                                if error == '':
                                    stemp = sticketdate + ' ' + sdonetime
                                    # convert stemp to datetime and UTC
                                    try:
                                        ddonetime = datetime.datetime.strptime(stemp, '%Y-%m-%d %H:%M:%S')
                                        utcdonetime = pytz.timezone(branch.timezone).localize(ddonetime)
                                        status = 'done'
                                    except:
                                        pass
                                waitperiod = None
                                if error == '':
                                    try:
                                        waitperiod = int(swaitperiod)
                                    except:
                                        pass
                                walkperiod = None
                                if error == '':
                                    try:
                                        walkperiod = int(swalkperiod)
                                    except:
                                        pass
                                processperiod = None
                                if error == '':
                                    try:
                                        processperiod = int(sprocessperiod)
                                    except:
                                        pass
                                totalperiod = None
                                if error == '':
                                    try:
                                        totalperiod = int(stotalperiod)
                                    except:
                                        pass
                                utcvoidtime = None
                                utcmisstime = None
                                ticket = None
                                if error == '':
                                    try:
                                        ticket = Ticket.objects.create(
                                            tickettype=ttype, 
                                            ticketnumber=tno,
                                            branch=branch,
                                            step=step,
                                            countertype=countertype,
                                            ticketroute=ticketroute,
                                            ticketformat=None,
                                            status=status,
                                            locked=True,
                                            tickettime=utctickettime,
                                            tickettext='',
                                            printernumber='',
                                            printedtimes=1,
                                            user=user,
                                            remark='Old',
                                            createdby=user,
                                            )
                                    except:
                                        error = 'Create Ticket error'
                                if error == '':
                                    try:
                                        ticketdata = TicketData.objects.create(
                                            ticket = ticket,
                                            tickettemp=None,
                                            branch=branch,
                                            countertype=countertype,
                                            step=step,
                                            starttime=utctickettime,
                                            startuser=user,
                                            calltime=utccalltime,
                                            calluser=user,
                                            processtime=utcprocesstime,
                                            processuser=user,
                                            donetime=utcdonetime,
                                            doneuser=user,
                                            misstime=utcmisstime,
                                            missuser=None,
                                            voidtime=utcvoidtime,
                                            voiduser=None,
                                            waitingperiod=waitperiod,
                                            walkingperiod=walkperiod,
                                            processingperiod=processperiod,
                                            totalperiod=totalperiod,
                                        )
                                    except Exception as e:
                                        error = 'Create TicketData error' + str(e)
                                        # remove ticket from Ticket
                                        ticket.delete()



                                if error != '':
                                    logger.error(error)
                        if error != '':
                                    logger.error(error)    
                    
                    logger.info('Completed migrating main ticket data...' + maindb_file)
                    # close file
                    file.close()           






        except Exception as e:
            logger.error("MigrateDBThread: run() Exception: ", e)

