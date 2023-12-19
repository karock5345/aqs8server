from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from crm.models import Member, Company, MemberItem
from base.models import Branch, APILog
import random
import string
from datetime import datetime, timezone, timedelta
from base.api.views import setting_APIlogEnabled, visitor_ip_address, loginapi_notoken, funUTCtoLocal, counteractive, checkuser
from crm.serializers import MemberItemListSerivalizer
import re
import phonenumbers
import phonenumbers.timezone
# from phonenumbers import timezone

# Member token expire hours
tokenexpire_hours = 24

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def crmMemberRegistrationView(request):
    datetime_now_utc = datetime.now(timezone.utc)
    status = {}
    data = {}
    rx_ccode = ''
    rx_member_username = ''
    rx_member_password = ''
    rx_email = ''
    rx_mobile = ''
    rx_nickname = ''
    rx_gender = ''
    rx_dob = ''
    error = ''
    company = None
    member = None

    rx_app = request.GET.get('app') if request.GET.get('app') != None else ''
    rx_version = request.GET.get('version') if request.GET.get('version') != None else ''
    rx_ccode = request.GET.get('ccode') if request.GET.get('ccode') != None else ''
    rx_member_username = request.GET.get('username') if request.GET.get('username') != None else ''
    rx_member_password = request.GET.get('password') if request.GET.get('password') != None else ''
    rx_email = request.GET.get('email') if request.GET.get('email') != None else ''
    rx_mobile = request.GET.get('mobile') if request.GET.get('mobile') != None else ''
    rx_nickname = request.GET.get('nickname') if request.GET.get('nickname') != None else ''
    rx_gender = request.GET.get('gender') if request.GET.get('gender') != None else ''
    rx_dob = request.GET.get('dob') if request.GET.get('dob') != None else ''

    # check miss parameters
    if error == '':
        if rx_ccode == '' or rx_member_username == '' or rx_member_password == '' or rx_email == '' or rx_mobile == '' or rx_nickname == '' or rx_gender == '' or rx_dob == '' :
            error = 'Missing parameters'
    # check ccode
    if error == '':
        try:
            company = Company.objects.get(ccode=rx_ccode)
        except :
            error = 'company not found failed'
    # check username
    # username is lowercase, auto convert to lowercase
    rx_member_username = rx_member_username.lower()
    if error == '':
        try:
            member = Member.objects.get(username=rx_member_username, company=company)
            error = 'Username already exists'
        except :
            pass
    # check rx_member_username should be 4-20 chars
    if error == '':
        if len(rx_member_username) < 4 or len(rx_member_username) > 20 :
            error = 'Username should be 4-20 chars'
    # check password should be 8-20 chars
    if error == '':
        if len(rx_member_password) < 8 or len(rx_member_password) > 20 :
            error = 'Password should be 8-20 chars'
    # check email
    if error == '':
        try:
            member = Member.objects.get(email=rx_email, company=company)
            error = 'Email already exists'
        except :
            pass
    # check email format
    if error == '':
        regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b'
        if(re.fullmatch(regex, rx_email)):
            pass       
        else:
            error = 'Email format is incorrect'

    # check mobile
    if error == '':
        try:
            member = Member.objects.get(mobile=rx_mobile, company=company)
            error = 'Mobile already exists'
        except :
            pass
    # check mobile format

    if error == '':
        if len(rx_mobile) == 8 and rx_mobile.isdigit() == True:
            rx_mobile = '852' + rx_mobile
            pass
    if error == '':
        # check mobile first 4 digits is '+852'
        if rx_mobile[0:4] == '+852':
            # remove '+' from mobile
            rx_mobile = rx_mobile[1:]
    if error == '':
        print(rx_mobile)
        phone_number = phonenumbers.parse('+' + rx_mobile)
        print(phone_number)
        print(phonenumbers.is_valid_number(phone_number))
        print(phonenumbers.timezone.time_zones_for_number(phone_number))
        print('Country code:' + str(phone_number.country_code))
        print('National number:' + str(phone_number.national_number))

    # check nickname
    if error == '':
        if len(rx_nickname) < 4 :
            error = 'Nickname min. 4 chars'
    # check gender
    if error == '':
        if rx_gender == 'M' or rx_gender == 'F':
            pass
        else:
            error = 'Gender must be M or F'
    # check dob
    if error == '':
        try:
            rx_dob = datetime.strptime(rx_dob, '%Y_%m_%d')
        except:
            error = 'DOB format must be YYYY_MM_DD'
    
    
    # Save Api Log
    if company != None:
        if setting_APIlogEnabled(None, company) == True :
            APILog.objects.create(
                logtime=datetime_now_utc,
                requeststr = request.build_absolute_uri() ,
                ip = visitor_ip_address(request),
                app = rx_app,
                version = rx_version,
                logtext = 'API call : CRM Member registration',
            )
    
    if error == '' :
        # new member
        # verifycode = random.choices(string.ascii_uppercase + string.ascii_lowercase + string.digits, k=6)
        # verifycode = ''.join(verifycode)
        verifycode = '1234'
        # username is lowercase, auto convert to lowercase
        rx_member_username = rx_member_username.lower()

        

        status = {'status':'success', 'msg':'Successfully! Please check your email to activate your account.', }
    else:
        status = {'status':'failed', 'msg':error}
    return Response(status | data )

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def crmMemberItemListView(request):
    datetime_now_utc = datetime.now(timezone.utc)
    status = {}
    data = {}
    rx_member_no = ''
    rx_member_token = ''
    error = ''
    company = None
    member = None

    rx_app = request.GET.get('app') if request.GET.get('app') != None else ''
    rx_version = request.GET.get('version') if request.GET.get('version') != None else ''
    rx_member_no = request.GET.get('member_no') if request.GET.get('member_no') != None else ''
    rx_member_token = request.GET.get('member_token') if request.GET.get('member_token') != None else ''
    rx_ccode = request.GET.get('ccode') if request.GET.get('ccode') != None else ''

    if rx_member_no == '' or rx_member_token == '' or rx_ccode == '':
        error = 'Missing parameters'
    
    # check bcode
    if error == '':
        try:
            company = Company.objects.get(ccode=rx_ccode)
        except :
            error = 'company not found failed'
    
    if error == '':
        check, error, member = checkmember(rx_member_no, rx_member_token, company, datetime_now_utc)


    # Save Api Log
    if company != None:
        if setting_APIlogEnabled(None, company) == True :
            APILog.objects.create(
                logtime=datetime_now_utc,
                requeststr = request.build_absolute_uri() ,
                ip = visitor_ip_address(request),
                app = rx_app,
                version = rx_version,
                logtext = 'API call : CRM Member items list',
            )
    if error == '' :
        # Get member items
        memberitems = MemberItem.objects.filter(company=company)
        serializers  = MemberItemListSerivalizer(memberitems, many=True)
        context_list = serializers.data

        status = {'status':'success', 'msg':'Successfully!', }
        data = {'items' : context_list}
    else:
        status = {'status':'failed', 'msg':error}
        data = {}
    return Response(status | data )



@api_view(['GET'])
@permission_classes([IsAuthenticated])
def crmMemberInfoView(request):
    datetime_now_utc = datetime.now(timezone.utc)
    status = {}
    data = {}
    rx_member_no = ''
    rx_member_token = ''
    error = ''
    company = None
    member = None

    rx_app = request.GET.get('app') if request.GET.get('app') != None else ''
    rx_version = request.GET.get('version') if request.GET.get('version') != None else ''
    rx_member_no = request.GET.get('member_no') if request.GET.get('member_no') != None else ''
    rx_member_token = request.GET.get('member_token') if request.GET.get('member_token') != None else ''
    rx_ccode = request.GET.get('ccode') if request.GET.get('ccode') != None else ''

    if rx_member_no == '' or rx_member_token == '' or rx_ccode == '':
        error = 'Missing parameters'
    
    # check bcode
    if error == '':
        try:
            company = Company.objects.get(ccode=rx_ccode)
        except :
            error = 'company not found failed'
        
    if error == '':
        check, error, member = checkmember(rx_member_no, rx_member_token, company, datetime_now_utc)

    # Save Api Log
    if company != None:
        if setting_APIlogEnabled(None, company) == True :
            APILog.objects.create(
                logtime=datetime_now_utc,
                requeststr = request.build_absolute_uri() ,
                ip = visitor_ip_address(request),
                app = rx_app,
                version = rx_version,
                logtext = 'API call : CRM Member Info',
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


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def crmMemberLogoutView(request):
    datetime_now_utc = datetime.now(timezone.utc)
    status = {}
    data = {}
    rx_member_no = ''
    rx_member_token = ''
    error = ''
    member = None
    company = None

    rx_app = request.GET.get('app') if request.GET.get('app') != None else ''
    rx_version = request.GET.get('version') if request.GET.get('version') != None else ''
    rx_member_no = request.GET.get('member_no') if request.GET.get('member_no') != None else ''
    rx_member_token = request.GET.get('member_token') if request.GET.get('member_token') != None else ''
    rx_ccode = request.GET.get('ccode') if request.GET.get('ccode') != None else ''

    if rx_member_no == '' or rx_member_token == '' or rx_ccode == '':
        error = 'Missing parameters'

    # check ccode
    if error == '':
        try:
            company = Company.objects.get(ccode=rx_ccode)
        except :
            error = 'company not found failed'    

    if error == '':
        check, error, member = checkmember(rx_member_no, rx_member_token, company, datetime_now_utc)



    # Save Api Log
    if company != None:
        if setting_APIlogEnabled(None, company) == True :
            APILog.objects.create(
                logtime=datetime_now_utc,
                requeststr = request.build_absolute_uri() ,
                ip = visitor_ip_address(request),
                app = rx_app,
                version = rx_version,
                logtext = 'API call : CRM Member Logout',
            )

    if error == '' :
        # Member logout
        member.token = ''
        member.tokendate = None
        member.login = False
        member.save()

        status = {'status':'success', 'msg':'Logout successfully!', }
    else:
        status = {'status':'failed', 'msg':error}
        data = {}
    return Response(status | data )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def crmMemberLoginView(request):
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
        error, member_no, member_token, company = MemberLogin(rx_username, rx_password, rx_ccode, datetime_now_utc)
        
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

def MemberLogin(username, password, ccode, datetime_now_utc):
    error = ''
    member_no = ''
    member_token = ''
    # username is lowercase, auto convert to lowercase
    username = username.lower()

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
            member_token = random.choices(string.ascii_uppercase + string.ascii_lowercase + string.digits, k=4) #k=114)
            member_token = ''.join(member_token)
            member.token = member_token
            member.tokendate = datetime_now_utc
            member.login = True
            member.save()
        else:
            error = 'Member is deactivated'

    return error, member_no, member_token, company

def checkmember(rx_member_no, rx_member_token, company, datetime_now_utc):
    check = False
    error = ''
    member = None

    if error == '':
        if rx_member_token == '' or rx_member_token == None:
            error = 'Unauthorized'

    # check member token
    if error == '':
        try:
            member = Member.objects.get(number=rx_member_no, token=rx_member_token, company=company)
        except:
            error = 'Unauthorized'
    
    # check member is verified?
    if error == '':
        if member.verified == False:
            error = 'Member is not verified'

    # check member is active?
    if error == '':
        if member.enabled == False:
            error = 'Member is deactivated'

    # check member is login?
    if error == '':
        if member.login == False:
            error = 'Member do not login'

    # check member token expired?
    if error == '':
        if member.tokendate == None:
            error = 'Unauthorized'
        else:
            temp = member.tokendate + timedelta(hours=tokenexpire_hours)
            if temp < datetime_now_utc:
                error = 'Token expired'

    check = False
    if error == '':
        check = True

    return check, error, member