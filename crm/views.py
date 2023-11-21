from django.shortcuts import render
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from crm.models import Member
from base.models import Branch
import random
import string
from datetime import datetime, timedelta, timezone

# Create your views here.
def WelcomeView(request):
    content = {'user':request.user}
    return render(request, 'crm/welcome.html', content)

@api_view(['GET'])
# @permission_classes([IsAuthenticated])
def crmUserLoginView(request):
    status = {}
    data = {}

    app = request.GET.get('app') if request.GET.get('app') != None else ''
    version = request.GET.get('version') if request.GET.get('version') != None else ''
    username = request.GET.get('username') if request.GET.get('username') != None else ''
    password = request.GET.get('password') if request.GET.get('password') != None else ''
    bcode = request.GET.get('bcode') if request.GET.get('bcode') != None else ''

    if app == '' or version == '' or username == '' or password == '' or bcode == '':
        status = {'status':'failed', 'msg':'Missing parameters'}
        return Response(status)

    member_no = ''
    member_token = ''
    error = ''
    error, member_no, member_token = crmUserLogin(username, password, bcode)

    if error == '':        
        status = {'status':'success', 'msg':'Login success', }
        data = {'member_no':member_no, 'member_token':member_token, }
    else:
        status = {'status':'failed', 'msg':error}
        data = {}
    return Response(status | data )

def crmUserLogin(username, password, bcode):
    error = ''
    member_no = ''
    member_token = ''
    datetime_now_utc = datetime.now(timezone.utc)

    branch = None
    if error == '' :
        try:
            branch = Branch.objects.get(bcode=bcode)
        except :
            error = 'Login failed'
    if error == '' :
        try:
            member = Member.objects.get(username=username, branch=branch, password=password)
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

    return error, member_no, member_token