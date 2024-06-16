from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.utils import timezone
from django.db.models import Q

from base.models import APILog, Branch, TicketFormat, Ticket, TicketTemp
from base.models import TicketRoute, TicketData, TicketLog, lcounterstatus
from booking.models import Booking, TimeSlot
from .views import setting_APIlogEnabled, visitor_ip_address, funUTCtoLocal, checkuser
from .v_roche import rocheSMS
from base.ws import wssendwebtv, wssendql, wsSendPrintTicket, wssenddispwait
import random
from .v_softkey_sub import cc_autocall
from .serializers import touchkeysSerivalizer
from django.db import transaction
from aqs.settings import DOMAIN
import urllib.parse

def gensecuritycode():
    sc = ''
  
    for i in range(3):
        sc = sc + random.choice("abcdefghijklmnopqrstuvwxyz0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ")

    return sc

@transaction.atomic
# parameter 'pno' data changed from <PNO>P1</PNO> -> P1,P2, ... support multiple printers
def newticket_v830(branch, ttype, pnos, remark, datetime_now, user, app, version):
    ticketno_str = ''
    countertype = None
    tickettemp = None 
    ticket = None
    error = ''

    if error == '' :
        # ticket format
        ticketobj = TicketFormat.objects.filter(Q(branch=branch) & Q(ttype=ttype))
        if not(ticketobj.count() == 1) :
            error =  'TicketFormat not found'

    if error == '' :
        # Lock the ticket format nowait=False
        try:
            ticketformat = TicketFormat.objects.select_for_update().get(id=ticketobj[0].id)
        except Exception as e:
            error = e.__str__()
    
    if error == '' :
        if ticketformat.enabled == False :
            error = 'Ticket disabled'

    if error == '' :
        # check ticket time
        time_now = datetime_now.time()

        btickettime = False    
   
        if branch.tickettimestart < branch.tickettimeend :
            if (branch.tickettimestart <= time_now) & (time_now <= branch.tickettimeend) :
                btickettime = True
        else :
            if not((branch.tickettimeend <= time_now) & (time_now <= branch.tickettimestart)) :
                btickettime = True                        
        if btickettime == False :  
            error = 'Out of ticket time range'

    if error == '' :         
        # find out the countertype 
        routeobj = TicketRoute.objects.filter(branch=branch, step=1, tickettype=ttype)                        
        if routeobj.count() != 1 :
            error = 'Ticket route not found'
        else:
            route = routeobj[0]             

    if error == '' :

        # create ticket - get next ticket number
        if branch.ticketrepeatnumber == True :
            ticketno = ticketformat.ticketnext
            ticketformat.ticketnext = ticketformat.ticketnext + 1
            if ticketformat.ticketnext > branch.ticketmax :
                ticketformat.ticketnext = 1
            ticketformat.save()
        else:
            ticketno = branch.ticketnext
            branch.ticketnext = branch.ticketnext + 1
            if branch.ticketnext > branch.ticketmax :
                branch.ticketnext = 1
            branch.save()
        ticketnoformat = branch.ticketnoformat
        ticketno_str = str(ticketno)
        ticketno_str = ticketno_str.zfill(len(ticketnoformat))
        sc = gensecuritycode()

        # for myTicket old school
        # base_url = reverse('myticket')
        # query_string =  urlencode({
        #                             'tt':ttype, 
        #                             'no':ticketno_str, 
        #                             'bc':branch.bcode, 
        #                             'sc':sc,
        #                             }) 
        # url = '{}?{}'.format(base_url, query_string)  # 3 ip/my/?tt=A&no=003&bc=KB&sc=vVL

        url = '/my/' + branch.bcode + '/' + ttype +'/' + ticketno_str + '/' + sc + '/'
        # myticketlink =  ('{0}://{1}'.format(request.scheme, request.get_host()) +   url)
        myticketlink = DOMAIN + url
        


        countertype = route.countertype
        # waiting on queue +1
        route.waiting = route.waiting + 1
        route.save()
        
        # -if user is not None:
        # -    return Response(user.username) 
        # add DB -> Ticket, TicketLog, TicketData
        # data : tickettext, datetime_now, ttype, ticketno_str
        ticket = Ticket.objects.create(
            tickettype=ttype, 
            ticketnumber=ticketno_str, 
            branch=branch, 
            step=1,
            countertype=countertype,
            ticketroute=route,
            ticketformat=ticketformat,
            status=lcounterstatus[0] ,
            tickettime=datetime_now, 
            # tickettext=tickettext,
            printernumber=pnos ,
            printedtimes = 0 ,
            user=user,
            createdby=user,
            remark=remark,
        )
       
        tickettemp = TicketTemp.objects.create(
            tickettype=ttype, 
            ticketnumber=ticketno_str, 
            branch=branch, 
            step=1,
            countertype=countertype,
            ticketroute=route,
            ticketformat=ticketformat,
            status=lcounterstatus[0] ,
            tickettime=datetime_now, 
            # tickettext=tickettext,
            printernumber=pnos ,
            printedtimes = 0 ,
            user=user,
            createdby=user,
            remark=remark,
            ticket=ticket,
            securitycode=sc,
            myticketlink=myticketlink,
        )

        TicketData.objects.create(
            tickettemp=tickettemp,
            branch = branch,
            countertype=countertype,
            step=ticket.step,
            starttime = datetime_now,
            startuser=user,
        )
        TicketLog.objects.create(
                ticket=ticket,
                tickettemp=tickettemp,
                logtime=datetime_now,
                app = app,
                version = version,
                logtext='TicketKey API ticket created '  + branch.bcode + '_' + ttype + '_'+ ticketno_str + '_' + datetime_now.strftime('%Y-%m-%dT%H:%M:%S.%fZ') + ' Printer Number: ' + pnos ,
                user=user,
            )

        wssendwebtv(branch.bcode, countertype.name)
        # websocket to display panel for waiting ticket
        wssenddispwait(branch, countertype, ticket)
        wssendql(branch.bcode, countertype.name,tickettemp,'add')


        # if pnos != '' and pnos != None:
        #     pno_list = pnos.split(",")
        #     for p in pno_list:
        #         wsSendPrintTicket(branch.bcode, ttype, ticketno_str, datetime_now, tickettext, p)

     
        
        # for Roche send SMS to staff when new ticket issued
        # rocheSMS(branch, tickettemp)

        # call centre mode auto send ticket to counter
        if countertype.countermode == 'cc':
            cc_autocall(countertype,  app, version, datetime_now)

    return ticketno_str, countertype, tickettemp, ticket, error

def printTicket(branch:Branch, tickettemp:TicketTemp, ticketformat:TicketFormat, datetime_now, pnos):

    if pnos != '' and pnos != None:
        
        p_ttype = tickettemp.tickettype_disp
        p_ticketno_str = tickettemp.ticketnumber_disp
        str_appointment_time = '- - -'
        booking = None
        if tickettemp.booking_id != None:
            try:
                booking = Booking.objects.get(id=tickettemp.booking_id)
            except Booking.DoesNotExist:
                booking = None
            if booking != None:
                timeslot = booking.timeslot
                appointment_time = timeslot.start_date
                appointment_time_local = funUTCtoLocal(appointment_time, branch.timezone)
                str_appointment_time = appointment_time_local.strftime('%H:%M:%S %d-%m-%Y')

            
        # ticket text
        tickettext = ticketformat.tformat
        tickettext = tickettext.replace('<TICKET>','<TEXT>' + p_ttype + p_ticketno_str)                        
        localtime = funUTCtoLocal(datetime_now, branch.timezone)
        localtime_str = localtime.strftime('%H:%M:%S %d-%m-%Y')
        tickettext = tickettext.replace('<DATETIME>', '<TEXT>' + localtime_str)
        tickettext = tickettext.replace('<MYTICKET>', tickettemp.myticketlink)
        tickettext = tickettext.replace('<APPOINT>', '<TEXT>' + str_appointment_time)

        tickettemp.tickettext = tickettext
        tickettemp.save()
        
        pno_list = pnos.split(",")
        for p in pno_list:
            xmlp = '<PNO>' + p + '</PNO>'
            wsSendPrintTicket(branch.bcode, tickettemp.tickettype , tickettemp.ticketnumber, datetime_now, tickettemp.tickettext, xmlp )


def newticket(branch, ttype, pno, remark, datetime_now, user, app, version):
    ticketno_str = ''
    countertype = None
    tickettemp = None 
    ticket = None
    error = ''

    if error == '' :
        # ticket format
        ticketobj = TicketFormat.objects.filter( Q(branch=branch) & Q(ttype=ttype) )
        if not(ticketobj.count() == 1) :
            error =  'TicketFormat not found'
    if error == '' :
        ticketformat = ticketobj[0]

        if ticketformat.enabled == False :
            error = 'Ticket disabled'

    if error == '' :
        # check ticket time
        time_now = datetime_now.time()

        btickettime = False    
   
        if branch.tickettimestart < branch.tickettimeend :
            if (branch.tickettimestart <= time_now) & (time_now <= branch.tickettimeend) :
                btickettime = True
        else :
            if not((branch.tickettimeend <= time_now) & (time_now <= branch.tickettimestart)) :
                btickettime = True                        
        if btickettime == False :  
            error = 'Out of ticket time range'

    if error == '' :         
        # find out the countertype 
        routeobj = TicketRoute.objects.filter(branch=branch, step=1, tickettype=ttype)                        
        if routeobj.count() != 1 :
            error = 'Ticket route not found'
        else:
            route = routeobj[0]             

    if error == '' :

        # create ticket - get next ticket number
        if branch.ticketrepeatnumber == True :
            ticketno = ticketformat.ticketnext
            ticketformat.ticketnext = ticketformat.ticketnext + 1
            if ticketformat.ticketnext > branch.ticketmax :
                ticketformat.ticketnext = 1
            ticketformat.save()
        else:
            ticketno = branch.ticketnext
            branch.ticketnext = branch.ticketnext + 1
            if branch.ticketnext > branch.ticketmax :
                branch.ticketnext = 1
            branch.save()
        ticketnoformat = branch.ticketnoformat
        ticketno_str = str(ticketno)
        ticketno_str = ticketno_str.zfill(len(ticketnoformat))
        sc = gensecuritycode()

        # for myTicket old school
        # base_url = reverse('myticket')
        # query_string =  urlencode({
        #                             'tt':ttype, 
        #                             'no':ticketno_str, 
        #                             'bc':branch.bcode, 
        #                             'sc':sc,
        #                             }) 
        # url = '{}?{}'.format(base_url, query_string)  # 3 ip/my/?tt=A&no=003&bc=KB&sc=vVL

        url = '/my/' + branch.bcode + '/' + ttype +'/' + ticketno_str + '/' + sc + '/'
        # myticketlink =  ('{0}://{1}'.format(request.scheme, request.get_host()) +   url)
        url = urllib.parse.urljoin( DOMAIN , url)
       
        myticketlink = url
        
        # ticket text
        tickettext = ticketformat.tformat
        tickettext = tickettext.replace('<TICKET>','<TEXT>'+ ttype+ticketno_str)                        
        localtime = funUTCtoLocal(datetime_now, branch.timezone)
        localtime_str = localtime.strftime('%H:%M:%S %d-%m-%Y')
        tickettext = tickettext.replace('<DATETIME>', '<TEXT>' + localtime_str)
        tickettext = tickettext.replace('<MYTICKET>', myticketlink)

        countertype = route.countertype
        # waiting on queue +1
        route.waiting = route.waiting + 1
        route.save()
        
        # -if user is not None:
        # -    return Response(user.username) 
        # add DB -> Ticket, TicketLog, TicketData
        # data : tickettext, datetime_now, ttype, ticketno_str
        ticket = Ticket.objects.create(
            tickettype=ttype, 
            ticketnumber=ticketno_str, 
            branch=branch, 
            step=1,
            countertype=countertype,
            ticketroute=route,
            ticketformat=ticketformat,
            status=lcounterstatus[0] ,
            tickettime=datetime_now, 
            tickettext=tickettext,
            printernumber=pno ,
            printedtimes = 0 ,
            user=user,
            createdby=user,
            remark=remark,
        )
       
        tickettemp = TicketTemp.objects.create(
            tickettype=ttype, 
            ticketnumber=ticketno_str, 
            branch=branch, 
            step=1,
            countertype=countertype,
            ticketroute=route,
            ticketformat=ticketformat,
            status=lcounterstatus[0] ,
            tickettime=datetime_now, 
            tickettext=tickettext,
            printernumber=pno ,
            printedtimes = 0 ,
            user=user,
            createdby=user,
            remark=remark,
            ticket=ticket,
            securitycode=sc,
            myticketlink=myticketlink,
        )

        TicketData.objects.create(
            tickettemp=tickettemp,
            branch = branch,
            countertype=countertype,
            step=ticket.step,
            starttime = datetime_now,
            startuser=user,
        )
        TicketLog.objects.create(
                ticket=ticket,
                tickettemp=tickettemp,
                logtime=datetime_now,
                app = app,
                version = version,
                logtext='TicketKey API ticket created '  + branch.bcode + '_' + ttype + '_'+ ticketno_str + '_' + datetime_now.strftime('%Y-%m-%dT%H:%M:%S.%fZ') + ' Printer Number: ' + pno ,
                user=user,
            )

        wssendwebtv(branch.bcode, countertype.name)
        # websocket to display panel for waiting ticket
        wssenddispwait(branch, countertype, ticket)
        wssendql(branch.bcode, countertype.name,tickettemp,'add')
        wsSendPrintTicket(branch.bcode, ttype, ticketno_str, datetime_now, tickettext, pno)
        
        # for Roche send SMS to staff when new ticket issued
        # rocheSMS(branch, tickettemp)

        # call centre mode auto send ticket to counter
        if countertype.countermode == 'cc':
            cc_autocall(countertype,  app, version, datetime_now)

    return ticketno_str, countertype, tickettemp, ticket, error

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def postTicket(request):
    # {
    #    "status":"OK/Error",
    #    "msg":"Ticket route not found",
    #    "data":[
    #         {"ticket":"A001","tickettime":"2022-11-30","i":"1"}   
    #    ]
    # }
    status = dict({})
    msg = dict({})
    context = dict({})
    # username is optional parameter. If not provided, it will be set to request.user
    username = request.GET.get('username') if request.GET.get('username') != None else ''
    # password = request.GET.get('password') if request.GET.get('password') != None else ''
    # token = request.GET.get('token') if request.GET.get('token') != None else ''
    app = request.GET.get('app') if request.GET.get('app') != None else ''
    version = request.GET.get('version') if request.GET.get('version') != None else ''
    bcode = request.GET.get('branchcode') if request.GET.get('branchcode') != None else ''
    ttype = request.GET.get('tickettype') if request.GET.get('tickettype') != None else ''
    pno = request.GET.get('printernumber') if request.GET.get('printernumber') != None else ''
    remark = request.GET.get('remark') if request.GET.get('remark') != None else ''

    #datetime_now = datetime.utcnow()
    datetime_now =timezone.now()

 

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
                if branch.enabled == False :
                    status = dict({'status': 'Error'})
                    msg =  dict({'msg':'Branch disabled'})
    # check user
    if status == dict({}) :
        error, user = checkuser(request.user, branch, username)
        if error !='OK' :
            status = dict({'status': 'Error'})
            msg =  dict({'msg':error})

    if status == dict({}) :
        # check subscribe
        if branch.subscribe == True :
            if datetime_now > branch.subend :
                status = dict({'status': 'Error'})
                msg =  dict({'msg':'Branch Subscribe'})
        pass

    if status == dict({}) :    
        if pno == '' :
            status = dict({'status': 'Error'})
            msg =  dict({'msg':'No printer number'})  
    if status == dict({}) :
        if ttype == '' :
            status = dict({'status': 'Error'})
            msg =  dict({'msg':'No ticket type'})   

     # Save Api Log
    if setting_APIlogEnabled(branch) == True :
        APILog.objects.create(
            logtime=datetime_now,
            requeststr = request.build_absolute_uri() ,
            ip = visitor_ip_address(request),
            app = app,
            version = version,
            logtext = 'API call : Ticket Key',
        ) 

    # if status == dict({}) :
        
    #     loginreply, user = loginapi(request , username, password, token, None)

    #     if loginreply != 'OK':
    #         status = dict({'status': 'Error'})
    #         msg =  dict({'msg':loginreply})   
         
    if status == dict({}) :
        # old version no database lock may be cause double ticket number
        # ticketno_str, countertype, tickettemp, ticket, error = newticket(branch, ttype, pno, remark, datetime_now, user, app, version)
        # new version with database lock
        ticketno_str, countertype, tickettemp, ticket, error = newticket_v830(branch, ttype, pno, remark, datetime_now, user, app, version)
        if error == '' :
            printTicket(branch, tickettemp, tickettemp.ticketformat, datetime_now, tickettemp.printernumber)
        if error != '' :            
            status = dict({'status': 'Error'})
            msg =  dict({'msg':error})
        
    if status == dict({}) :

        test = lcounterstatus[0]
        i = lcounterstatus.index(test)
        status = dict({'status': 'OK'})                     
        context = {'ticket': ttype+ticketno_str , 'tickettime': datetime_now.strftime('%Y-%m-%dT%H:%M:%S.%fZ') , 'counterstatus': test + '[' + str(i) +']' , 'timezone': branch.timezone , 'mylink': tickettemp.myticketlink}
        context = dict({'data':context})
        

      
    output = status | msg | context
    return Response(output)  

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def postTouchKeys(request):
    # for Touch Panel to get the touch keys
    # {
    #    "status":"OK/Error",
    #    "msg":"Ticket format not found",
    #    "data":[
    #         {"tickettype":"A",
    #          "touchkey_lang1":"一般查詢",
    #          "touchkey_lang2":"General Enquiry",
    #          "touchkey_lang3":"---",
    #          "touchkey_lang4":"---"}   
    #    ]
    # }
    status = dict({})
    msg = dict({})
    context = dict({})
    app = request.GET.get('app') if request.GET.get('app') != None else ''
    version = request.GET.get('version') if request.GET.get('version') != None else ''
    bcode = request.GET.get('branchcode') if request.GET.get('branchcode') != None else ''
    
    #datetime_now = datetime.utcnow()
    datetime_now =timezone.now()

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
                if branch.enabled == False :
                    status = dict({'status': 'Error'})
                    msg =  dict({'msg':'Branch disabled'})

     # Save Api Log
    if setting_APIlogEnabled(branch) == True :
        APILog.objects.create(
            logtime=datetime_now,
            requeststr = request.build_absolute_uri() ,
            ip = visitor_ip_address(request),
            app = app,
            version = version,
            logtext = 'API Get Touch Keys',
        ) 
      
    if status == dict({}) :

        objticketformat = TicketFormat.objects.filter(branch=branch, enabled=True, for_booking=False).order_by('ttype')
        serializers  = touchkeysSerivalizer(objticketformat, many=True)
        context = dict({'data':serializers.data})
       
        status = dict({'status': 'OK'})                     
      
    output = status | msg | context
    return Response(output)  

# If tickettemp is from booking, use booking ticket format (branch.bookingTicketFormat)
# Full ticket format (e.g. B003A02)
# Short(1) ticket format (e.g. BA02) 
# Short(2) ticket format (e.g. A02)
def funGetDispTicketNumber(tickettemp:TicketTemp) :
    p_ttype = tickettemp.tickettype
    p_ticketno_str = tickettemp.ticketnumber

    booking = None
    if tickettemp.booking_id != None:
        try:
            booking = Booking.objects.get(pk=tickettemp.booking_id)
        except Booking.DoesNotExist:
            booking = None
        
    if booking != None:
        # booking to queue ticket

        # booking ticket format 0=Ticket Type + Ticket Nubmber + Sub Ticket Type + sub Ticket number, 
        #                       1=Ticket Type + Sub Ticket Type + sub Ticket number, 
        #                       2=Sub Ticket Type + sub Ticket number,
        if tickettemp.branch.bookingTicketFormat == 0 or tickettemp.branch.bookingTicketFormat == None:
            # Full ticket format (e.g. B003A02)
            p_ticketno_str = tickettemp.ticketnumber + tickettemp.booking_tickettype + tickettemp.booking_ticketnumber
        elif booking.branch.bookingTicketFormat == 1:
            # tickettemp(1) ticket format (e.g. BA02) 
            p_ticketno_str = tickettemp.booking_tickettype + tickettemp.booking_ticketnumber
        elif tickettemp.branch.bookingTicketFormat == 2:
            # Short(2) ticket format (e.g. A02)
            p_ttype = tickettemp.booking_tickettype
            p_ticketno_str = tickettemp.booking_ticketnumber
    
    return p_ttype, p_ticketno_str