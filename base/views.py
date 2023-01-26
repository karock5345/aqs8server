from django.shortcuts import render, redirect, HttpResponse
from django.urls import reverse
from urllib.parse import urlencode
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.db.models import Q
from django.contrib.auth.forms import UserCreationForm, PasswordChangeForm
from datetime import datetime
from base.decorators import *
# from django.contrib.auth.views import PasswordChangeView
# from django.urls import reverse_lazy

from .models import TicketLog, CounterStatus, CounterType, TicketData, TicketRoute, UserProfile, TicketFormat, Branch, TicketTemp, DisplayAndVoice, PrinterStatus, WebTouch
from .forms import TicketFormatForm, UserForm, UserFormAdmin, UserProfileForm,trForm, CaptchaForm
from .api.views import funUTCtoLocal, funLocaltoUTC, funUTCtoLocaltime, funLocaltoUTCtime
from django.utils.timezone import localtime, get_current_timezone
import pytz
from .api.serializers import webdisplaylistSerivalizer
from django.utils import timezone
from .api.v_softkey import funVoid
from .api.v_ticket import newticket


userweb = None
try:
    userweb = User.objects.get(username='userweb')
except:
    print('userweb not found.')

# Create your views here.
def webtouchView(request):
    # 127.0.0.1:8000/touch?bc=KB&t=01
    # t=kiosk01 is Touch Name
    context = None
    error = ''
    bcode = ''
    touchname = ''
    logofile = ''
    touchkeylist= []
    try:
        bcode = request.GET['bc']
    except:
        bcode = ''
        error = 'Branch code is blank.'
    try:
        touchname = request.GET['t']
    except:
        touchname = ''
        error = 'Touch Name is blank.'   
    print ('bcode:' + bcode)
    print ('TouchName:' + touchname)
    print ('error:' + error)

    if error == '' :
        branchobj = Branch.objects.filter( Q(bcode=bcode) )
        if branchobj.count() == 1:
            branch = branchobj[0]
            logofile = branch.webtvlogolink
            datetime_now = timezone.now()
            datetime_now_local = funUTCtoLocal(datetime_now, branch.timezone)
        else :
            error = 'Branch not found.'
    if error == '' :
        wtobj = WebTouch.objects.filter( Q(branch=branch) & Q(name=touchname)  )
        if wtobj.count() == 1:
            wt = wtobj[0]
            touchkeylist = wt.touchkey.all()
            # print(touchkeylist.count())
        else :
            error = 'Web Touch not found.'
    if error == '' :
        if wt.enabled == False :
            error = 'Web Touch Disabled.'
    if error == '' :
        if request.method =='POST':
            for key in touchkeylist:
                if key.ttype in request.POST:
                    print('Ticket ' + key.ttype)

                    ticketno_str, countertype, tickettemp, error = newticket(branch, key.ttype, '','', datetime_now, userweb, 'web', '8')
                    if error == '' :
                        # add ticketlog
                        TicketLog.objects.create(
                            tickettemp=tickettemp,
                            logtime=datetime_now,
                            app = 'web',
                            version = '8',
                            logtext='New Ticket by Web Touch: '  + tickettemp.branch.bcode + '_' + tickettemp.tickettype + '_'+ tickettemp.ticketnumber + '_' + datetime_now.strftime('%Y-%m-%dT%H:%M:%S.%fZ') ,
                            user=userweb,
                        )
                        # rediect to e-ticket
                        base_url = reverse('myticket')
                        query_string =  urlencode({
                                    'tt':tickettemp.tickettype , 
                                    'no':tickettemp.ticketnumber, 
                                    'bc':tickettemp.branch.bcode, 
                                    'sc':tickettemp.securitycode,
                                    }) 
                        url = '{}?{}'.format(base_url, query_string)  # 3 ip/my/?tt=A&no=003&bc=KB&sc=vVL
                        backurl = '{0}://{1}'.format(request.scheme, request.get_host()) +   url
                        print (backurl)
                        if url != '':
                            return redirect(url)
                        
            # if 'A' in request.POST:
            #     print('Ticket A')
            # if 'B' in request.POST:
            #     print('Ticket B')
            # if 'C' in request.POST:
            #     print('Ticket C')
    else:
        messages.error(request, error)
    context = {
        'touchkeylist':touchkeylist,
        'logofile':logofile,
        'errormsg':error,
        }        
    return render(request, 'base/webtouch.html', context)

def CancelTicketView(request, pk, sc):
    error = ''
    logofile = ''
    url = ''
    backurl = ''

    print('pk:' + pk)
    print('sc:' + sc)
    
    try:
        tt = TicketTemp.objects.get(id=pk)
        logofile = tt.branch.webtvlogolink

        # back to : http://127.0.0.1:8000/my/?tt=A&no=003&bc=KB&sc=vVL
        base_url = reverse('myticket')
        query_string =  urlencode({
                                    'tt':tt.tickettype , 
                                    'no':tt.ticketnumber, 
                                    'bc':tt.branch.bcode, 
                                    'sc':tt.securitycode,
                                    }) 
        url = '{}?{}'.format(base_url, query_string)  # 3 ip/my/?tt=A&no=003&bc=KB&sc=vVL
        backurl = '{0}://{1}'.format(request.scheme, request.get_host()) + url
        print (backurl)
    except:
        error = 'Ticket not found.'

    if error == '' :
        if tt.securitycode != sc :
            error = 'Ticket not found. (security code)'
    if error == '' :
        if request.method =='POST':
            # process cancel ticket (void)
            print('tapped CONFIRM')

            user = userweb
            
            tdobj = TicketData.objects.filter(tickettemp=tt)
            if tdobj.count() == 1 :
                td = tdobj[0]
            else:
                error = 'TicketData not found.'

            if error == '' :
                if tt.status != 'waiting':
                    error = 'Status is not correct.'

            if error == '' :  
                datetime_now =timezone.now()
                funVoid(user, tt, td, datetime_now)

                # add ticketlog
                TicketLog.objects.create(
                    tickettemp=tt,
                    logtime=datetime_now,
                    app = 'Web',
                    version = '8',
                    logtext='Ticket Void by web : '  + tt.branch.bcode + '_' + tt.tickettype + '_'+ tt.ticketnumber + '_' + datetime_now.strftime('%Y-%m-%dT%H:%M:%S.%fZ') ,
                    user=user,
                )


                return redirect(url)
    if error != '' :
        print (error)
        messages.error(request, error)
        if url != '':
            return redirect(url)

    context = {
    'logofile':logofile,
    'errormsg':error,
    'backurl':backurl,
    }
    return render(request, 'base/webmyticket_cancel.html', context)

def webmyticket_old_school(request):
    # 127.0.0.1:8000/my?tt=A&no=001&bc=KB&sc=123
    context = None
    error = ''
    bcode = ''
    try:
        bcode = request.GET['bc']
    except:
        bcode = ''
        error = 'Branch code is blank.'

    ttype = ''
    tno = ''
    try:
        ttype = request.GET['tt']
        ticket = ttype + tno
    except:
        ttype = ''
        error = 'Ticket type is blank.'  
    try:
        tno = request.GET['no']
        ticket = ttype + tno
    except:
        tno = ''
        error = 'Ticket number is blank.'  

    securitycode = ''
    try:
        securitycode = request.GET['sc']
    except:
        securitycode = ''
        error = 'Security code is blank.'  

    branch = None
    logofile = None
    datetime_now_local = None
    if error == '' :        
        branchobj = Branch.objects.filter( Q(bcode=bcode) )
        if branchobj.count() == 1:
            branch = branchobj[0]
            logofile = branch.webtvlogolink
            datetime_now = timezone.now()
            datetime_now_local = funUTCtoLocal(datetime_now, branch.timezone)
        else :
            error = 'Branch not found.'
    
    countertype = None
    if error == '' :        
        ttobj = TicketTemp.objects.filter(  
                                            Q(branch=branch) & 
                                            Q(tickettype=ttype) &
                                            Q(ticketnumber=tno) & 
                                            Q(securitycode=securitycode)
                                            )
        if ttobj.count() == 1:
            tickettemp = ttobj[0]

            tickettime = tickettemp.tickettime
            counterstatus = tickettemp.status
            countertype = tickettemp.countertype

            tickettime = funUTCtoLocal(tickettime, branch.timezone)
        else :
            error = 'Ticket not found.'
    
    displaylist = None 
    if error == '' :
        displaylist = DisplayAndVoice.objects.filter (branch=branch, countertype=countertype).order_by('-displaytime')[:5]
    
    counter='---'
    if error == '':
        csobj = CounterStatus.objects.filter(
            Q(tickettemp = tickettemp)
        )
        if csobj.count() == 1:
            counter = csobj[0].counternumber
    if error == '':
        context = {
            'ticket':ticket,
            'tickettime':tickettime.strftime('%Y-%m-%d %H:%M:%S'),
            'counterstatus':counterstatus,
            'logofile':logofile,
            'lastupdate':datetime_now_local.strftime('%Y-%m-%d %H:%M:%S'),            
            'counter':counter,
            'countertype':countertype,
            'tickettemp':tickettemp,
            'ticketlist':displaylist,
            'errormsg':'',
            }
    else:
        context = {
            'logofile':logofile,
            'errormsg':error,
            }
        messages.error(request, error)
    return render(request , 'base/webmyticketold2.html', context)


def webtv_old_school(request):
    
    context = None
    error = ''
    bcode = ''
    try:
        bcode = request.GET['bcode']
    except:
        bcode = ''
        error = 'Branch code is blank.'

    countertypename = ''
    try:
        countertypename = request.GET['ct']
    except:
        countertypename = ''
    
    
    branch = None
    if error == '' :        
        branchobj = Branch.objects.filter( Q(bcode=bcode) )
        if branchobj.count() == 1:
            branch = branchobj[0]
            logofile = branch.webtvlogolink
        else :
            error = 'Branch not found.'

    # get the Counter type
    countertype = None
    if error == '' :    
        if countertypename == '' :
            ctypeobj = CounterType.objects.filter( Q(branch=branch) )
        else:
            ctypeobj = CounterType.objects.filter( Q(branch=branch) & Q(name=countertypename) )
        if (ctypeobj.count() > 0) :
            countertype = ctypeobj[0]
        else :
            error = 'Counter Type not found.' 



    if error == '' : 
        if countertype == None :
            displaylist = DisplayAndVoice.objects.filter (branch=branch).order_by('-displaytime')[:5]
        else:
            displaylist = DisplayAndVoice.objects.filter (branch=branch, countertype=countertype).order_by('-displaytime')[:5]
        # serializers  = webdisplaylistSerivalizer(displaylist, many=True)
        # context = ({'ticketlist':serializers.data})

        datetime_now = timezone.now()
        datetime_now_local = funUTCtoLocal(datetime_now, branch.timezone)

        context = {
        'lastupdate':datetime_now_local.strftime('%Y-%m-%d %H:%M:%S'),
        'ticketlist':displaylist,
        'logofile':logofile,
        }
    else :
        context = {
        'lastupdate' : 'Error: ' + error + ' ',
        'errormsg' : error,
        }
        messages.error(request, error)
    return render(request , 'base/webtvold3.html', context)


def disptvView(request):
    return render(request, 'base/webtv.html')

@unauth_user
@allowed_users(allowed_roles=['admin', 'report'])
def Report_RAW_Result(request):
    bcode = request.GET['branch']
    s_startdate = request.GET['startdate']
    s_enddate = request.GET['enddate']
    countertype_id = request.GET['countertype']

    error = ''

    if error == '':
        try:
            branch = Branch.objects.get(bcode=bcode)
        except:
            error = 'Error : Branch not found.'
    
    countertype = None            
    if error == '':
        if countertype_id == '':
            # error = 'Error : Counter Type is blank.'
            pass
        else:
            try:
                countertype = CounterType.objects.get(id=int(countertype_id))
            except:
                error = 'Error : Counter Type not found.'
             
    if error == '':
        try:
            startdate = datetime.strptime(s_startdate, '%Y-%m-%dT%H:%M:%S')
            startdate = funLocaltoUTC(startdate, branch.timezone)
        except:
            try: 
                startdate = datetime.strptime(s_startdate + ':00', '%Y-%m-%dT%H:%M:%S')
                startdate = funLocaltoUTC(startdate, branch.timezone) 
            except:
                error = 'Error : Start Datetime not found.'

    if error == '':
        try:
            enddate = datetime.strptime(s_enddate, '%Y-%m-%dT%H:%M:%S')
            enddate = funLocaltoUTC(enddate, branch.timezone)
        except:
            try:
                enddate = datetime.strptime(s_enddate + ':00', '%Y-%m-%dT%H:%M:%S')
                enddate = funLocaltoUTC(enddate, branch.timezone)
            except:
                error = 'Error : End Datetime not found.'

    
    if error == '':
        if startdate > enddate :
            error = 'Error : Start Datetime > End Datetime.'

    table = None
    if error == '':
        localtimezone = pytz.timezone(branch.timezone)
        if countertype == None  :
            table = TicketData.objects.filter(
                Q(branch=branch),
                Q(starttime__range=[startdate,enddate]),
                ~Q(ticket = None),
            )
            report_result = 'RAW Data Report  Branch:' + branch.name + '(' + branch.bcode + ') Start datetime:' + s_startdate + ' End datetime:' + s_enddate + ' Counter Type:ALL'
        else:
            table = TicketData.objects.filter(
                Q(branch=branch),
                Q(starttime__range=[startdate,enddate]),
                ~Q(ticket = None),
                Q(countertype=countertype),
            )        
            report_result = 'RAW Data Report  Branch:' + branch.name + '(' + branch.bcode + ') Start datetime:' + s_startdate + ' End datetime:' + s_enddate + ' Counter Type:' + countertype.name


    if error == '':
        context = {
        'localtimezone':localtimezone,
        'result':report_result,
        'table':table,        
        }
    else:
        context = {
        'result':error,
        }

    return render(request, 'base/r-raw.html', context)
    
@unauth_user
@allowed_users(allowed_roles=['admin', 'report'])
def Report_RAW_q(request):
    
    users = User.objects.exclude( Q(is_superuser=True) | Q(groups__name='api'))
    branchs = Branch.objects.all()
    ticketformats = TicketFormat.objects.all().order_by('branch','ttype')
    routes = TicketRoute.objects.all().order_by('branch','tickettype','step')
    countertypes = CounterType.objects.all()

    now_l = datetime.now()
    snow_l = now_l.strftime('%Y-%m-%dT%H:%M:%S')

    context = {
    'now':snow_l,
    'users':users,
    'branchs':branchs,  
    'ticketformats':ticketformats, 
    'routes':routes,
    'countertypes':countertypes,
    }
    return render(request, 'base/r-rawq.html', context)

@unauth_user
@allowed_users(allowed_roles=['admin', 'report'])
def SuperVisorView(request, pk):

    branch = Branch.objects.get(id=pk)    
    countertypes = CounterType.objects.filter(Q(branch=branch))
    
    qlists = [[],[]]    
    counterstatus =[[],[]] 
    for ct in countertypes :
        t = TicketTemp.objects.filter( Q(branch=branch) & Q(locked=False) & Q(status='waiting') & Q(countertype=ct))
        qlists.append(t)

        cs = CounterStatus.objects.filter(Q(countertype=ct)).order_by('countertype', 'counternumber',)
        counterstatus.append(cs)
        
    # qlists[0] = Ticket.objects.filter( Q(branch=branch) & Q(locked=False) & Q(status='waiting') & Q(countertype=countertypes[0]))
    # qlists[1] = Ticket.objects.filter( Q(branch=branch) & Q(locked=False) & Q(status='waiting') & Q(countertype=countertypes[1]))
    localtimezone = pytz.timezone(branch.timezone)

    donelist = TicketTemp.objects.filter( Q(branch=branch) & Q(locked=False) & Q(status='done'))
    
    misslist = TicketTemp.objects.filter( Q(branch=branch) & Q(locked=False) & (Q(status='miss') | Q(status='void'))  )

    printerstatuslist = PrinterStatus.objects.filter(Q(branch=branch))

    now = datetime.utcnow()
    # snow = now.strftime('%H:%M:%S %Y-%m-%d')

    context = {
    'now':now,
    'localtimezone':localtimezone,
    'branch':branch,
    'qlist':qlists,  
    'counterstatus':counterstatus,
    'donelist':donelist,
    'misslist':misslist,
    'printerstatuslist':printerstatuslist,
    }

    return render(request, 'base/supervisor.html', context)


@unauth_user
@allowed_users(allowed_roles=['admin', 'report'])
def SuperVisorListView(request):  
    
    users = User.objects.exclude( Q(is_superuser=True) | Q(groups__name='api'))
    #users = User.objects.exclude( Q(is_superuser=True) )
    profiles = UserProfile.objects.all()
    branchs = Branch.objects.all()    
    ticketformats = TicketFormat.objects.all()
    routes = TicketRoute.objects.all()
    # profiles = UserProfile.objects.filter(Q(user=users.user))
    #profiles = users.userprofile_set.all()
    
    context = {'users':users, 'profiles':profiles, 'branchs':branchs, 'ticketformats':ticketformats, 'routes':routes}
    return render(request, 'base/supervisors.html', context)

@unauth_user
@allowed_users(allowed_roles=['admin'])
def TicketRouteNewView(request):
    #page = 'register'
    form = trForm()
    if request.method == 'POST':
        form = trForm(request.POST)
        if form.is_valid():
            newroute = form.save(commit=False)
            newroute.tickettype  = newroute.tickettype.upper()

            try:
                newroute.save()
                messages.success(request, 'Created new Ticket Route.')
            except:
                messages.error(request,' An error occurcd during registration: ' )
                   
            
            return redirect('routesummary')
        else:
            messages.error(request,' An error occurcd during registration: '+ str(form.errors) )
    #context = {'page':page}
    return render(request, 'base/routenew.html', {'form':form})

@unauth_user
@allowed_users(allowed_roles=['admin'])
def TicketRouteDelView(request, pk):
 
    route = TicketRoute.objects.get(id=pk)
  
    if request.method =='POST':
        route.delete()
        messages.success(request, 'Ticket Route was successfully Deleted!')
        return redirect('routesummary')    
    return render(request, 'base/delete.html', {'obj':route})

@unauth_user
@allowed_users(allowed_roles=['admin'])
def TicketRouteUpdateView(request, pk):
    route = TicketRoute.objects.get(id=pk)    
    if request.method == 'POST':
    
        trform = trForm(request.POST, instance=route, prefix='trform')
          
                
        if trform.is_valid():  
            new = trform.save(commit=False)          
            new.tickettype  = new.tickettype.upper()
            new.save()
            messages.success(request, 'Ticket Route was successfully changed!')
            return redirect('routesummary')
    else:
        trform = trForm(instance=route, prefix='trform')
       
    context =  {'route':route, 'trform':trform }
    return render(request, 'base/route-update.html', context)


@unauth_user
@allowed_users(allowed_roles=['admin'])
def TicketRouteSummaryView(request):  
    users = User.objects.exclude( Q(is_superuser=True) | Q(groups__name='api'))
    branchs = Branch.objects.all()
    ticketformats = TicketFormat.objects.all().order_by('branch','ttype')
    routes = TicketRoute.objects.all().order_by('branch','tickettype','step')

    context = {'users':users, 'branchs':branchs, 'ticketformats':ticketformats, 'routes':routes}

    return render(request, 'base/routes.html', context)

@unauth_user
@allowed_users(allowed_roles=['admin'])
def TicketFormatNewView(request):
    #page = 'register'
    form = TicketFormatForm()
    if request.method == 'POST':
        form = TicketFormatForm(request.POST)
        if form.is_valid():
            tf = form.save(commit=False)
            tf.ttype = tf.ttype.upper()

            try:
                tf.save()
            except:
                messages.error(request,' An error occurcd during registration: ' )
                   
            
            return redirect('tfsummary')
        else:
            messages.error(request,' An error occurcd during registration: '+ str(form.errors) )
    #context = {'page':page}
    return render(request, 'base/tfnew.html', {'form':form})

@unauth_user
@allowed_users(allowed_roles=['admin'])
def TicketFormatDelView(request, pk):
 
    ticketformat = TicketFormat.objects.get(id=pk)
  
    if request.method =='POST':
        ticketformat.delete()       
        messages.success(request, 'Ticket Format was successfully deleted!') 
        return redirect('tfsummary')    
    return render(request, 'base/delete.html', {'obj':ticketformat})

@unauth_user
@allowed_users(allowed_roles=['admin'])
def TicketFormatUpdateView(request, pk):
    ticketformat = TicketFormat.objects.get(id=pk)    
    if request.method == 'POST':
    
        tfform = TicketFormatForm(request.POST, instance=ticketformat, prefix='tfform')
        
        
        if  (tfform.is_valid()):
            tfform.save()
            messages.success(request, 'Ticket Format was successfully updated!')        
            return redirect('tfsummary')
    else:
        tfform = TicketFormatForm(instance=ticketformat, prefix='tfform')        
    context =  {'tfform':tfform, 'ticketformat':ticketformat, }
    return render(request, 'base/tf-update.html', context)

@unauth_user
@allowed_users(allowed_roles=['admin'])
def TicketFormatSummaryView(request):  
    users = User.objects.exclude( Q(is_superuser=True) | Q(groups__name='api'))
    branchs = Branch.objects.all()
    ticketformats = TicketFormat.objects.all().order_by('branch','ttype')
    routes = TicketRoute.objects.all()
    context = {'users':users, 'branchs':branchs, 'ticketformats':ticketformats, 'routes':routes}
    return render(request, 'base/tfs.html', context)

@unauth_user
@allowed_users(allowed_roles=['admin'])
def Branch_Save(request, pk):
    branch = Branch.objects.get(id=pk) 
    result = ''

    
    s_branchenabled = 'off'
    try:
        s_branchenabled = request.GET['branchenabled']
    except:
        s_branchenabled = 'off'
    if s_branchenabled == 'on':
        new_branchenabled = True
    else:
        new_branchenabled = False



    # check input data
    new_branchname = request.GET['branchname']    
    if new_branchname == '' :
        result = 'Input error : Branch name is blank.'
    
    new_address = request.GET['address']
    new_gps = request.GET['gps']

    new_timezone = request.GET['timezone']
    if new_timezone == '' :
        result = 'Input error : Timezone is blank.'
    if result == '' :
        try:
            local_zone = pytz.timezone(new_timezone)              
        except:
            result = 'Input error : Timezone not correct. Please check the Timezone '

    new_officehourstart = request.GET['officehourstart']
    if new_officehourstart == '' :
        result = 'Input error : Office Hour start time is blank.'
    if result == '' :
        try :        
            new_officehourstart = datetime.strptime(new_officehourstart, '%H:%M:%S' )        
            u_officehourstart = funLocaltoUTCtime(new_officehourstart, new_timezone)
        except:
            result = 'Input error : Office Hour start time'            

    new_officehourend = request.GET['officehourend']
    if new_officehourend == '' :
        result = 'Input error : Office Hour end time is blank.'
    if result == '' :
        try :            
            new_officehourend = datetime.strptime(new_officehourend, '%H:%M:%S' )
            u_officehourend = funLocaltoUTCtime(new_officehourend, new_timezone)
        except:
            result = 'Input error : Office Hour end time'

    new_tickettimestart = request.GET['tickettimestart']
    if new_tickettimestart == '' :
        result = 'Input error : Ticket start time is blank.'
    if result == '' :
        try :            
            new_tickettimestart = datetime.strptime(new_tickettimestart, '%H:%M:%S' )
            u_tickettimestart = funLocaltoUTCtime(new_tickettimestart, new_timezone)
        except:
            result = 'Input error : Ticket start time'

    new_tickettimeend = request.GET['tickettimeend']
    if new_tickettimeend == '' :
        result = 'Input error : Ticket end time is blank.'
    if result == '' :
        try :            
            new_tickettimeend = datetime.strptime(new_tickettimeend, '%H:%M:%S' )
            u_tickettimeend = funLocaltoUTCtime(new_tickettimeend, new_timezone)
        except:
            result = 'Input error : Ticket end time'
    
    new_queuepriority = request.GET['queuepriority']
    if new_queuepriority == '' :
         result = 'Input error : Queue priority is blank.'

    new_queuemask = request.GET['queuemask']
    new_queuemask = new_queuemask.upper()
    new_queuemask = new_queuemask.replace(' ', '')
    if new_queuemask == '' :
         result = 'Input error : Queue mask is blank.'    

    new_ticketmax = request.GET['ticketmax']
    if new_ticketmax == '' :
        result = 'Input error : Ticket Max. number is blank.'
    if result == '' :
        try:
            new_ticketmax = int(new_ticketmax)
        except:
            result = 'Input error : Ticket Max. number should be integer.'
    if result == '' :            
        if 0 < new_ticketmax  :
            pass
        else:
            result = 'Input error : Ticket Max. number should be larger then 0.'
    
    new_ticketnoformat = request.GET['ticketnoformat']
    if new_ticketnoformat == '' :
         result = 'Input error : Ticket number format is blank.'
    if result == '' :
        for c in new_ticketnoformat:
            if c != '0':
                result = 'Input error : Ticket number format should be "0".'
                break

    s_ticketrepeatnumber = 'off'
    try:
        s_ticketrepeatnumber = request.GET['ticketrepeatnumber']
    except:
        s_ticketrepeatnumber = 'off'   
    if s_ticketrepeatnumber == 'on':
        new_ticketrepeatnumber = True
    else:
        new_ticketrepeatnumber  = False

    s_displayenabled = 'off'
    try:
        s_displayenabled = request.GET['displayenabled']
    except:
        s_displayenabled = 'off'   
    if s_displayenabled == 'on':
        new_displayenabled = True
    else:
        new_displayenabled  = False

    new_displayflashtime = request.GET['displayflashtime']
    if new_displayflashtime == '' :
         result = 'Input error : Display flash time is blank.'
    if result == '' :
        try :
            new_displayflashtime = int(new_displayflashtime)
        except:
            result = 'Input error : Display flash time should be integer.'
    if result == '' :        
        if 0 < new_displayflashtime and new_displayflashtime <= 50 :
            pass
        else:
            result = 'Input error : Display flash time should be 1-50.'

    s_voiceenabled = 'off'
    try:
        s_voiceenabled = request.GET['voiceenabled']
    except:
        s_voiceenabled = 'off'   
    if s_voiceenabled == 'on':
        new_voiceenabled = True
    else:
        new_voiceenabled  = False       

    new_language1 = request.GET['language1']
    if new_language1 == '' :
         result = 'Input error : Language 1 is blank.'
    if result == '' :
        try:
            new_language1 = int(new_language1)
        except:
            result = 'Input error : Language 1 should be integer.'
    if result == '' :
        if -1 < new_language1 and new_language1 <= 4 :
            pass
        else:
            result = 'Input error : Language 1 should be 0-4.'

    new_language2 = request.GET['language2']
    if new_language2 == '' :
         result = 'Input error : Language 2 is blank.'
    if result == '' :
        try:
            new_language2 = int(new_language2)
        except:
            result = 'Input error : Language 2 should be integer.'
    if result == '' :
        if -1 < new_language2 and new_language2 <= 4 :
            pass
        else:
            result = 'Input error : Language 2 should be 0-4.'

    new_language3 = request.GET['language3']
    if new_language3 == '' :
         result = 'Input error : Language 3 is blank.'
    if result == '' :
        try:
            new_language3 = int(new_language3)
        except:
            result = 'Input error : Language 3 should be integer.'
    if result == '' :
        if -1 < new_language3 and new_language3 <= 4 :
            pass
        else:
            result = 'Input error : Language 3 should be 0-4.'

    new_language4 = request.GET['language4']
    if new_language4 == '' :
         result = 'Input error : Language 4 is blank.'
    if result == '' :
        try:
            new_language4 = int(new_language4)
        except:
            result = 'Input error : Language 4 should be integer.'
    if result == '' :
        if -1 < new_language4 and new_language4 <= 4 :
            pass
        else:
            result = 'Input error : Language 4 should be 0-4.'

    s_usersinglelogin = 'off'
    try:
        s_usersinglelogin = request.GET['usersinglelogin']
    except:
        s_usersinglelogin = 'off'   
    if s_usersinglelogin == 'on':
        new_usersinglelogin = True
    else:
        new_usersinglelogin  = False    



    if result == '' :
        branch.enabled = new_branchenabled
        branch.name = new_branchname
        branch.address = new_address
        branch.gps = new_gps
        branch.timezone = new_timezone
        branch.officehourstart = u_officehourstart
        branch.officehourend = u_officehourend
        branch.tickettimestart = u_tickettimestart
        branch.tickettimeend = u_tickettimeend
        branch.queuepriority = new_queuepriority
        branch.queuemask = new_queuemask
        branch.ticketmax = new_ticketmax
        branch.ticketnoformat = new_ticketnoformat
        branch.ticketrepeatnumber = new_ticketrepeatnumber 
        branch.displayenabled = new_displayenabled
        branch.displayflashtime = new_displayflashtime
        branch.voiceenabled = new_voiceenabled
        branch.language1 = new_language1
        branch.language2 = new_language2
        branch.language3 = new_language3
        branch.language4 = new_language4
        branch.usersinglelogin = new_usersinglelogin

    if result == '' :
        branch.save()

        countertypes = CounterType.objects.filter(Q(branch=branch))
        for ct in countertypes:
            ct.displayscrollingtext = request.GET[branch.bcode + '-' + ct.name]
            ct.save()
        messages.success(request, 'Branch settings was successfully changed!')
        result = ''
    else :
        messages.error(request, result)
    
    # context = {'result':result}
    return redirect('branchsummary')
    # return render(request, 'base/branchresult.html', context)

@unauth_user
@allowed_users(allowed_roles=['admin'])
def BranchUpdateView(request, pk):
    branch = Branch.objects.get(id=pk)

    branchcode = branch.bcode
    branchname = branch.name
    branchenabled = branch.enabled

    timezone = branch.timezone

    officehourstart = branch.officehourstart
    l_officehourstart = funUTCtoLocaltime(officehourstart, timezone)
    sofficehourstart =  l_officehourstart.strftime('%H:%M:%S')

    officehourend = branch.officehourend
    l_officehourend = funUTCtoLocaltime(officehourend, timezone)
    sofficehourend =  l_officehourend.strftime('%H:%M:%S')

    tickettimestart = branch.tickettimestart
    l_tickettimestart = funUTCtoLocaltime(tickettimestart, timezone)
    stickettimestart =  l_tickettimestart.strftime('%H:%M:%S')
    tickettimeend = branch.tickettimeend
    l_tickettimeend = funUTCtoLocaltime(tickettimeend, timezone)
    stickettimeend =  l_tickettimeend.strftime('%H:%M:%S')

    queuepriority = branch.queuepriority

    countertypes = CounterType.objects.filter(Q(branch=branch))

    context = {
    'branch':branch,
    'branchcode':branchcode, 'branchname':branchname, 'branchenabled':branchenabled,
    'timezone':timezone, 
    'officehourstart':sofficehourstart, 'officehourend':sofficehourend,
    'tickettimestart':stickettimestart, 'tickettimeend':stickettimeend,
    'queuepriority':queuepriority,
    'countertypes':countertypes,
    }

    return render(request, 'base/branch-update.html', context)

@unauth_user
@allowed_users(allowed_roles=['admin'])
def BranchSummaryView(request):  
    users = User.objects.exclude( Q(is_superuser=True) | Q(groups__name='api'))
    #users = User.objects.exclude( Q(is_superuser=True) )
    profiles = UserProfile.objects.all()
    branchs = Branch.objects.all()    
    ticketformats = TicketFormat.objects.all()
    routes = TicketRoute.objects.all()
    # profiles = UserProfile.objects.filter(Q(user=users.user))
    #profiles = users.userprofile_set.all()
    
    context = {'users':users, 'profiles':profiles, 'branchs':branchs, 'ticketformats':ticketformats, 'routes':routes}
    return render(request, 'base/branch.html', context)

@unauth_user
def homeView(request):  
    users = User.objects.exclude( Q(is_superuser=True) | Q(groups__name='api'))
    branchs = Branch.objects.all()
    ticketformats = TicketFormat.objects.all()
    routes = TicketRoute.objects.all()
    # users = User.objects.exclude(is_superuser=True)
    context =  {'users':users , 'branchs':branchs, 'ticketformats':ticketformats, 'routes':routes}
    return render(request, 'base/home.html', context)

@unauth_user
@allowed_users(allowed_roles=['admin'])
def UserSummaryView(request):  
    users = User.objects.exclude( Q(is_superuser=True) | Q(groups__name='api'))
    #users = User.objects.exclude( Q(is_superuser=True) )
    profiles = UserProfile.objects.all()
    branchs = Branch.objects.all()
    ticketformats = TicketFormat.objects.all()
    routes = TicketRoute.objects.all()
    # profiles = UserProfile.objects.filter(Q(user=users.user))
    #profiles = users.userprofile_set.all()
    
    context = {'users':users, 'profiles':profiles, 'branchs':branchs, 'ticketformats':ticketformats, 'routes':routes}
    return render(request, 'base/user.html', context)

def UserLogoutView(request):   
    logout(request)
    return redirect('login')

@unauth_user_login
def UserLoginView(request):
    page = 'login'
    # if request.user.is_authenticated:
    #     return redirect('home')

    if request.method == 'POST':
        username = request.POST.get('username').lower()
        password = request.POST.get('password')
        human = True

        captchaform = CaptchaForm(request.POST)
        if captchaform.is_valid():
            human = True
            # print ('Is human.')
        else:
            # print('Is NOT human.')
            messages.error(request, 'User is NOT human.')
            return redirect('home')
        
        if human == True:
            try:
                user = User.objects.get(username=username)
            except:
                messages.error(request, 'User does not exist')

            user =  authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('home')
            else:
                messages.error(request, 'Username or password does not exist')
    else:
        captchaform = CaptchaForm()
        pass

    context = {'page':page} 
    context = context | {'captcha_form':captchaform} 
    return render(request, 'base/login_register.html', context)

@unauth_user
@allowed_users(allowed_roles=['admin'])
def UserUpdateView(request, pk):
    user = User.objects.get(id=pk)
    userp =UserProfile.objects.get(user__exact=user)
    if request.method == 'POST':
    
        userform = UserForm(request.POST, instance=user, prefix='uform')
        if user == request.user:
            userform = UserFormAdmin(request.POST, instance=user, prefix='uform')        
            
        profileform = UserProfileForm(request.POST, instance=userp, prefix='pform')
        
        if  (userform.is_valid() & profileform.is_valid()):
            userform.save()
            profileform.save()
            profileform_temp = profileform.save(commit=False)
            profileform_temp.tickettype = profileform_temp.tickettype.upper()
            profileform_temp.save()
            # profileform_temp = profileform.save(commit=False)
            # profileform_temp.tickettype = profileform_temp.tickettype.upper()
            # profileform_temp.branchs = profileform.branchs
            
            # profileform_temp.save()
            messages.success(request, 'Profile was successfully updated!')
            return redirect('usersummary')
    else:
        userform = UserForm(instance=user, prefix='uform')
        if user == request.user:
            userform = UserFormAdmin(instance=user, prefix='uform')  
        profileform = UserProfileForm(instance=userp, prefix='pform')
    context =  {'userform':userform , 'profileform':profileform, 'user':user}
    return render(request, 'base/user-update.html', context)

@unauth_user
@allowed_users(allowed_roles=['admin'])
def UserNewView(request):
    #page = 'register'
    form = UserCreationForm()
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.username = user.username.lower()
            user.save()
            # new userprofile for this user
            #newuser = user.user
            UserProfile.objects.create(user=user)
                   
            #login(request, user)
            return redirect('usersummary')
        else:
            messages.error(request, 'An error occurcd during registration')
    #context = {'page':page}
    return render(request, 'base/usernew.html', {'form':form})

@unauth_user
# @allowed_users(allowed_roles=['admin'])
def UserChangePWView(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # Important!
            messages.success(request, 'Your password was successfully updated!')
            logout(request)
            return redirect('login')
        else:
            messages.error(request, 'Please correct the error below.')
    else:
        form = PasswordChangeForm(request.user)
    return render(request, 'base/changepassword.html', {'form': form})

@unauth_user
@allowed_users(allowed_roles=['admin'])
def UserDelView(request, pk):
 
    user = User.objects.get(id=pk)
    userp =UserProfile.objects.get(user__exact=user)

    if request.user == user :
        #  return HttpResponse('You can not kill yourself!')
        messages.error(request, 'You can not kill yourself!')
        return redirect('usersummary')   

    if request.method =='POST':
        userp.delete()
        user.delete()
        messages.success(request, 'User successfully deleted.')
        return redirect('usersummary')    
    return render(request, 'base/delete.html', {'obj':user})

def MenuView(request):

    users = User.objects.exclude( Q(is_superuser=True) | Q(groups__name='api'))
    branchs = Branch.objects.all()
    ticketformats = TicketFormat.objects.all().order_by('branch','ttype')
    routes = TicketRoute.objects.all()
    
    adminuser = '0'
    reportuser = '0'
    for group in request.user.groups.all() :
        if group.name == 'admin':
            adminuser = '1'
            reportuser = '1'
        elif group.name == 'report':
            reportuser = '1'
    if request.user.is_superuser :
        adminuser = '1'
        reportuser = '1'

    context = {'users':users, 'branchs':branchs, 'ticketformats':ticketformats, 'routes':routes, 'admin':adminuser, 'report':reportuser}
    return render (request, 'base/m-menu.html', context)