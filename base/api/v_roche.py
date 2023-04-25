from datetime import timedelta
from django.utils import timezone
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.db.models import Q
from .views import setting_APIlogEnabled, visitor_ip_address, loginapi, funUTCtoLocal, counteractive
from .v_display import newdisplayvoice
from base.models import APILog, Branch, CounterStatus, CounterType, Ticket, DisplayAndVoice, Setting, TicketFormat, TicketTemp, TicketRoute, TicketData, TicketLog, CounterLoginLog, UserProfile, lcounterstatus
from .serializers import rocheticketlistSerivalizer, ticketlistSerivalizer
# from .v_display import wssendwebtv
from .v_softkey import logcounterlogin, logcounterlogout
from base.ws import wsrochesms
import random
import logging

# list only show within x mins, details : the Ticket table list is too long, can not give full list to roche ios app.
rochelist_x_mins = 3

logger = logging.getLogger(__name__)
def rocheSMS(branch, tticket):
    error = ''
    if error == '':
        if branch.enabledsms == False:
            error = 'SMS disabled'
    if error == '':
        if branch.smsmsg == None or branch.smsmsg == '' :
            error = 'SMS message is blank'
    
    if error == '':
        ttype = tticket.tickettype
        objpuser = UserProfile.objects.filter(branchs=branch, tickettype__contains=ttype).exclude(mobilephone=None).exclude(mobilephone='')
        for puser in objpuser:
            if puser.user.is_active == True:
                smsmsg = branch.smsmsg.replace('<TICKET>', tticket.tickettype + tticket.ticketnumber)
                wsrochesms(branch.bcode, puser.mobilephone, smsmsg)

                pass
    else:
        logger.info(error)

    pass


@api_view(['POST'])
def postRocheLogin(request):
# Request :
# 'POST /api/applogin/?username=xxx&password=xxx&token=xxx&app=ios&version=0.1&branchcode=xxx'

# Response :
# {
#     "status":"OK/Error",
#     "msg":"Ticket route not found",
#     "data": {
#         "name": "Mary Li",
#         "ttype": "ABCDEFGHIJKLMNOPQRSTUVWXYZ",
#     }
# }

    status = dict({})
    msg = dict({})
    context = dict({})

    rx_username = request.GET.get('username') if request.GET.get('username') != None else ''
    rx_password = request.GET.get('password') if request.GET.get('password') != None else ''
    rx_token = request.GET.get('token') if request.GET.get('token') != None else ''
    rx_app = request.GET.get('app') if request.GET.get('app') != None else ''
    rx_version = request.GET.get('version') if request.GET.get('version') != None else ''
    rx_bcode = request.GET.get('branchcode') if request.GET.get('branchcode') != None else ''

    datetime_now =timezone.now()
   
     
   
    branch = None
    if status == dict({}) :
        if rx_bcode == '' :
            status = dict({'status': 'Error'})
            msg =  dict({'msg':'No branch code'})
        else :
            # check branch        
            branchobj = Branch.objects.filter( Q(bcode=rx_bcode) )
            if branchobj.count() != 1:
                # branch not found
                status = dict({'status': 'Error'})
                msg =  dict({'msg':'Branch not found'})   
            else:
                branch = branchobj[0]        

    # Save Api Log
    if setting_APIlogEnabled(branch) == True :
        APILog.objects.create(
            logtime=datetime_now,
            requeststr = request.build_absolute_uri() ,
            ip = visitor_ip_address(request),
            app = rx_app,
            version = rx_version,
            logtext = 'API call : Counter login',
        )



    if status == dict({}) :
        
        loginreply, user = loginapi(request , rx_username, rx_password, rx_token, branch)

        if loginreply != 'OK':
            status = dict({'status': 'Error'})
            msg =  dict({'msg':loginreply})   
   
    # get user profiles
    if status == dict({}) :
        userp = None
        obj_userp =UserProfile.objects.filter(user__exact=user)
        if obj_userp.count() == 1 :
            userp = obj_userp[0]
        if userp == None :
            status = dict({'status': 'Error'})
            msg =  dict({'msg':'user profile not found or more then one'})       

 
    # check the counter is already login 
    if status == dict({}) :
        context = {'name': user.first_name + ' ' + user.last_name , 'ttype': userp.tickettype,
        }
        context = dict({'data':context})    
    
        status = dict({'status': 'OK'})
        msg =  dict({'msg':'Have a nice day'})  

                                        
                                     
                
    output = status | msg | context
    return Response(output)







# edit from v_ticket getFirstPrint
@api_view(['GET'])
def getRocheFirstPrint(request):

    status = dict({})
    msg = dict({})
    context = dict({})

    username = request.GET.get('username') if request.GET.get('username') != None else ''
    password = request.GET.get('password') if request.GET.get('password') != None else ''
    token = request.GET.get('token') if request.GET.get('token') != None else ''
    app = request.GET.get('app') if request.GET.get('app') != None else ''
    version = request.GET.get('version') if request.GET.get('version') != None else ''
    bcode = request.GET.get('branchcode') if request.GET.get('branchcode') != None else ''

    #datetime_now = datetime.utcnow()
    datetime_now =timezone.now()

    branch = None
    if status == dict({}) :
        if bcode == '' :
            status = dict({'status': 'Error'})
            msg =  dict({'msg':'No branch code'})
        else :
            # check branch        
            branchobj = Branch.objects.filter( Q(bcode=bcode) )
            if branchobj.count() != 1:
                # branch not found
                status = dict({'status': 'Error'})
                msg =  dict({'msg':'Branch not found'})   
            else:
                branch = branchobj[0]        

    # Save Api Log
    if setting_APIlogEnabled(branch) == True :
        APILog.objects.create(
            logtime=datetime_now,
            requeststr = request.build_absolute_uri() ,
            ip = visitor_ip_address(request),
            app = app,
            version = version,
            logtext = 'API call : First Print API',
        )


    if status == dict({}) :
        
        loginreply, user = loginapi(request , username, password, token, None)

        if loginreply != 'OK':
            status = dict({'status': 'Error'})
            msg =  dict({'msg':loginreply})    

    if status == dict({}) :
        starttime = datetime_now + timedelta(minutes=-rochelist_x_mins)

        ticketlist = Ticket.objects.filter( Q(branch=branch) & Q(tickettime__range=[starttime, datetime_now]) & Q(locked=False))
        serializers  = rocheticketlistSerivalizer(ticketlist, many=True)
        context = dict({'data':serializers.data})
        status = dict({'status': 'OK'})
    
    output = status | msg | context
    return Response(output)



# edit from v_ticket getFirstPrint
@api_view(['GET'])
def getRocheFirstPrintTest(request):

    status = dict({})
    msg = dict({})
    context = dict({})

    username = request.GET.get('username') if request.GET.get('username') != None else ''
    password = request.GET.get('password') if request.GET.get('password') != None else ''
    token = request.GET.get('token') if request.GET.get('token') != None else ''
    app = request.GET.get('app') if request.GET.get('app') != None else ''
    version = request.GET.get('version') if request.GET.get('version') != None else ''
    bcode = request.GET.get('branchcode') if request.GET.get('branchcode') != None else ''
    listlen = request.GET.get('listlen') if request.GET.get('listlen') != None else ''
    testtype = request.GET.get('testtype') if request.GET.get('testtype') != None else ''

    if listlen == '' :
        listlen = 1
    else :
        listlen = int(listlen)

    #datetime_now = datetime.utcnow()
    datetime_now =timezone.now()

    branch = None
    if status == dict({}) :
        if bcode == '' :
            status = dict({'status': 'Error'})
            msg =  dict({'msg':'No branch code'})
        else :
            # check branch        
            branchobj = Branch.objects.filter( Q(bcode=bcode) )
            if branchobj.count() != 1:
                # branch not found
                status = dict({'status': 'Error'})
                msg =  dict({'msg':'Branch not found'})   
            else:
                branch = branchobj[0]        

    # Save Api Log
    if setting_APIlogEnabled(branch) == True :
        APILog.objects.create(
            logtime=datetime_now,
            requeststr = request.build_absolute_uri() ,
            ip = visitor_ip_address(request),
            app = app,
            version = version,
            logtext = 'API call : First Print API',
        )


    if status == dict({}) :
        
        loginreply, user = loginapi(request , username, password, token, None)

        if loginreply != 'OK':
            status = dict({'status': 'Error'})
            msg =  dict({'msg':loginreply})    

    if status == dict({}) :

        tlist = []

        for i in range(listlen):

            if testtype == '':
                asctt = random.randint(65, 67)
                tt = chr(asctt)
            else :
                tt = testtype.upper()

            tno = str(random.randint(0, 9)) + str(random.randint(0, 9))+ str(random.randint(0, 9))

            tlist.append(dict({'tickettype': tt}) | dict({'ticketnumber': tno}) | dict({'tickettime': datetime_now}) )

       

        context = dict({ 'data':  tlist })        
        status = dict({'status': 'OK'})
    
    output = status | msg | context
    return Response(output)