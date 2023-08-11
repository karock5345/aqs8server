from aqs.settings import aqs_version
from datetime import datetime, timedelta, date
import time
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User, Group
from django.db.models import Q
import pytz
from dateutil import tz
from base.models import APILog, Branch, Setting, TicketFormat, Ticket, TicketRoute, TicketData, TicketLog, UserProfile, lcounterstatus
from .serializers import branchSerivalizer, ticketlistSerivalizer
from .thread import MigrateDBThread, MigrateDBThreadtst

token_api = 'WrE-1t7IdrU2iB3a0e'
# if the counter keep active > 6 minutes then auto logout and the counter replace the new user
counteractive = 1

@api_view(['GET'])
def getDBtst(request):
    # for PCCW migration old data to new system
    app = request.GET.get('app') if request.GET.get('app') != None else ''
    version = request.GET.get('version') if request.GET.get('version') != None else ''

    error = ''
    branch = None
    staff_file = ''
    maindb_file = ''
    userlog_file = ''


    if error == '' :
        staff_file = ''
        maindb_file = ''
        userlog_file = ''


    if setting_APIlogEnabled(None) == True :
        #datetime_now = datetime.utcnow()
        datetime_now =timezone.now()    
        APILog.objects.create(
            logtime=datetime_now,
            requeststr = request.build_absolute_uri() ,
            ip = visitor_ip_address(request),
            app = app,
            version = version,
            logtext = 'API call : Migration TST branch old database to new system (branch:(HHT))',
        )

    if error == '':

        MigrateDBThreadtst(branch, staff_file, maindb_file, userlog_file).start()
        routes = [
            'Migration TST branch old database (HHT) processing....',
            'Version : ' + aqs_version,
                    ]
    else:
        routes = [
            'Migration error : ' + error,
            'Version : ' + aqs_version,
                    ]
    return Response(routes)

@api_view(['GET'])
def getDB2(request):
    # for PCCW migration old data to new system
    app = request.GET.get('app') if request.GET.get('app') != None else ''
    version = request.GET.get('version') if request.GET.get('version') != None else ''

    error = ''
    branch = None
    staff_file = ''
    maindb_file = ''
    userlog_file = ''


    if error == '' :
        staff_file = ''
        maindb_file = ''
        userlog_file = ''


    if setting_APIlogEnabled(None) == True :
        #datetime_now = datetime.utcnow()
        datetime_now =timezone.now()    
        APILog.objects.create(
            logtime=datetime_now,
            requeststr = request.build_absolute_uri() ,
            ip = visitor_ip_address(request),
            app = app,
            version = version,
            logtext = 'API call : Migration 2 branchs old database to new system (branch:(SCP, WTT))',
        )

    if error == '':

        MigrateDBThread(branch, staff_file, maindb_file, userlog_file).start()
        routes = [
            'Migration 2 branchs old database (SCP, WTT) processing....',
            'Version : ' + aqs_version,
                    ]
    else:
        routes = [
            'Migration error : ' + error,
            'Version : ' + aqs_version,
                    ]
    return Response(routes)


def checkuser(apiuser, branch, rx_username):
    # check user group is api
    isAPIuser = False
    error = ''
    user_out = None
    userp = None

    if error == '' :
        for group in apiuser.groups.all():
            if group.name == 'api':
                isAPIuser = True
                exit
        if isAPIuser == False:
            error = 'User group is not allow to call API'
    
    # check api user is allow operate this branch
    if error == '' :
        b_found = False
        try :
            userp = UserProfile.objects.get(user=apiuser)
        except :
            error = 'User Profile not found'
        if userp != None :
            for branch in userp.branchs.all():
                if branch == branch :
                    b_found = True
                    exit
            if b_found == False :
                error = 'User not authorized operate this branch'

            
    # check rx_username is allow operate this branch
    if error == '' :
        user_out = apiuser
        if (rx_username == apiuser.username) or (rx_username == '') or (rx_username == None) :
            pass
        else :
            try :
                rx_user = User.objects.get(username=rx_username)
            except :
                error = 'Receiver user not found'
            if error == '' :
                user_out = rx_user
                b_found = False
                try :
                    rx_userp = UserProfile.objects.get(user=rx_user)
                except :
                    error = 'Receiver user Profile not found'
                if error == '' :
                    for branch in rx_userp.branchs.all():
                        if branch == branch :
                            b_found = True
                            exit
                    if b_found == False :
                        error = 'Receiver user not authorized operate this branch'
    
    if error == '' :
        return 'OK', user_out
    else :
        return error, user_out
    

# api response json format :
# {
#    "status":"OK/Error",
#    "msg":"Ticket route not found",
#    "data": [
#             {
#                 "tickettype": "A",
#                 "ticketnumber": "170",
#                 "bcode": "KB",
#                 "tickettime": "2022-05-13T09:19:48.713711Z",
#                 "tickettext": "<CEN><LOGO><TEXT>歡迎光臨，請稍候\r\n<TEXT>Welcome, please wait to be served\r\n<LINE><B_FONT>\r\n<TEXT>票 號<TEXT>Ticket number\r\n<D_FONT>A170\r\n<N_FONT>\r\n<LINE>\r\n17:19:48 13-05-2022\r\n<CUT>",
#                 "printernumber": "<PNO>1</PNO>"
#             }
#         ]
# }

# first api is show all api you can call


@api_view(['GET'])
def getRoutes(request):
    # check request user group is api
    # user = request.user
    # isAPIuser = False
    # for group in user.groups.all():
    #     if group.name == 'api':
    #         isAPIuser = True
    #         exit
    # if isAPIuser == False:
    #     return Response('User group is not allow to call API')
    
    if setting_APIlogEnabled(None) == True :
        app = request.GET.get('app') if request.GET.get('app') != None else ''
        version = request.GET.get('version') if request.GET.get('version') != None else ''
        #datetime_now = datetime.utcnow()
        datetime_now =timezone.now()    
        APILog.objects.create(
            logtime=datetime_now,
            requeststr = request.build_absolute_uri() ,
            ip = visitor_ip_address(request),
            app = app,
            version = version,
            logtext = 'API call : Get routes',
        )

    routes = [
        'API is working.',
        'Version : ' + aqs_version,
                ]
    return Response(routes)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def getBranchs(request):
    if setting_APIlogEnabled(None) == True :
        app = request.GET.get('app') if request.GET.get('app') != None else ''
        version = request.GET.get('version') if request.GET.get('version') != None else ''
        #datetime_now = datetime.utcnow()
        datetime_now =timezone.now()
        APILog.objects.create(
            logtime=datetime_now,
            requeststr = request.build_absolute_uri() ,
            ip = visitor_ip_address(request),
            app = app,
            version = version,
            logtext = 'API call : Get routes',
        )    
    branchs = Branch.objects.all()
    serializers = branchSerivalizer(branchs, many=True)
    return Response(serializers.data)










def loginapi_notoken(request, username, password, in_branch):

    user = None
    # loginresult = '"Error":"Method should be "POST",'
    # if request.method == 'POST':
    username = username.lower()
    password = password
    loginresult = 'OK'
    

    user =  authenticate(request, username=username, password=password)
    if user is not None:
        # check branch code
        userp= UserProfile.objects.get(user=user)
        for branch in userp.branchs.all():
            if branch == in_branch :
                b_found = True
                exit
        if b_found == False :
            loginresult = 'User not authorized operate this branch'
    else:
        loginresult =  'Login error, username or password does not exist'

    return loginresult, user


def loginapi(request, username, password, token, in_branch):

    user = None
    # loginresult = '"Error":"Method should be "POST",'
    # if request.method == 'POST':
    username = username.lower()
    password = password

    try:
        user = User.objects.get(username=username)
    except:
        loginresult =  'Login error, user does not exist'

    user =  authenticate(request, username=username, password=password)
    if user is not None:
        
        #login(request, user)
        isAPIuser = False
        if token_api == token:
            loginresult = 'OK'
        else :
            # check user group
            for group in user.groups.all():
                loginresult = 'Login error, user group [' + user.groups.all()[0].name + '] is not allow'             
                if group.name == 'api':
                    loginresult = 'OK'
                    isAPIuser = True
                    exit 

        if in_branch != None :
            b_found = False
            if isAPIuser == False:
                # check branch code
                userp= UserProfile.objects.get(user=user)
                for branch in userp.branchs.all():
                    if branch == in_branch :
                        b_found = True
                        exit
                if b_found == False :
                    loginresult = 'User not authorized operate this branch'
    else:
        loginresult =  'Login error, username or password does not exist'

    return loginresult, user

# Convert UTC to Locate datetime
def funUTCtoLocal(dInput, zone) -> datetime :
    # localtime = dInput + timedelta(hours=zone)
    UTC_zone = tz.gettz('UTC')
    local_zone = tz.gettz(zone)
    
    utc = dInput.replace(tzinfo=UTC_zone)
    
    localtime = utc.astimezone(local_zone)

    return localtime

def funUTCtoLocaltime(dInput, zone) -> datetime.time :
    # hour = dInput.strftime('%H')
    # ihour = int(hour)
    # ihour = ihour + zone
    # if ihour >= 24  :
    #     ihour = ihour - 24
    # snew = str(ihour) + dInput.strftime(':%M:%S')
    # new = datetime.strptime(snew, '%H:%M:%S')
    UTC_zone = tz.gettz('UTC')
    local_zone = tz.gettz(zone)

    sDateTime = '2020-01-01 ' + dInput.strftime('%H:%M:%S')
    utc = datetime.strptime(sDateTime, '%Y-%m-%d %H:%M:%S')
    utc = utc.replace(tzinfo=UTC_zone)

    newDateTime = utc.astimezone(local_zone)
    localtime = newDateTime.time()
    return localtime


# Convert Locate datetime to UTC
def funLocaltoUTC(dInput, zone) -> datetime :    
    # ts = datetime.mktime(dInput.timetuple())
    # utc = datetime.utcfromtimestamp(ts) 
    UTC_zone = tz.gettz('UTC')
    local_zone = tz.gettz(zone)
    
    localtime = dInput.replace(tzinfo=local_zone)

    utc = localtime.astimezone(UTC_zone)

    return utc
# Convert Locate time to UTC
def funLocaltoUTCtime(dInput, zone) -> datetime.time :   
    # hour = dInput.strftime('%H')
    # ihour = int(hour)
    # ihour = ihour - zone
    # if ihour < 0 :
    #     ihour = ihour + 24
    # snew = str(ihour) + dInput.strftime(':%M:%S')
    # new = datetime.strptime(snew, '%H:%M:%S')
    UTC_zone = tz.gettz('UTC')
    local_zone = tz.gettz(zone)
    
    sDateTime = '2020-01-01 ' + dInput.strftime('%H:%M:%S')
    localtime = datetime.strptime(sDateTime, '%Y-%m-%d %H:%M:%S')
    localtime = localtime.replace(tzinfo=local_zone)

    utcdt = localtime.astimezone(UTC_zone)

    utc = utcdt.time()
        
    return utc

def visitor_ip_address(request):

    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')

    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

# Convert Locate time to UTC
def setting_APIlogEnabled(branch) -> bool :
    
    out = True
    setobj = Setting.objects.filter( Q(branch=branch))
    if setobj.count() > 0 :
        set = setobj[0]
        out = set.API_Log_Enabled
    else:
        setobj = Setting.objects.filter( Q(name='global'))
        if setobj.count() > 0 :
            set = setobj[0]
            out = set.API_Log_Enabled

    return out    