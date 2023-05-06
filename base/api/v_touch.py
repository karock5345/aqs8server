
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.utils import timezone
from django.db.models import Q

from base.models import APILog, Branch, TicketFormat, Ticket, TicketTemp
from base.models import TicketRoute, TicketData, TicketLog, lcounterstatus
from .views import setting_APIlogEnabled, visitor_ip_address, funUTCtoLocal, checkuser
from .v_roche import rocheSMS
from base.ws import wssendwebtv, wssendql, wsSendPrintTicket
import random

def gensecuritycode():
    sc = ''
  
    for i in range(3):
        sc = sc + random.choice("abcdefghijklmnopqrstuvwxyz0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ")

    return sc

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
                logtext='TicketKey API ticket created : '  + branch.bcode + '_' + ttype + '_'+ ticketno_str + '_' + datetime_now.strftime('%Y-%m-%dT%H:%M:%S.%fZ') + ' Printer Number: ' + pno ,
                user=user,
            )

        wssendwebtv(branch.bcode, countertype.name)
        wssendql(branch.bcode, countertype.name,tickettemp,'add')
        wsSendPrintTicket(branch.bcode, ttype, ticketno_str, datetime_now, tickettext, pno)
        rocheSMS(branch, tickettemp)


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
        
        ticketno_str, countertype, tickettemp, ticket, error = newticket(branch, ttype, pno, remark, datetime_now, user, app, version)

        if error == '' :
            TicketLog.objects.create(
                ticket=ticket,
                tickettemp=tickettemp,
                logtime=datetime_now,
                app = app,
                version = version,
                logtext='TicketKey API ticket created : '  + branch.bcode + '_' + ttype + '_'+ ticketno_str + '_' + datetime_now.strftime('%Y-%m-%dT%H:%M:%S.%fZ') + ' Printer Number: ' + pno ,
                user=user,
            )
        else :
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

