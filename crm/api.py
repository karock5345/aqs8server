from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from crm.models import Member, Company
from base.models import Branch, APILog
import random
import string
from datetime import datetime, timezone, timedelta
from base.api.views import setting_APIlogEnabled, visitor_ip_address, loginapi_notoken, funUTCtoLocal, counteractive, checkuser

# Member token expire hours
tokenexpire_hours = 24

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def crmMemberInfoView(request):
    datetime_now_utc = datetime.now(timezone.utc)
    status = {}
    data = {}
    rx_member_no = ''
    rx_member_token = ''
    error = ''
    branch = None
    member = None

    rx_app = request.GET.get('app') if request.GET.get('app') != None else ''
    rx_version = request.GET.get('version') if request.GET.get('version') != None else ''
    rx_member_no = request.GET.get('member_no') if request.GET.get('member_no') != None else ''
    rx_member_token = request.GET.get('member_token') if request.GET.get('member_token') != None else ''
    rx_bcode = request.GET.get('bcode') if request.GET.get('bcode') != None else ''

    if rx_member_no == '' or rx_member_token == '' or rx_bcode == '':
        error = 'Missing parameters'
    
    # check bcode
    if error == '':
        try:
            branch = Branch.objects.get(bcode=rx_bcode)
        except :
            error = 'branch not found failed'
    
    # check member token
    if error == '':
        try:
            member = Member.objects.get(number=rx_member_no, token=rx_member_token, branch=branch)
        except:
            error = 'Unauthorized'

    # check member is active?
    if error == '':
        if member.enabled == False:
            error = 'Member is deactivated'
    
    # check member token expired?
    if error == '':
        if member.tokendate == None:
            error = 'Unauthorized'
        else:
            temp = member.tokendate + timedelta(hours=tokenexpire_hours)
            if temp < datetime_now_utc:
                error = 'Token expired'



    # Save Api Log
    if branch != None:
        if setting_APIlogEnabled(branch) == True :
            APILog.objects.create(
                logtime=datetime_now_utc,
                requeststr = request.build_absolute_uri() ,
                ip = visitor_ip_address(request),
                app = rx_app,
                version = rx_version,
                logtext = 'API call : CRM User Login',
            )

    if error == '' :        
        # member info:
        status = {'status':'success', 'msg':'Login success', }
        data = {
                'nickname':member.nickname, 
                'member_level':member.memberlevel ,
                'member_points':member.memberpoints,
                }
    else:
        status = {'status':'failed', 'msg':error}
        data = {}
    return Response(status | data )

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def crmUserLoginView(request):
    datetime_now_utc = datetime.now(timezone.utc)
    status = {}
    data = {}
    member_no = ''
    member_token = ''
    error = ''
    company = None

    rx_app = request.GET.get('app') if request.GET.get('app') != None else ''
    rx_version = request.GET.get('version') if request.GET.get('version') != None else ''
    rx_username = request.GET.get('username') if request.GET.get('username') != None else ''
    rx_password = request.GET.get('password') if request.GET.get('password') != None else ''
    rx_ccode = request.GET.get('ccode') if request.GET.get('ccode') != None else ''

    if rx_username == '' or rx_password == '' or rx_ccode == '':
        error = 'Missing parameters'
        
    if error == '' :        
        error, member_no, member_token, company = crmUserLogin(rx_username, rx_password, rx_ccode, datetime_now_utc)
        
    # Save Api Log
    if company != None:
        if setting_APIlogEnabled(None, company) == True :
            APILog.objects.create(
                logtime=datetime_now_utc,
                requeststr = request.build_absolute_uri() ,
                ip = visitor_ip_address(request),
                app = rx_app,
                version = rx_version,
                logtext = 'API call : CRM User Login',
            )

            # # remove all data from APILog
            # APILog.objects.all().delete()

    if error == '':
        status = {'status':'success', 'msg':'Login success', }
        data = {'member_no':member_no, 'member_token':member_token, }
    else:
        status = {'status':'failed', 'msg':error}
        data = {}
    return Response(status | data )

def crmUserLogin(username, password, ccode, datetime_now_utc):
    error = ''
    member_no = ''
    member_token = ''

    # branch = None
    company = None
    if error == '' :
        try:
            company = Company.objects.get(ccode=ccode)
        except :
            error = 'Login failed'
    if error == '' :
        try:
            member = Member.objects.get(username=username, company=company, password=password)
        except :
            error = 'Login failed'
    if error == '' :
        if member.enabled == True :
            member_no = member.number
            # generate token ramdom 114 chars
            member_token = random.choices(string.ascii_uppercase + string.ascii_lowercase + string.digits, k=114)
            member_token = ''.join(member_token)
            member.token = member_token
            member.tokendate = datetime_now_utc
            member.save()
        else:
            error = 'Member is deactivated'

    return error, member_no, member_token, company