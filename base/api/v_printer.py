from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
# from django.utils import timezone
from django.urls import reverse
from urllib.parse import urlencode
from django.db.models import Q
from datetime import datetime, timezone, timedelta
from base.models import APILog, Branch, PrinterStatus,  TicketFormat, Ticket, TicketTemp
from base.models import TicketRoute, TicketData, TicketLog, lcounterstatus
from .serializers import printerstatusSerivalizer, ticketlistSerivalizer
from .views import setting_APIlogEnabled, visitor_ip_address, loginapi, funUTCtoLocal, checkuser
from .v_roche import rocheSMS
from base.ws import wssendwebtv, wssendql, wssendprinterstatus, wsSendPrintTicket
import random
from django.contrib.auth.models import User, Group
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def getFirstPrint(request):

    status = dict({})
    msg = dict({})
    context = dict({})

    # username = request.GET.get('username') if request.GET.get('username') != None else ''
    # password = request.GET.get('password') if request.GET.get('password') != None else ''
    # token = request.GET.get('token') if request.GET.get('token') != None else ''
    app = request.GET.get('app') if request.GET.get('app') != None else ''
    version = request.GET.get('version') if request.GET.get('version') != None else ''
    bcode = request.GET.get('branchcode') if request.GET.get('branchcode') != None else ''

    #datetime_now = datetime.utcnow()
    datetime_now =datetime.now(timezone.utc)

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

    # check user
    if status == dict({}) :
        error, user = checkuser(request.user, branch, '')
        if error !='OK' :
            status = dict({'status': 'Error'})
            msg =  dict({'msg':error})

    if status == dict({}) :
        # userapi = User.objects.get(username='userapi')
        userweb = User.objects.get(username='userweb')
        ticketlist = TicketTemp.objects.filter( Q(branch=branch) & Q(printedtimes=0) & Q(locked=False) & ~Q(createdby=userweb))
        serializers  = ticketlistSerivalizer(ticketlist, many=True)
        context = dict({'data':serializers.data})
        status = dict({'status': 'OK'})
        # msg =  dict({'msg':branch.queuepriority})
    
    output = status | msg | context
    return Response(output)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def postTicketPrinted(request):

    status = dict({})
    msg = dict({})
    context = dict({})

    # username is optional
    username = request.GET.get('username') if request.GET.get('username') != None else ''
    # password = request.GET.get('password') if request.GET.get('password') != None else ''
    # token = request.GET.get('token') if request.GET.get('token') != None else ''
    app = request.GET.get('app') if request.GET.get('app') != None else ''
    version = request.GET.get('version') if request.GET.get('version') != None else ''
    bcode = request.GET.get('branchcode') if request.GET.get('branchcode') != None else ''
    ttype = request.GET.get('tickettype') if request.GET.get('tickettype') != None else ''
    tnumber = request.GET.get('ticketnumber') if request.GET.get('ticketnumber') != None else ''
    tickettime = request.GET.get('tickettime') if request.GET.get('tickettime') != None else ''
 

    #datetime_now = datetime.utcnow()
    datetime_now =datetime.now(timezone.utc)

    # check input
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
            logtext = 'API call : Ticket printed',
        )

    if status == dict({}) :
        if tnumber == '' :
            status = dict({'status': 'Error'})
            msg =  dict({'msg':'No printer number'})  
    if status == dict({}) :
        if ttype == '' :
            status = dict({'status': 'Error'})
            msg =  dict({'msg':'No ticket type'})  
    if status == dict({}) :
        if tickettime == '' :   
            status = dict({'status': 'Error'})
            msg =  dict({'msg':'No ticket time'})  




    stickettime = ''
    if status == dict({}) :
        try:
            stickettime = str(datetime.strptime(tickettime, '%Y-%m-%dT%H:%M:%S.%fZ'))
        except:
            stickettime = ''
        if stickettime == '' :
            try :
                stickettime = str(datetime.strptime(tickettime, '%Y-%m-%dT%H:%M:%SZ'))
            except:
                stickettime = ''
                status = dict({'status': 'Error'})
                msg =  dict({'msg':'Ticket time format not correct. Should be : 2022-05-19T23:59:59.123456Z'}) 
                        
    # check user
    if status == dict({}) :
        error, user = checkuser(request.user, branch, '')
        if error !='OK' :
            status = dict({'status': 'Error'})
            msg =  dict({'msg':error})

    
    if status == dict({}) :
        ticketobj = TicketTemp.objects.filter( Q(branch=branch) & Q(tickettype=ttype) &  Q(ticketnumber=tnumber) & Q(tickettime=tickettime) )
        if ticketobj.count() == 0 :
            status = dict({'status': 'Error'})
            msg =  dict({'msg':'Ticket not found'})  
    if status == dict({}) :
        for ticket in ticketobj :
            if stickettime != '' :
                ticket.printedtimes = ticket.printedtimes +1
                ticket.save()
                status = dict({'status': 'OK'})
                localdate_now = funUTCtoLocal(datetime_now, branch.timezone)
                TicketLog.objects.create(
                    tickettemp=ticket,
                    logtime=datetime_now,
                    app = app,
                    version = version,
                    logtext='API Ticket Printed ' + branch.bcode + '_' + ttype + '_'+ tnumber + '_' + localdate_now.strftime('%Y-%m-%d_%H:%M:%S'),
                    user=user,
                )
                context = dict({'Printed times': str(ticket.printedtimes)})
                context = dict({'data':context})
    output = status | msg | context
    return Response(output)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def postUpdatePrinter(request):

    status = dict({})
    msg = dict({})
    context = dict({})

    app = request.GET.get('app') if request.GET.get('app') != None else ''
    version = request.GET.get('version') if request.GET.get('version') != None else ''
    bcode = request.GET.get('branchcode') if request.GET.get('branchcode') != None else ''
    rxprinternumber = request.GET.get('printernumber') if request.GET.get('printernumber') != None else ''
    rxpstatus = request.GET.get('status') if request.GET.get('status') != None else ''
    rxpstatustext = request.GET.get('statustext') if request.GET.get('statustext') != None else '' 
    


    rxprinternumber = rxprinternumber.upper()
    #datetime_now = datetime.utcnow()
    datetime_now =datetime.now(timezone.utc)

    # check input
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
            logtext = 'API call : Update Printer Status API',
        )

    if status == dict({}) :
        if rxprinternumber == '' :
            status = dict({'status': 'Error'})
            msg =  dict({'msg':'No printer number'})  

    if status == dict({}) :
        if rxpstatus == '' :
            status = dict({'status': 'Error'})
            msg =  dict({'msg':'No Printer status'})  

    # check user
    if status == dict({}) :
        error, user = checkuser(request.user, branch, '')
        if error !='OK' :
            status = dict({'status': 'Error'})
            msg =  dict({'msg':error})   

    if status == dict({}) :
        # update db
    
        objps = PrinterStatus.objects.filter(Q(branch=branch) & Q(printernumber=rxprinternumber))
        if objps.count() < 1 :
            # create new 
            PrinterStatus.objects.create(
                branch = branch,
                printernumber=rxprinternumber,
                status = rxpstatus ,
                statustext = rxpstatustext,
            )            
        else:
            pss = objps[0]
            pss.status = rxpstatus
            pss.statustext = rxpstatustext
            pss.save()
        status = dict({'status': 'OK'})
        # Websocket send Printer status
        wssendprinterstatus(branch.bcode)
        # msg =  dict({'msg':'Everything will be OK.'}) 
    
    output = status | msg | context
    return Response(output)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def getPrinterStatus(request):

    status = dict({})
    msg = dict({})
    context = dict({})

    # username is optional
    username = request.GET.get('username') if request.GET.get('username') != None else ''
    app = request.GET.get('app') if request.GET.get('app') != None else ''
    version = request.GET.get('version') if request.GET.get('version') != None else ''
    bcode = request.GET.get('branchcode') if request.GET.get('branchcode') != None else ''

    #datetime_now = datetime.utcnow()
    datetime_now =datetime.now(timezone.utc)

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

    # check user
    if status == dict({}) :
        error, user = checkuser(request.user, branch, '')
        if error !='OK' :
            status = dict({'status': 'Error'})
            msg =  dict({'msg':error})  

    if status == dict({}) :
        printerstatuslist = PrinterStatus.objects.filter( Q(branch=branch) ).order_by('-updated')
        serializers  = printerstatusSerivalizer(printerstatuslist, many=True)
        context = dict({'data':serializers.data})
        status = dict({'status': 'OK'})

        # msg =  dict({'msg':'Everything will be OK.'})
    
    output = status | msg | context
    return Response(output)

