from rest_framework.response import Response
from django.shortcuts import render
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from crm.models import Member, Company, MemberItem, CRMAdmin, PushMessage
from base.models import Branch, APILog
import random
import string
from datetime import datetime, timezone, timedelta
from base.api.views import setting_APIlogEnabled, visitor_ip_address, loginapi_notoken, funUTCtoLocal, funLocaltoUTC, counteractive, checkuser
from crm.serializers import MemberItemListSerivalizer
import re
import phonenumbers
import phonenumbers.timezone
import xml.etree.ElementTree as ET
from django.template.loader import render_to_string
from aqs.tasks import sendemail
# from django.utils.safestring import mark_safe
# from django.utils.html import format_html, escape
import os
import qrcode
from io import BytesIO
from django.core.files import File
from aqs.settings import STATICFILES_DIRS, STATIC_URL
import shutil
import urllib.parse
from django.db import transaction

# Member token expire hours
tokenexpire_hours = 24


def genQRcode(member:Member):

    path = ''
    path = os.path.join(STATICFILES_DIRS[0], 'qr' , member.company.ccode , member.number)

    # print('Folder removed:' + path)
    if os.path.isdir(path):
        # remove folder
        shutil.rmtree(path)
            
    if not os.path.exists(path):
        # create folder
        os.makedirs(path)

    qr_code = member.company.ccode + '_' + member.number + '_' + member.token
    fname = member.company.ccode + '_' + member.number + '_' + member.token + '.png'
    qrurl = urllib.parse.urljoin( member.company.domain , STATIC_URL)
    qrurl = urllib.parse.urljoin( qrurl , 'qr' + '/')
    qrurl = urllib.parse.urljoin( qrurl , member.company.ccode + '/')
    qrurl = urllib.parse.urljoin( qrurl , member.number + '/')
    qrurl = urllib.parse.urljoin( qrurl , fname )
    # , 'qr', member.company.ccode , member.number , fname)
    # canvas = Image.new('RGB', (300, 300), 'white')
    qrcode_image = qrcode.make(qr_code)
    # draw = ImageDraw.Draw(canvas)
    path = os.path.join(path, fname)
    # print('QR code path:' + path)
    buffer = BytesIO()
    # canvas.save(buffer, 'PNG')
    qrcode_image.save(path, File(buffer), save=True)
    # canvas.close()

    # print('qr url:' + qrurl)

    return qrurl



# del member for test
@api_view(['DELETE'])
def crmMemberDelView(request):
    datetime_now_utc = datetime.now(timezone.utc)
    status = {}
    data = {}
    rx_ccode = ''
    rx_member_username = ''
    error = ''
    company = None
    member = None

    rx_ccode = request.GET.get('ccode') if request.GET.get('ccode') != None else ''
    rx_member_username = request.GET.get('username') if request.GET.get('username') != None else ''
    # username is lowercase, auto convert to lowercase
    rx_member_username = rx_member_username.lower()

    # check miss parameters
    if error == '':
        if rx_ccode == '' or rx_member_username == '' :
            error = 'Missing parameters'
    if error == '':
        try:
            company = Company.objects.get(ccode=rx_ccode)
        except :
            error = 'company not found failed'
    if error == '':
        try:
            member = Member.objects.get(username=rx_member_username, company=company)
        except :
            error = 'Member not exists'
    if error == '':
        member.delete()
        status = {'status':'success', 'msg':'Successfully!'}
    else:
        status = {'status':'failed', 'msg':error}
    return Response(status | data )

@api_view(['GET'])
def crmMemberVerificationView(request):
    datetime_now_utc = datetime.now(timezone.utc)
    status = {}
    data = {}
    rx_ccode = ''
    rx_member_username = ''
    rx_verify_code = ''
    error = ''
    company = None
    member = None

    rx_app = request.GET.get('app') if request.GET.get('app') != None else ''
    rx_ccode = request.GET.get('ccode') if request.GET.get('ccode') != None else ''
    rx_member_username = request.GET.get('username') if request.GET.get('username') != None else ''
    # username is lowercase, auto convert to lowercase
    rx_member_username = rx_member_username.lower()
    rx_verify_code = request.GET.get('verifycode') if request.GET.get('verifycode') != None else ''

    # check miss parameters
    if error == '':
        if rx_ccode == '' or rx_member_username == '' or rx_verify_code == '' :
            error = 'Missing parameters'

    # check ccode
    if error == '':
        try:
            company = Company.objects.get(ccode=rx_ccode)
        except :
            error = 'company not found failed'
            
    if error == '':
        try:
            member = Member.objects.get(username=rx_member_username, company=company)            
        except :
            error = 'Member not exists'
    if error == '':
        if member.enabled == False:
            error = 'Member is deactivated'    
    
    if error == '':
        if member.verifycode != rx_verify_code:
            # if verify code is incorrect, member will be deactivated
            error = 'Verify code is incorrect'
            # member.enabled = False
            # member.save()

    if error == '':
        member.verified = True
        member.verifycode_date = datetime_now_utc
        member.save()
        status = {'status':'success', 'msg':'Successfully!'}
        content = {'company':company, 'member':member, }
        return render(request, 'crm/verify_pass.html', content)
    else:
        status = {'status':'failed', 'msg':error}        
        # return Response(status | data )
        return render(request, 'crm/verify_fail.html', status)


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
    # username is lowercase, auto convert to lowercase
    rx_member_username = rx_member_username.lower()

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

    # check dob
    if error == '':
        try:
            rx_dob = datetime.strptime(rx_dob, '%Y_%m_%d')
        except:
            error = 'DOB format must be YYYY_MM_DD'

    if error == '':
        # print(str(rx_dob))
        status, error = new_member(
                                    request, datetime_now_utc, 
                                    company, rx_member_username, rx_member_password, True,
                                    False, datetime_now_utc,
                                    '', '', rx_gender, rx_email, '852', rx_mobile, rx_nickname, rx_dob,
                                    'SILVER', 0, 0,
                                    )

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
        # gen QR code
        qr_url = genQRcode(member)
        # member info:
        status = {'status':'success', 'msg':'Login success', }
        data = {
                'nickname' : member.nickname, 
                'member_level' : member.memberlevel ,
                'member_points' : member.memberpoints,
                'member_qr': qr_url,
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
    rx_username = rx_username.lower()
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
        if member.enabled == False :
            error = 'Member is deactivated'
    if error == '' :
        if member.verified == False :
            error = 'Member is not verified, please check your email'

    if error == '' :
        member_no = member.number
        # generate token ramdom 114 chars
        member_token = random.choices(string.ascii_uppercase + string.ascii_lowercase + string.digits, k=4) #k=114)
        member_token = ''.join(member_token)
        member.token = member_token
        member.tokendate = datetime_now_utc
        member.login = True
        member.save()
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

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def crmPushMessageDataView(request):
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
    rx_pushid = request.GET.get('pushid') if request.GET.get('pushid') != None else ''
    rx_ccode = request.GET.get('ccode') if request.GET.get('ccode') != None else ''
    rx_msgtype = request.GET.get('msgtype') if request.GET.get('msgtype') != None else ''

    if rx_pushid == '' or rx_ccode == '' or rx_msgtype == '' :
        error = 'Missing parameters'
    
    # check bcode
    if error == '':
        try:
            company = Company.objects.get(ccode=rx_ccode)
        except :
            error = 'company not found failed'        

    # Save Api Log
    if company != None:
        if setting_APIlogEnabled(None, company) == True :
            APILog.objects.create(
                logtime=datetime_now_utc,
                requeststr = request.build_absolute_uri() ,
                ip = visitor_ip_address(request),
                app = rx_app,
                version = rx_version,
                logtext = 'API call : CRM Push Message',
            )
    if error == '' :
        # Get the push message data
        pushmsgs = PushMessage.objects.filter(pushid=rx_pushid, company=company, msgtype=rx_msgtype)
        if pushmsgs.count() == 0:
            error = 'No push message found'
        else:
            pushmsg = pushmsgs.first()
            # print(pushmsg.message)

    if error == '' :
        # push message
        updated = pushmsg.updated.strftime('%Y-%m-%d_%H:%M:%S')
        status = {'status':'success', 'msg':'Push message success', }
        data = {'message':pushmsg.message, 'content':pushmsg.content, 'imageurl':pushmsg.imageurl, 'updated':updated, }        
    else:
        status = {'status':'failed', 'msg':error}
        data = {}
    return Response(status | data )

@transaction.atomic
def gen_new_memberno(company:Company, datetime_now_utc:datetime):
    error = ''
    number_str = None

    if error == '':
        # genrate member number
        try:
            crmadmin = CRMAdmin.objects.select_for_update().get(company=company)
        except:
            error = 'CRM Admin not found'   
    
    if error == '' :
        number = crmadmin.membernumber_next
        number_digit = crmadmin.membernumber_digit
        # check number reset
        # membernumber_reset is role for reset member number, e.g. role:<Y>2024</Y> now is 2023-12-31, when now is 2024-01-01, reset member number to 1 
        reset ='<DATA>' + crmadmin.membernumber_reset + '</DATA>'
        tree = ET.fromstring(reset)
        for elem in tree.iter():
            # print(elem.tag, elem.text)
            if elem.text == None and elem.tag != 'DATA':
                error = 'Member number reset format error'
                break
            if elem.tag == 'Y':
                value = int(elem.text)
                now_y = datetime_now_utc.year
                if value != now_y:
                    number = 1

                    crmadmin.membernumber_reset = crmadmin.membernumber_reset.replace('<Y>' + str(value) + '</Y>', '<Y>' + str(now_y) + '</Y>')
                    crmadmin.save()
                    # save xml to db
            elif elem.tag == 'm':
                value = int(elem.text)
                now_m = datetime_now_utc.month
                if value != now_m:
                    number = 1
                    
                    crmadmin.membernumber_reset = crmadmin.membernumber_reset.replace('<m>' + str(value) + '</m>', '<m>' + str(now_m) + '</m>')
                    crmadmin.save()
            elif elem.tag == 'd':
                value = int(elem.text)
                now_d = datetime_now_utc.day
                if value != now_d:
                    number = 1

                    crmadmin.membernumber_reset = crmadmin.membernumber_reset.replace('<d>' + str(value) + '</d>', '<d>' + str(now_d) + '</d>')
                    crmadmin.save()
        
    if error == '':
    # process prefix
    # membernumber_prefix is role for member number, <TEXT>MEM</TEXT><Y></Y><m></m><d></d><no></no> is Year, Month, Day, Hour, Minute, Second, Number('%Y-%m-%d %H:%M:%S')
    # e.g. <TEXT>VIP</TEXT><Y></Y><no></no> is VIP2023001       
        number_str = ''
        prefix = crmadmin.membernumber_prefix
        if prefix == '' or prefix == None :
            number_str = str(number).zfill(number_digit)
        else:
            nonumber = True
            prefix ='<DATA>' + prefix + '</DATA>'
            tree = ET.fromstring(prefix)
            for elem in tree.iter():
                # print(elem.tag, elem.text)
                if elem.tag == 'Y':
                    number_str = number_str + str(datetime_now_utc.year)
                elif elem.tag == 'm':
                    number_str = number_str + str(datetime_now_utc.month)
                elif elem.tag == 'd':
                    number_str = number_str + str(datetime_now_utc.day)
                elif elem.tag == 'no':
                    number_str = number_str + str(number).zfill(number_digit)
                    nonumber = False
                elif elem.tag == 'TEXT' :
                    if elem.text != None :
                        number_str = number_str + elem.text
            if nonumber == True:
                number_str = number_str + str(number).zfill(number_digit)
        crmadmin.membernumber_next = crmadmin.membernumber_next + 1
        crmadmin.save()
        # print(number_str)

    return error, number_str

@transaction.atomic
def new_member(
            request, datetime_now_utc:datetime,
            company:Company, username:str, password:str, enabled:bool, 
            verified:bool, verifycode_date:datetime, 
            firstname:str, lastname:str, gender:str, email:str, mobilephone_country:str, mobilephone:str, nickname:str, dob:datetime, 
            memberlevel:str, memberpoints:int, memberpointtotal:int, ):
    status = {}
    # data = {}
    error = ''

    rx_member_username = ''
    rx_member_password = ''
    rx_email = ''
    rx_mobile = ''
    rx_nickname = ''
    rx_gender = ''
    rx_dob = ''

    rx_member_username = username
    rx_member_password = password
    rx_email = email
    rx_mobilephone_country = mobilephone_country
    rx_mobile = mobilephone
    rx_nickname = nickname
    rx_gender = gender

    # change dob from Local time to UTC time
    # str_time = str(dob) + ' 00:00:00'
    # dob = datetime.strptime(str_time, "%Y-%m-%d %H:%M:%S")
    rx_dob = funLocaltoUTC(dob, company.timezone)

    # username is lowercase, auto convert to lowercase
    rx_member_username = rx_member_username.lower()

    # check miss parameters
    if error == '':
        if rx_member_username == '' :
            error = 'Username not found'
    if error == '':
        if rx_member_password == '' :
            error = 'Password not found'
    if error == '':
        if rx_email == '' :
            error = 'Email not found'
    if error == '':
        if rx_mobile == '' :
            error = 'Mobile not found'
    if error == '':
        if rx_nickname == '' :
            error = 'Nickname not found'
    if error == '':
        if rx_gender == '' :
            error = 'Gender not found'
    if error == '':
        if rx_dob == '' :
            error = 'Birthday not found'

    # check company
    if error == '':
        if company == None :
            error = 'company not found failed'
    # check username
    if error == '':
        try:
            member = Member.objects.get(username=rx_member_username, company=company)
            error = 'Username already exists'
        except :
            pass
    # check rx_member_username should be 3-20 chars
    if error == '':
        if len(rx_member_username) < 3 or len(rx_member_username) > 20 :
            error = 'Username should be 4-20 chars'
    # check password should be 8-20 chars
    if error == '':
        if len(rx_member_password) < 8 or len(rx_member_password) > 20 :
            error = 'Password should be 8-20 chars'
    # check email 
            # for development mode
    # if error == '':
    #     try:
    #         member = Member.objects.get(email=rx_email, company=company)
    #         error = 'Email already exists'
    #     except :
    #         pass
    # check email format
    if error == '':
        regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b'
        if(re.fullmatch(regex, rx_email)):
            pass       
        else:
            error = 'Email format is incorrect'


    # check mobile format
    # print('Received phone number:' + rx_mobile)
    if error == '':
        if rx_mobilephone_country[0:1] == '+' :
            rx_mobile = rx_mobilephone_country + rx_mobile
        else:
            rx_mobile = '+' + rx_mobilephone_country + rx_mobile

    if error == '':
        try:
            phone_number = phonenumbers.parse(rx_mobile)
        except:
            error = 'Mobile format is incorrect'
    if error == '':
        if phonenumbers.is_valid_number(phone_number) == False:
            error = 'Mobile format is incorrect'
    # if error == '':
    #     print(phonenumbers.is_valid_number(phone_number))
    #     print(phonenumbers.timezone.time_zones_for_number(phone_number))
    #     print('Country code:' + str(phone_number.country_code))
    #     print('National number:' + str(phone_number.national_number))
    # check mobile
    if error == '':
        try:
            member = Member.objects.get(mobile_country=str(phone_number.country_code), mobile=str(phone_number.national_number), company=company)
            error = 'Mobile already exists'
        except :
            pass

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
    # if error == '':
    #     try:
    #         rx_dob = datetime.strptime(rx_dob, '%Y_%m_%d')
    #     except:
    #         error = 'DOB format must be YYYY_MM_DD'
    
    # memberlevel:str, memberpoints:int, memberpointtotal:int, ):
    if error == '':
        if memberlevel == '' or memberlevel == None :
            memberlevel = 'SILVER'
        if memberpoints == None :
            memberpoints = 0
        if memberpointtotal == None :
            memberpointtotal = 0

    if error == '':
        # genrate member number
        error , number_str = gen_new_memberno(company, datetime_now_utc)

        try:
            crmadmin = CRMAdmin.objects.get(company=company)
        except:
            error = 'CRM Admin not found'

    if error == '':
        # new member
        verifycode = random.choices(string.ascii_uppercase + string.ascii_lowercase + string.digits, k=128)
        verifycode = ''.join(verifycode)
        # verifycode = '1234'

        member = Member.objects.create(
            company = company,
            username = rx_member_username,
            number = number_str,
            password = rx_member_password,
            verifycode = verifycode,
            verified = verified,
            verifycode_date = verifycode_date,
            enabled = enabled,
            birthday = rx_dob,
            gender = rx_gender,
            memberpoints = memberpoints,
            memberpointtotal = memberpointtotal,
            memberlevel = memberlevel,
            firstname = firstname,
            lastname = lastname,
            nickname = rx_nickname,
            mobilephone_country = str(phone_number.country_code),
            mobilephone = str(phone_number.national_number),
            email = rx_email,            
        )
        crmadmin.membernumber_next = crmadmin.membernumber_next + 1
        crmadmin.save()

        # get the http host
        http_host = request.META['HTTP_HOST']
        verify_link ='http://' + http_host + '/crm/api/verify/?app=email&username=' + rx_member_username + '&ccode=' + company.ccode +  '&verifycode=' + verifycode

        # print('Link:' + verify_link)
        # send email
        subject = 'Welcome! Please Verify Your Account - ' + company.name
        message = render_to_string('crm/email_verify.html', {
            'company': company,
            'member': member,
            'url': verify_link,
        })
        # print(message)
        message = message.replace('amp;', '')
        # print(message)
        # message = escape(mark_safe(message))
        toemail = rx_email
        sendemail.delay(subject, message, toemail)

        status = {'status':'success', 'msg':'Successfully! Please check your email to activate your account.' +  ' In development mode: ' + verify_link }
    else:
        status = {'status':'failed', 'msg':error}
    return status, error