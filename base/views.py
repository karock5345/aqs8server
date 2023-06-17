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
from .forms import TicketFormatForm, UserForm, UserFormAdmin, UserProfileForm,trForm, CaptchaForm, getForm, voidForm, newTicketTypeForm, UserFormSuper
from .api.views import funUTCtoLocal, funLocaltoUTC, funUTCtoLocaltime, funLocaltoUTCtime
from django.utils.timezone import localtime, get_current_timezone
import pytz
from .api.serializers import displaylistSerivalizer, waitinglistSerivalizer
from django.utils import timezone
# from .api.v_softkey import funVoid
from .api.v_softkey_sub import *
from .api.v_touch import newticket
from base.ws import wsHypertext, wscounterstatus, wssendflashlight


from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
import logging

logger = logging.getLogger(__name__)

enable_captcha = False

userweb = None
try:
    userweb = User.objects.get(username='userweb')
except:
    logger.error('userweb not found.')
    

context_login = {}

@unauth_user
def Softkey_VoidView(request, pk, ttid):
    context = {}
    datetime_now =timezone.now()
    try:
        tt = TicketTemp.objects.get(id=ttid)
        datetime_now_local = funUTCtoLocal(datetime_now, tt.branch.timezone)
        str_now = datetime_now_local.strftime('%Y-%m-%d %H:%M:%S')
    except:
        messages.error(request, 'TicketTemp not found.')
        return redirect('softkey', pk=pk)
    try:
        td = TicketData.objects.get(Q(tickettemp=tt))
    except:
        messages.error(request, 'TicketData not found.')
        return redirect('softkey', pk=pk)
    context = {'tt':tt}
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'confirm':           
            funVoid(request.user, tt, td, datetime_now)
            messages.success(request, 'Ticket ' + tt.tickettype + tt.ticketnumber + ' has been voided.')
            return redirect('softkey', pk=pk)
    return render(request , 'base/softkey_void.html', context)
    


@unauth_user
def SoftkeyView(request, pk):
    context = {}
    context_counter = {}
    error = ''
    str_now = '--:--'
    datetime_now =timezone.now()

    auth_branchs , auth_userlist, auth_profilelist, auth_ticketformats , auth_routes, auth_countertype = auth_data(request.user)
    context = {
    'users':auth_userlist, 'branchs':auth_branchs, 'ticketformats':auth_ticketformats, 'routes':auth_routes
    }

    try:
        counterstatus = CounterStatus.objects.get(id=pk)
        datetime_now_local = funUTCtoLocal(datetime_now, counterstatus.countertype.branch.timezone)
        str_now = datetime_now_local.strftime('%Y-%m-%d %H:%M:%S')
  
    except:
        error = 'CounterStatus not found.'
    if counterstatus == None:
        error = 'CounterStatus not found.'

    if error == '':
        status, msg, context_counter = funCounterLogin(datetime_now, request.user, counterstatus.countertype.branch, counterstatus, counterstatus.counternumber, counterstatus.countertype)
        if status['status'] == 'Error':
            error = msg['msg']
    if error == '':
        context_tr = []
        trobj = TicketRoute.objects.filter(Q(branch=counterstatus.countertype.branch) & Q(countertype=counterstatus.countertype) & Q(enabled=True) )
        for tr in trobj:

            lang1 = ''
            lang2 = ''
            ticketformat = None

            try :
                ticketformat = TicketFormat.objects.get(ttype=tr.tickettype , branch=counterstatus.countertype.branch, enabled=True)
                # lang1 = ticketformat.touchkey_lang1
                # lang2 = ticketformat.touchkey_lang2
            except:
                logger.warning( 'TicketFormat not found (in find TicketRoute.waiting). Branch is ' + str(counterstatus.countertype.branch) + ', TicketType is ' + tr.tickettype + ' TicketFormat maybe disabled/removed. Please disable TicketRoute : ' + str(tr))
            
            # dict add to list
            if ticketformat != None:
                lang1 = ticketformat.touchkey_lang1
                lang2 = ticketformat.touchkey_lang2

                userttype = False
                if context_counter['data']['userttype'].find(tr.tickettype + ',') != -1:
                    userttype = True
                newrow = {
                    'tickettype' : tr.tickettype,
                    'lang1' : lang1,
                    'lang2' : lang2,
                    'wait' : tr.waiting,
                    'userttype' : userttype,             
                }
                context_tr.append(newrow)

    if error == '':
        ticketlist = TicketTemp.objects.filter( Q(branch=counterstatus.countertype.branch) & Q(countertype=counterstatus.countertype) & Q(status=lcounterstatus[0]) & Q(locked=False))       
        serializers  = waitinglistSerivalizer(ticketlist, many=True)       
        context_ql = serializers.data
        # add new column to context_ql (tickettime_local)
        for i in range(len(context_ql)):
            # convert string context_ql[i]['tickettime'] to datetime
            try:                
                utctt = datetime.strptime(context_ql[i]['tickettime'], '%Y-%m-%dT%H:%M:%S.%fZ')
            except:
                utctt = datetime.strptime(context_ql[i]['tickettime'], '%Y-%m-%dT%H:%M:%SZ')

            context_ql[i]['tickettime_local'] = funUTCtoLocal(utctt, counterstatus.countertype.branch.timezone)
            context_ql[i]['tickettime_local'] = context_ql[i]['tickettime_local'].strftime('%H:%M:%S %Y-%m-%d')

    if error == '':
        printerobj = PrinterStatus.objects.filter(Q(branch=counterstatus.countertype.branch))

        if request.method == 'POST':
            action = request.POST.get('action')
            if action == 'submit':
                # add Get form to context
                getform = getForm(request.POST)
                getticket = getform['ticketnumber'].value()
                
                if error == '':
                    status, msg, context_get = funCounterGet(getticket, '', '', request.user, counterstatus.countertype.branch, counterstatus.countertype, counterstatus, 'Get ticket :', 'Softkey-web', softkey_version, datetime_now)
                    if status['status'] == 'Error':
                        messages.error(request, msg['msg'] + ' ' + getticket)
                    context = context | context_counter | {'pk':pk} | context_get
                else :
                    messages.error(request, error)
              
                return redirect('softkey', pk=pk)
                # return render(request, 'base/softkey.html', context)
            elif action == 'call':
                status, msg, context_call = funCounterCall(request.user, counterstatus.countertype.branch, counterstatus.countertype, counterstatus, 'Call ticket :', 'Softkey-web', softkey_version, datetime_now)
                if status['status'] == 'Error':
                    messages.error(request, msg['msg'])
                if status['status'] == 'OK' and context_call == {'data': {}} :
                    messages.success(request, 'No ticket to call.')
            elif action == 'recall':
                status, msg = funCounterRecall(request.user, counterstatus.countertype.branch, counterstatus.countertype, counterstatus, 'Recall ticket :', 'Softkey-web', softkey_version, datetime_now)
                if status['status'] == 'OK' :
                    messages.success(request, 'Recall ticket success.')
            elif action == 'process':
                status, msg = funCounterProcess(request.user, counterstatus.countertype.branch, counterstatus.countertype, counterstatus, 'Process ticket :', 'Softkey-web', softkey_version, datetime_now)
            elif action == 'done':
                status, msg = funCounterComplete(request.user, counterstatus.countertype.branch, counterstatus.countertype, counterstatus, 'Done ticket :', 'Softkey-web', softkey_version, datetime_now)
            elif action == 'miss':
                status, msg = funCounterMiss(request.user, counterstatus.countertype.branch, counterstatus.countertype, counterstatus, 'Miss ticket :', 'Softkey-web', softkey_version, datetime_now)
            # elif action == 'void':
            #     voidform = voidForm(request.POST)
            #     voidttype = voidform['tickettype'].value()
            #     voidtno = voidform['ticketnumber'].value()
            #     voidttime = voidform['tickettime'].value()
            #     try:
            #         tt = TicketTemp.objects.get(Q(branch=counterstatus.countertype.branch) & Q(countertype=counterstatus.countertype) & Q(tickettype=voidttype) & Q(ticketnumber=voidtno) & Q(tickettime=voidttime))
            #     except:
            #         messages.error(request, 'TicketTemp not found.')
            #         return redirect('softkey', pk=pk)
            #     try:
            #         td = TicketData.objects.get(Q(tickettemp=tt))
            #     except:
            #         messages.error(request, 'TicketData not found.')
            #         return redirect('softkey', pk=pk)
            #     # funVoid(request.user,tt, td, datetime_now)
            #     render(request, '')
            elif action == 'logout':
                status, msg= funCounterLogout(counterstatus, datetime_now)
                if status['status'] == 'Error':
                    messages.error(request, msg['msg'])
                else:
                    messages.success(request, 'Logout success.')
                    return redirect('softkeylogin', counterstatus.countertype.branch.id)
            elif action == 'ready':
                cc_ready(request.user, counterstatus.countertype.branch, counterstatus.countertype, counterstatus, 'Ready button passed', 'Softkey-web', softkey_version, datetime_now)
            elif action == 'busy':
                # call centre mode 
                status, msg = funCounterProcess(request.user, counterstatus.countertype.branch, counterstatus.countertype, counterstatus, 'Process ticket :', 'Softkey-web', softkey_version, datetime_now)
            elif action == 'aux':
                cc_aux(request.user, counterstatus.countertype.branch, counterstatus.countertype, counterstatus, 'AUX button passed', 'Softkey-web', softkey_version, datetime_now)
            elif action == 'acw':
                cc_acw(request.user, counterstatus.countertype.branch, counterstatus.countertype, counterstatus, 'ACW button passed', 'Softkey-web', softkey_version, datetime_now)
            elif action == 'cancel':
                status, msg = funCounterMiss(request.user, counterstatus.countertype.branch, counterstatus.countertype, counterstatus, 'Miss ticket :', 'Softkey-web', softkey_version, datetime_now)
            elif action == 'on':
                # websocket to flash light ON
                wssendflashlight(counterstatus.countertype.branch, counterstatus.countertype, counterstatus, 'on')
                pass
            elif action == 'off':
                # websocket to flash light OFF
                wssendflashlight(counterstatus.countertype.branch, counterstatus.countertype, counterstatus, 'off')
                pass
            elif action == 'flash':
                # websocket to flash light FLASH
                wssendflashlight(counterstatus.countertype.branch, counterstatus.countertype, counterstatus, 'flash')                            
                pass
            elif action == None :
                pass
            else:
                messages.error(request, 'Action not found:' + action)
            return redirect('softkey', pk=pk)
            # q: how to return to same page after post and do not refresh page
            # return render(request, 'base/softkey.html', context_login[pk] | context)
        context = context | {'lastupdate': str_now}
        context = context | context_counter 
        context = context | {'pk':pk}
        context = context | {'printerstatus': printerobj}
        context = context | {'wsh' : wsHypertext}
        context = context | {'subtotal' : context_tr}
        context = context | {'qlist' : context_ql}
        # context_login[pk] = context

        if counterstatus.countertype.countermode == 'normal':
            return render(request, 'base/softkey.html', context)
        else:
            return render(request, 'base/softkey_callcentre.html', context)
        # pass
    else:
        messages.error(request, error)
        # Redirect to last page
        return redirect('softkeylogin', counterstatus.countertype.branch.id)

@unauth_user
def SoftkeyLoginBranchView(request):
    error = ''
    context = {}

    auth_branchs , auth_userlist, auth_profilelist, auth_ticketformats , auth_routes, auth_countertype = auth_data(request.user)

    user = request.user
    # get user auth branchs
    userpobj = UserProfile.objects.filter(user=user)
    if userpobj.count() == 1 :
        userp = userpobj[0]
        # print (userp.user.username)
    else :
        error = 'UserProfile not find'
    if error == '':
        branchs = userp.branchs.all()
        counterstatus =[[],[]]        
        for branch in branchs :
            countertypes = CounterType.objects.filter(Q(branch=branch))
            for ct in countertypes :
                cs = CounterStatus.objects.filter(Q(countertype=ct)).order_by('countertype', 'counternumber',).exclude(enabled=False)
                counterstatus.append(cs)
        context = {
        'users':auth_userlist, 'branchs':auth_branchs, 'ticketformats':auth_ticketformats, 'routes':auth_routes,
        'counterstatus':counterstatus,
        }

        return render(request, 'base/softkey_lobby_branch.html', context)
    else :
        return HttpResponse(error)

@unauth_user
def SoftkeyLoginView(request, pk):
    error = ''
    context = {}

    auth_branchs , auth_userlist, auth_profilelist, auth_ticketformats , auth_routes, auth_countertype = auth_data(request.user)

    branch = Branch.objects.get(id=pk)

    user = request.user
    # get user auth branchs
    userpobj = UserProfile.objects.filter(user=user)
    if userpobj.count() == 1 :
        userp = userpobj[0]
        # print (userp.user.username)
    else :
        error = 'UserProfile not find'
    if error == '':

        # new version should select branch first then counter
        # branchs = userp.branchs.all()
        # counterstatus =[[],[]]        
        # for branch in branchs :
        #     countertypes = CounterType.objects.filter(Q(branch=branch))
        #     for ct in countertypes :
        #         cs = CounterStatus.objects.filter(Q(countertype=ct)).order_by('countertype', 'counternumber',).exclude(enabled=False)
        #         counterstatus.append(cs)


        # branchs = userp.branchs.all()
        counterstatus =[[],[]]        
        # for branch in branchs :
        countertypes = CounterType.objects.filter(Q(branch=branch))
        for ct in countertypes :
            cs = CounterStatus.objects.filter(Q(countertype=ct)).order_by('countertype', 'counternumber',).exclude(enabled=False)
            counterstatus.append(cs)




        context = {
        'users':auth_userlist, 'branchs':auth_branchs, 'ticketformats':auth_ticketformats, 'routes':auth_routes,
        'counterstatus':counterstatus,
        }

        return render(request, 'base/softkey_lobby.html', context)
    else :
        return HttpResponse(error)
  
@unauth_user
def SoftkeyLogoutView(request, pk):
    error = ''
    context = {}
    datetime_now =timezone.now()
    auth_branchs , auth_userlist, auth_profilelist, auth_ticketformats , auth_routes, auth_countertype = auth_data(request.user)
    context = {
        'users':auth_userlist, 'branchs':auth_branchs, 'ticketformats':auth_ticketformats, 'routes':auth_routes
        }
    try:
        counterstatus = CounterStatus.objects.get(id=pk)
    except:
        error = 'CounterStatus not found.'
    if counterstatus == None:
        error = 'CounterStatus not found.'

    if error == '':
        status, msg= funCounterLogout(counterstatus, datetime_now)
        if status['status'] == 'Error':
            error = msg['msg']

    if error == '':
        messages.success(request, 'Logout success.')
        return redirect('softkeylogin', counterstatus.countertype.branch.id)
        # pass
    else:
        messages.error(request, error)
        # Redirect to last page
        return redirect('home')
        pass 

@unauth_user
def SoftkeyCallView(request, pk):
    error = ''
    context = {}
    datetime_now =timezone.now()
    auth_branchs , auth_userlist, auth_profilelist, auth_ticketformats , auth_routes, auth_countertype = auth_data(request.user)
    context = {
        'users':auth_userlist, 'branchs':auth_branchs, 'ticketformats':auth_ticketformats, 'routes':auth_routes
        }
    try:
        counterstatus = CounterStatus.objects.get(id=pk)
    except:
        error = 'CounterStatus not found.'
    if counterstatus == None:
        error = 'CounterStatus not found.'

    if error == '':
        status, msg, context = funCounterCall(request.user, counterstatus.countertype.branch, counterstatus.countertype, counterstatus, 'Call ticket:', 'Softkey-web', softkey_version, datetime_now)
        if status['status'] == 'Error':
            error = msg['msg']

    if error == '':
        if context == {'data': {}} :
            messages.success(request, 'No ticket.')
    else:
        messages.error(request, error)
        # Redirect to last page
    return redirect('softkey', pk)





@unauth_user
def SoftkeyProcessView(request, pk):
    error = ''
    context = {}
    datetime_now =timezone.now()
    auth_branchs , auth_userlist, auth_profilelist, auth_ticketformats , auth_routes, auth_countertype = auth_data(request.user)
    context = {
        'users':auth_userlist, 'branchs':auth_branchs, 'ticketformats':auth_ticketformats, 'routes':auth_routes
        }
    try:
        counterstatus = CounterStatus.objects.get(id=pk)
    except:
        error = 'CounterStatus not found.'
    if counterstatus == None:
        error = 'CounterStatus not found.'
    if error == '':
        if counterstatus.status != 'calling':
            error = 'CounterStatus not in calling status.'
    if error == '':
        status, msg = funCounterProcess(request.user, counterstatus.countertype.branch, counterstatus.countertype, counterstatus, 'Process ticket:', 'Softkey-web', softkey_version, datetime_now)
        if status['status'] == 'Error':
            error = msg['msg']

    if error != '':
        messages.error(request, error)
        # Redirect to last page
    return redirect('softkey', pk)


@unauth_user
def SoftkeyMissView(request, pk):
    error = ''
    context = {}
    datetime_now =timezone.now()
    auth_branchs , auth_userlist, auth_profilelist, auth_ticketformats , auth_routes, auth_countertype = auth_data(request.user)
    context = {
        'users':auth_userlist, 'branchs':auth_branchs, 'ticketformats':auth_ticketformats, 'routes':auth_routes
        }
    try:
        counterstatus = CounterStatus.objects.get(id=pk)
    except:
        error = 'CounterStatus not found.'
    if counterstatus == None:
        error = 'CounterStatus not found.'
    if error == '':
        if counterstatus.status != 'calling':
            error = 'CounterStatus not in calling status.'
    if error == '':
        status, msg = funCounterMiss(request.user, counterstatus.countertype.branch, counterstatus.countertype, counterstatus, 'Miss ticket:', 'Softkey-web', softkey_version, datetime_now)
        if status['status'] == 'Error':
            error = msg['msg']

    if error != '':
        messages.error(request, error)
        # Redirect to last page
    return redirect('softkey', pk)

@unauth_user
def SoftkeyRecallView(request, pk):
    error = ''
    context = {}
    datetime_now =timezone.now()
    auth_branchs , auth_userlist, auth_profilelist, auth_ticketformats , auth_routes, auth_countertype = auth_data(request.user)
    context = {
        'users':auth_userlist, 'branchs':auth_branchs, 'ticketformats':auth_ticketformats, 'routes':auth_routes
        }
    try:
        counterstatus = CounterStatus.objects.get(id=pk)
    except:
        error = 'CounterStatus not found.'
    if counterstatus == None:
        error = 'CounterStatus not found.'
    if error == '':
        if counterstatus.status != 'calling':
            error = 'CounterStatus not in calling status.'
    if error == '':
        status, msg = funCounterRecall(request.user, counterstatus.countertype.branch, counterstatus.countertype, counterstatus, 'Recall ticket:', 'Softkey-web', softkey_version, datetime_now)
        if status['status'] == 'Error':
            error = msg['msg']

    if error != '':
        messages.error(request, error)
        # Redirect to last page
    else:
        messages.success(request, 'Recall success.')
    return redirect('softkey', pk)

@unauth_user
def SoftkeyDoneView(request, pk):
    error = ''
    context = {}
    datetime_now =timezone.now()
    auth_branchs , auth_userlist, auth_profilelist, auth_ticketformats , auth_routes, auth_countertype = auth_data(request.user)
    context = {
        'users':auth_userlist, 'branchs':auth_branchs, 'ticketformats':auth_ticketformats, 'routes':auth_routes
        }
    try:
        counterstatus = CounterStatus.objects.get(id=pk)
    except:
        error = 'CounterStatus not found.'
    if counterstatus == None:
        error = 'CounterStatus not found.'
    if error == '':
        if counterstatus.status != 'processing':
            error = 'CounterStatus not in processing status.'
    if error == '':
        status, msg = funCounterComplete(request.user, counterstatus.countertype.branch, counterstatus.countertype, counterstatus, 'Done ticket:', 'Softkey-web', softkey_version, datetime_now)
        if status['status'] == 'Error':
            error = msg['msg']

    if error != '':
        messages.error(request, error)
        # Redirect to last page
    return redirect('softkey', pk)









def repair(request):
    # 127.0.0.1:8000/repair?bc=KB&note=R000123
    context = None
    error = ''
    bcode = ''
    note = ''
    str_now = '---'
    logofile = ''

    try:
        bcode = request.GET['bc']
    except:
        bcode = ''
        error = 'Branch code is blank.'

    try:
        note = request.GET['note']
    except:
        note = ''
        error = 'Repair note is blank.'  


    branch = None
    if error == '' :        
        branchobj = Branch.objects.filter( Q(bcode=bcode) )
        if branchobj.count() == 1:
            branch = branchobj[0]
            logofile = branch.webtvlogolink
            datetime_now = timezone.now()
            datetime_now_local = funUTCtoLocal(datetime_now, branch.timezone)
            str_now = datetime_now_local.strftime('%Y-%m-%d %H:%M:%S')
        else :
            error = 'Branch not found.'
    if error == '':
        if note == 'R002301':
            counterstatus = 'done'
        else :
            counterstatus = 'error'
        context = {
            'ticket':note,
            'bcode':branch.bcode,
            'counterstatus':counterstatus,
            'logofile':logofile,
            'lastupdate':str_now,            
            'errormsg':'',
            }
    else:
        context = {
            'lastupdate':str_now, 
            'logofile':logofile,
            'errormsg':error,
            }
        messages.error(request, error)
    return render(request , 'base/repair.html', context)

def webmyticket(request, bcode, ttype, tno, sc):
    # ttype is ticket type
    # tno is ticket number
    # sc is ticket Security code
    # 127.0.0.1:8000/my/KB/A/001/123
    context = None
    error = ''
    str_now = '---'
    css = ''
    scroll = ''

    ticket = ttype + tno
    securitycode = sc

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
            str_now = datetime_now_local.strftime('%Y-%m-%d %H:%M:%S')
            css = branch.webtvcsslink
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
            scroll = countertype.displayscrollingtext
            tickettime = funUTCtoLocal(tickettime, branch.timezone)
        else :
            error = 'Ticket not found.'
    
    displaylist = None 
    if error == '' :
        # displaylist = DisplayAndVoice.objects.filter (branch=branch, countertype=countertype).order_by('-displaytime')[:5]
        displaylist = DisplayAndVoice.objects.filter (branch=branch, countertype=countertype).order_by('-displaytime')[:5]
        wdserializers  = displaylistSerivalizer(displaylist, many=True)
    
    counter='---'
    if error == '':
        csobj = CounterStatus.objects.filter(
            Q(tickettemp = tickettemp)
        )
        if csobj.count() == 1:
            counter = csobj[0].counternumber
    if error == '':
        context = {
            'wsh' : wsHypertext,
            'ticket':ticket,
            'tickettime':tickettime.strftime('%Y-%m-%d %H:%M:%S'),
            'bcode':branch.bcode,
            'counterstatus':counterstatus,
            'logofile':logofile,
            'css' : css,
            'lastupdate':str_now,            
            'counter':counter,
            'countertype':countertype,
            'tickettemp':tickettemp,
            'ticketlist':wdserializers.data,
            'errormsg':'',
            'scroll':scroll,
            }
    else:
        context = {
            'lastupdate':str_now, 
            'logofile':logofile,
            'errormsg':error,
            'scroll':scroll,
            'css' : css,
            }
        messages.error(request, error)
    return render(request , 'base/webmyticket.html', context)

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
    css = ''
    
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

    if error == '' :
        branchobj = Branch.objects.filter( Q(bcode=bcode) )
        if branchobj.count() == 1:
            branch = branchobj[0]
            logofile = branch.webtvlogolink
            datetime_now = timezone.now()
            datetime_now_local = funUTCtoLocal(datetime_now, branch.timezone)
            css = branch.webtvcsslink
        else :
            error = 'Branch not found.'
    if error == '' :
        wtobj = WebTouch.objects.filter( Q(branch=branch) & Q(name=touchname)  )
        if wtobj.count() == 1:
            wt = wtobj[0]
            touchkeylist = wt.touchkey.filter(Q(branch=branch))
            # touchkeylist = touchkeylistall.filter(Q(branch=branch))
        else :
            error = 'Web Touch not found.'
    if error == '' :
        if wt.enabled == False :
            error = 'Web Touch Disabled.'
    if error == '' :
        if request.method =='POST':
            
            for key in touchkeylist:
                if key.ttype in request.POST:
      
                    ticketno_str, countertype, tickettemp, ticket, error = newticket(branch, key.ttype, '','', datetime_now, userweb, 'web', '8')
                    if error == '' :
                        s_now= ''
                        try:
                            s_now = datetime_now.strftime('%Y-%m-%dT%H:%M:%S.%fZ')
                        except:
                            s_now = datetime_now.strftime('%Y-%m-%dT%H:%M:%SZ')
                        # add ticketlog
                        TicketLog.objects.create(
                            tickettemp=tickettemp,
                            ticket=ticket,
                            logtime=datetime_now,
                            app = 'web',
                            version = '8',
                            logtext='New Ticket by Web Touch: '  + tickettemp.branch.bcode + '_' + tickettemp.tickettype + '_'+ tickettemp.ticketnumber + '_' + s_now ,
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
                        

    if error != '' :
        touchkeylist= []
        messages.error(request, error)
    context = {
        'touchkeylist':touchkeylist,
        'logofile':logofile,
        'errormsg':error,
        'css' : css,
        }        
    return render(request, 'base/webtouch.html', context)

def CancelTicketView(request, pk, sc):
    error = ''
    logofile = ''
    url = ''
    backurl = ''
   
    try:
        tt = TicketTemp.objects.get(id=pk)
        logofile = tt.branch.webtvlogolink
        css = tt.branch.webtvcsslink

        # back to : http://127.0.0.1:8000/my/?tt=A&no=003&bc=KB&sc=vVL
        # base_url = reverse('myticket')
        # query_string =  urlencode({
        #                             'tt':tt.tickettype , 
        #                             'no':tt.ticketnumber, 
        #                             'bc':tt.branch.bcode, 
        #                             'sc':tt.securitycode,
        #                             }) 
        # url = '{}?{}'.format(base_url, query_string)  # 3 ip/my/?tt=A&no=003&bc=KB&sc=vVL

        base_url = '/my'
        url = base_url + '/' + tt.branch.bcode + '/' + tt.tickettype +'/' + tt.ticketnumber + '/' + tt.securitycode + '/'
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
                s_now= ''
                try:
                    s_now = datetime_now.strftime('%Y-%m-%dT%H:%M:%S.%fZ')
                except:
                    s_now = datetime_now.strftime('%Y-%m-%dT%H:%M:%SZ')
                # add ticketlog
                TicketLog.objects.create(
                    tickettemp=tt,
                    logtime=datetime_now,
                    app = 'Web',
                    version = '8',
                    logtext='Ticket Void by web : '  + tt.branch.bcode + '_' + tt.tickettype + '_'+ tt.ticketnumber + '_' + s_now ,
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
    'css':css,
    }
    return render(request, 'base/webmyticket_cancel.html', context)

def webmyticket_old_school(request):
    # 127.0.0.1:8000/my?tt=A&no=001&bc=KB&sc=123
    context = None
    error = ''
    bcode = ''
    css = ''
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
            css = branch.webtvcsslink
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
        # displaylist = DisplayAndVoice.objects.filter (branch=branch, countertype=countertype).order_by('-displaytime')[:5]
        displaylist = DisplayAndVoice.objects.filter (branch=branch, countertype=countertype).order_by('-displaytime')[:5]
        wdserializers  = displaylistSerivalizer(displaylist, many=True)
    
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
            'css' : css,
            'lastupdate':datetime_now_local.strftime('%Y-%m-%d %H:%M:%S'),            
            'counter':counter,
            'countertype':countertype,
            'tickettemp':tickettemp,
            'ticketlist':wdserializers.data,
            'errormsg':'',
            'scroll':countertype.displayscrollingtext,
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
    str_now = '---'

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
            datetime_now = timezone.now()
            datetime_now_local = funUTCtoLocal(datetime_now, branch.timezone)
            str_now = datetime_now_local.strftime('%Y-%m-%d %H:%M:%S')

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

        context = {
        'lastupdate' : str_now,
        'ticketlist' : displaylist,
        'logofile' : logofile,
        'scroll':countertype.displayscrollingtext,
        }
    else :
        context = {
        'lastupdate' : str_now,
        'errormsg' : error,
        }
        messages.error(request, error)
    return render(request , 'base/webtvold3.html', context)


def webtv(request, bcode, ct):
    # WebSocket version
    # http://127.0.0.1:8000/webtv/KB/Reception/
    context = None
    error = ''
    str_now = '---'
    logofile = ''

    countertypename = ct

    branch = None
    if error == '' :        
        branchobj = Branch.objects.filter( Q(bcode=bcode) )
        if branchobj.count() == 1:
            branch = branchobj[0]
            logofile = branch.webtvlogolink
            css = branch.webtvcsslink
            datetime_now = timezone.now()
            datetime_now_local = funUTCtoLocal(datetime_now, branch.timezone)
            str_now = datetime_now_local.strftime('%Y-%m-%d %H:%M:%S')
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
        displaylist = DisplayAndVoice.objects.filter (branch=branch, countertype=countertype).order_by('-displaytime')[:5]
        wdserializers  = displaylistSerivalizer(displaylist, many=True)
        # displaylist = ({'ticketlist':wdserializers.data})

        datetime_now = timezone.now()
        datetime_now_local = funUTCtoLocal(datetime_now, branch.timezone)

        context = {
        'wsh' : wsHypertext,
        'lastupdate' : str_now,
        'ticketlist' : wdserializers.data,
        'logofile' : logofile,
        'css' : css,
        'scroll':countertype.displayscrollingtext,
        }
        # print (wdserializers.data[0].wait)
    else :
        context = {
        'lastupdate' : str_now,
        'errormsg' : error,
        'logofile' : logofile,
        }
        messages.error(request, error)




    context = {
        'bcode' :  bcode ,
        'ct' : ct,
        } | context
    

    return render(request , 'base/webtv.html', context)


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

    auth_branchs , auth_userlist, auth_profilelist, auth_ticketformats , auth_routes, auth_countertype = auth_data(request.user)
    # users = User.objects.exclude( Q(is_superuser=True) | Q(groups__name='api'))    
    # ticketformats = TicketFormat.objects.all().order_by('branch','ttype')
    # routes = TicketRoute.objects.all().order_by('branch','tickettype','step')
    # countertypes = CounterType.objects.all()

    now_l = datetime.now()
    snow_l = now_l.strftime('%Y-%m-%dT%H:%M:%S')

    context = {
    'now':snow_l,
    'users':auth_userlist,
    'branchs':auth_branchs,  
    'ticketformats':auth_ticketformats, 
    'routes':auth_routes,
    'countertypes':auth_countertype,
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
    auth_branchs , auth_userlist, auth_profilelist, auth_ticketformats , auth_routes, auth_countertype = auth_data(request.user)
 
    # users = User.objects.exclude( Q(is_superuser=True) | Q(groups__name='api'))
    #users = User.objects.exclude( Q(is_superuser=True) )
    # profiles = UserProfile.objects.all()
    # branchs = Branch.objects.all()    
    # ticketformats = TicketFormat.objects.all()
    # routes = TicketRoute.objects.all()
    # profiles = UserProfile.objects.filter(Q(user=users.user))
    #profiles = users.userprofile_set.all()
    
    context = {'users':auth_userlist, 'profiles':auth_profilelist, 'branchs':auth_branchs, 'ticketformats':auth_ticketformats, 'routes':auth_routes}
    return render(request, 'base/supervisors.html', context)

@unauth_user
@allowed_users(allowed_roles=['admin'])
def TicketRouteNewView(request):
    if request.user.is_superuser == True :
        auth_branchs = Branch.objects.all()
    else :
        auth_userp = UserProfile.objects.get(user__exact=request.user)
        auth_branchs = auth_userp.branchs.all()
    form = trForm(auth_branchs=auth_branchs)
    if request.method == 'POST':
        error = ''
        form = trForm(request.POST, auth_branchs=auth_branchs)
        error, newroute = checkticketrouteform(form)
                            # if error == '':
                            #     if form.is_valid() == False:
                            #         error_string = ' '.join([' '.join(x for x in l) for l in list(form.errors.values())])
                            #         error = 'An error occurcd during registration: '+ error_string
                            # # newroute.tickettype  = newroute.tickettype.upper()
                            # if error == '':
                            #     newroute = form.save(commit=False)
                            #     if newroute.branch == None :
                            #         error = 'An error occurcd : Branch is blank'
                            # if error == '':
                            #     if newroute.countertype == None :
                            #         error = 'An error occurcd : Counter Type is blank'
                            # if error == '' :
                            #     #check ticket type should be letter
                            #     if newroute.tickettype.isalpha() == False :
                            #         error = 'An error occurcd : Ticket Type should be letter'
                            # # newroute.step is int so no need to check
                            # # if error == '' :
                            #     #check step should be number
                            #     # if newroute.step.isnumeric() == False :
                            #     #     error = 'An error occurcd : Step should be number'
        if error == '':
            try:
                newroute.save()
                messages.success(request, 'Created new Ticket Route.')
            except:
                messages.error(request,' An error occurcd during registration: ' )
            return redirect('routesummary')

        if error != '':
            messages.error(request, error)
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
    if request.user.is_superuser == True :
        auth_branchs = Branch.objects.all()
    else :
        auth_userp = UserProfile.objects.get(user__exact=request.user)
        auth_branchs = auth_userp.branchs.all()
    route = TicketRoute.objects.get(id=pk)    
    if request.method == 'POST':
        error = ''
        trform = trForm(request.POST, instance=route, prefix='trform', auth_branchs=auth_branchs)
        error, newroute = checkticketrouteform(trform)  
        if error == '':
            try:
                newroute.save()
                messages.success(request, 'Ticket Route was successfully updated!')
            except:
                messages.error(request,'An error occurcd during update' )
            return redirect('routesummary')

        if error != '':
            messages.error(request, error)                
    else:
        trform = trForm(instance=route, prefix='trform', auth_branchs=auth_branchs)
       
    context =  {'route':route, 'trform':trform }
    return render(request, 'base/route-update.html', context)


@unauth_user
@allowed_users(allowed_roles=['admin'])
def TicketRouteSummaryView(request):  
    auth_branchs , auth_userlist, auth_profilelist, auth_ticketformats , auth_routes, auth_countertype = auth_data(request.user)
 
    # users = User.objects.exclude( Q(is_superuser=True) | Q(groups__name='api'))
    # branchs = Branch.objects.all()
    # ticketformats = TicketFormat.objects.all().order_by('branch','ttype')
    # routes = TicketRoute.objects.all().order_by('branch','tickettype','step')

    context = {'users':auth_userlist, 'branchs':auth_branchs, 'ticketformats':auth_ticketformats, 'routes':auth_routes}

    return render(request, 'base/routes.html', context)

@unauth_user
@allowed_users(allowed_roles=['admin'])
def TicketFormatNewView(request):

    if request.user.is_superuser == True :
        auth_branchs = Branch.objects.all()
    else :
        auth_userp = UserProfile.objects.get(user__exact=request.user)
        auth_branchs = auth_userp.branchs.all()
    form = TicketFormatForm(auth_branchs=auth_branchs)
    if request.method == 'POST':
        form = TicketFormatForm(request.POST, auth_branchs=auth_branchs)
        
        error = ''
        error, tf = checkticketformatform(form)
        
        if error == '' :
            try:
                tf.save()
                messages.success(request, 'Created new Ticket Format.')

            except:
                error = 'An error occurcd during registration'

            if error == '':
                # create new ticket route automatically
                # check if ticket route already exist
                objct = CounterType.objects.filter(branch=tf.branch)
                if objct.count() > 0 :
                    ct = objct[0]
                    objtr = TicketRoute.objects.filter(branch=tf.branch, tickettype=tf.ttype, countertype=ct, step=1)
                    if objtr.count() == 0 :
                        # Create new ticket route
                        TicketRoute.objects.create(enabled=True, branch=tf.branch, tickettype=tf.ttype, step=1, countertype=ct)
                        messages.success(request, 'Create new ticket route automatically')
            else:
                messages.error(request, error)

            return redirect('tfsummary')
        if error != '':
            messages.error(request, error)
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
    if request.user.is_superuser == True :
        auth_branchs = Branch.objects.all()
    else :
        auth_userp = UserProfile.objects.get(user__exact=request.user)
        auth_branchs = auth_userp.branchs.all()

    if request.method == 'POST':
        tfform = TicketFormatForm(request.POST, instance=ticketformat, prefix='tfform',  auth_branchs=auth_branchs)
        error = ''
        error, tf = checkticketformatform(tfform)
        if error == '' :
            try :
                tf.save()
                messages.success(request, 'Ticket Format was successfully updated!')
                return redirect('tfsummary')
            except:
                error = 'An error occurcd during updating TicketFormat'
            
        if error != '':
            messages.error(request, error )
    else:
        tfform = TicketFormatForm(instance=ticketformat, prefix='tfform', auth_branchs=auth_branchs)        
    context =  {'tfform':tfform, 'ticketformat':ticketformat, }
    return render(request, 'base/tf-update.html', context)

@unauth_user
@allowed_users(allowed_roles=['admin'])
def TicketFormatSummaryView(request):
    auth_branchs , auth_userlist, auth_profilelist, auth_ticketformats , auth_routes, auth_countertype = auth_data(request.user)
  
    # users = User.objects.exclude( Q(is_superuser=True) | Q(groups__name='api'))
    # branchs = Branch.objects.all()
    # ticketformats = TicketFormat.objects.all().order_by('branch','ttype')
    # routes = TicketRoute.objects.all()
    context = {'users':auth_userlist, 'branchs':auth_branchs, 'ticketformats':auth_ticketformats, 'routes':auth_routes}
    return render(request, 'base/tfs.html', context)

@unauth_user
@allowed_users(allowed_roles=['admin'])
def Branch_Save(request, pk):
    branch = Branch.objects.get(id=pk) 
    result = ''

    # User do not touch Branch Enabled
    # s_branchenabled = 'off'
    # try:
    #     s_branchenabled = request.GET['branchenabled']
    # except:
    #     s_branchenabled = 'off'
    # if s_branchenabled == 'on':
    #     new_branchenabled = True
    # else:
    #     new_branchenabled = False



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

    s_smsenabled = 'off'
    try:
        s_smsenabled = request.GET['enabledsms']
    except:
        s_smsenabled = 'off'   
    if s_smsenabled == 'on':
        new_smsenabled = True
    else:
        new_smsenabled  = False  

    new_smsmsg = request.GET['smsmsg']
    if result == '' :
        # branch.enabled = new_branchenabled
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
        branch.enabledsms = new_smsenabled
        branch.smsmsg = new_smsmsg
        
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

    enabledsms = branch.enabledsms
    smsmsg = branch.smsmsg

    context = {
    'branch':branch,
    'branchcode':branchcode, 'branchname':branchname, 'branchenabled':branchenabled,
    'timezone':timezone, 
    'officehourstart':sofficehourstart, 'officehourend':sofficehourend,
    'tickettimestart':stickettimestart, 'tickettimeend':stickettimeend,
    'queuepriority':queuepriority,
    'countertypes':countertypes,
    'enabledsms':enabledsms,
    'smsmsg':smsmsg,
    }

    return render(request, 'base/branch-update.html', context)

@unauth_user
@allowed_users(allowed_roles=['admin'])
def BranchSummaryView(request):  
    # users = User.objects.exclude( Q(is_superuser=True) | Q(groups__name='api'))
    #users = User.objects.exclude( Q(is_superuser=True) )
    # profiles = UserProfile.objects.all()
    # branchs = Branch.objects.all()    
    # ticketformats = TicketFormat.objects.all()
    # routes = TicketRoute.objects.all()
    # profiles = UserProfile.objects.filter(Q(user=users.user))
    #profiles = users.userprofile_set.all()
    auth_branchs , auth_userlist, auth_profilelist, auth_ticketformats , auth_routes, auth_countertype = auth_data(request.user)


    context = {'users':auth_userlist, 'profiles':auth_profilelist, 'branchs':auth_branchs, 'ticketformats':auth_ticketformats, 'routes':auth_routes}
    return render(request, 'base/branch.html', context)

@unauth_user
def homeView(request):
    auth_branchs , auth_userlist, auth_profilelist, auth_ticketformats , auth_routes, auth_countertype = auth_data(request.user)

    # users = User.objects.exclude( Q(is_superuser=True) | Q(groups__name='api'))
    # branchs = Branch.objects.all()
    # ticketformats = TicketFormat.objects.all()
    # routes = TicketRoute.objects.all()
    # users = User.objects.exclude(is_superuser=True)





    context =  {'users':auth_userlist , 'branchs':auth_branchs, 'ticketformats':auth_ticketformats, 'routes':auth_routes}
    return render(request, 'base/home.html', context)

@unauth_user
@allowed_users(allowed_roles=['admin'])
def UserSummaryView(request):     
    auth_branchs , auth_userlist, auth_profilelist, auth_ticketformats , auth_routes, auth_countertype = auth_data(request.user)
 
    context = {'users':auth_userlist, 'profiles':auth_profilelist, 'branchs':auth_branchs, 'ticketformats':auth_ticketformats, 'routes':auth_routes}
    return render(request, 'base/user.html', context)

def UserLogoutView(request):   
    logout(request)
    return redirect('login')

@unauth_user_login
def UserLoginView(request):
    page = 'login'
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        username = request.POST.get('username').lower()
        password = request.POST.get('password')
        human = True

        if enable_captcha == True :
            captchaform = CaptchaForm(request.POST)
            if captchaform.is_valid():
                human = True
            else:
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
        if enable_captcha == True :
            captchaform = CaptchaForm()
        pass

    context = {'page':page} 
    if enable_captcha == True :
        context = context | {'captcha_form':captchaform} 
    return render(request, 'base/login_register.html', context)
    
@unauth_user
@allowed_users(allowed_roles=['admin'])
def UserUpdateView(request, pk):
    user = User.objects.get(id=pk)
    userp = UserProfile.objects.get(user__exact=user)
    error = ''
    if request.user.is_superuser == True :
        auth_branchs = Branch.objects.all()
    else :
        auth_userp = UserProfile.objects.get(user__exact=request.user)
        auth_branchs = auth_userp.branchs.all()
    # get all ticketformat but not ttype is repeated 
    ticketformat = TicketFormat.objects.all()

    for tf in ticketformat:
        # check if userp.branchs is not in tt.branchs
        if tf.branch not in userp.branchs.all():
            ticketformat = ticketformat.exclude(id=tf.id)
    ticketformat2 = ticketformat



    for tf in ticketformat:
        for tf2 in ticketformat:
            if tf != tf2:
                if tf.ttype == tf2.ttype:
                    ticketformat = ticketformat.exclude(id=tf.id)
                    ticketformat2 = ticketformat2.exclude(id=tf2.id)
    
    for tt in ticketformat2:
        # check if userp.branchs is not in tt.branchs
        if tt.branch not in userp.branchs.all():
            ticketformat2 = ticketformat2.exclude(id=tt.id)

    # add column for checked or unchecked to ticketformat2
    listusertt = userp.tickettype.split(',')
    for tt in ticketformat2:
        if tt.ttype in listusertt:
            tt.checked = 'checked'
        else:
            tt.checked = 'unchecked'
        tt.save()

    if request.method != 'POST':
        if request.user.is_superuser == True :
            userform = UserFormSuper(instance=user, prefix='uform')
        else :
            userform = UserForm(instance=user, prefix='uform')
        if user == request.user:
            userform = UserFormAdmin(instance=user, prefix='uform')  
        profileform = UserProfileForm(instance=userp, prefix='pform', auth_branchs=auth_branchs)
    elif request.method == 'POST':
        if request.user.is_superuser == True :
            userform = UserFormSuper(request.POST, instance=user, prefix='uform')
        else :
            userform = UserForm(request.POST, instance=user, prefix='uform')
        if user == request.user:
            userform = UserFormAdmin(request.POST, instance=user, prefix='uform')        
        
        profileform = UserProfileForm(request.POST, instance=userp, prefix='pform', auth_branchs=auth_branchs)
        newtickettypeform = newTicketTypeForm(request.POST)
        # check moblie phone format
        # inttel = profileform.mobilephone
        # if inttel != '+852':
        #     profileform.is_valid = False
        #     messages.error(request, 'Mobile phone number should include country code. E.g. "+852"')


        if (userform.is_valid() & profileform.is_valid() & newtickettypeform.is_valid()):
        # if (userform.is_valid() & profileform.is_valid()  ):
            profileform_temp = profileform.save(commit=False)
            
            # get data from html, and update to profileform_temp
            new_tt = newtickettypeform['new_tickettype'].value()
            print ('new_tt = ' + new_tt)
            if new_tt == '<No ticket type>':
                new_tt = ''
            profileform_temp.tickettype = new_tt

            if profileform_temp.mobilephone != None:
                inttel = profileform_temp.mobilephone[0:4]
                if inttel != '+852':
                    error = 'Mobile phone number should include HK country code. E.g. "+852"'
                if len(profileform_temp.mobilephone) != 12 :
                    error = 'Mobile phone number should 12-digit including country code.'
        else:
            profileform_temp = profileform.save(commit=False)

        if error == '':
            userform.save()
            profileform.save()            
            # profileform_temp.tickettype = profileform_temp.tickettype.upper()
            profileform_temp.save()
            # profileform_temp = profileform.save(commit=False)
            # profileform_temp.tickettype = profileform_temp.tickettype.upper()
            # profileform_temp.branchs = profileform.branchs
            
            # profileform_temp.save()
            messages.success(request, 'Profile was successfully updated!')
            return redirect('usersummary')
        else:
            messages.error(request, error)

    context =  {'userform':userform , 'profileform':profileform, 'user':user, 'userp':userp,'ticketformat':ticketformat2,'userptt':listusertt,}
    return render(request, 'base/user-update.html', context)

@unauth_user
@allowed_users(allowed_roles=['admin'])
def UserUpdateTTView(request, pk):
    userp = UserProfile.objects.get(id=pk)
    # get all ticketformat but not ttype is repeated 
    ticketformat = TicketFormat.objects.all()
    ticketformat2 = TicketFormat.objects.all()
    for tf in ticketformat:
        for tf2 in ticketformat:
            if tf != tf2:
                if tf.ttype == tf2.ttype:
                    ticketformat = ticketformat.exclude(id=tf.id)
                    ticketformat2 = ticketformat2.exclude(id=tf2.id)

    # add column for checked or unchecked to ticketformat2
    for tt in ticketformat2:
        tt2 = tt.ttype + ','
        if userp.tickettype.find(tt2) != -1:
            tt.checked = 'checked'
        else:
            tt.checked = 'unchecked'
        tt.save()

    context =  {'userp':userp, 'ticketformat':ticketformat2, }
    return render(request, 'base/user-update-tickettype.html', context)

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

def auth_data(user):

    if user.is_superuser == True :
        auth_profilelist = UserProfile.objects.all()
        auth_userlist = User.objects.exclude(Q(groups__name='web'))
        auth_branchs = Branch.objects.all()
        auth_ticketformats = TicketFormat.objects.all().order_by('branch','ttype')
        auth_routes = TicketRoute.objects.all().order_by('branch','countertype', 'tickettype', 'step')
        auth_countertype = CounterType.objects.all()
    else :
        profiles = UserProfile.objects.all()
        auth_branchs = UserProfile.objects.get(user=user).branchs.all()

        profid_list = []
        userid_list = []
        for prof in profiles :
            not_auth = False
            for b in prof.branchs.all():
                if (b in auth_branchs) == True :
                    pass                
                else :
                    not_auth = True
            if not_auth == False :
                if prof.user.is_superuser == False :
                    if ('api' in prof.user.groups.all()) == False :
                        if ('web' in prof.user.groups.all()) == False :
                            profid_list.append(prof.id)
                            userid_list.append(prof.user.id)
                        
        auth_userlist = User.objects.filter(id__in=userid_list)
        auth_profilelist = UserProfile.objects.filter(id__in=profid_list)
        auth_ticketformats = TicketFormat.objects.filter(branch__in=auth_branchs).order_by('branch','ttype')
        auth_routes = TicketRoute.objects.filter(branch__in=auth_branchs).order_by('branch','countertype', 'tickettype', 'step')
        auth_countertype = CounterType.objects.filter(branch__in=auth_branchs)
    return(auth_branchs, auth_userlist, auth_profilelist, auth_ticketformats, auth_routes, auth_countertype)


def checkticketrouteform(form):
    error = ''
    newform = None
    if error == '':
        if form.is_valid() == False:
            error_string = ' '.join([' '.join(x for x in l) for l in list(form.errors.values())])
            error = 'An error occurcd during registration: '+ error_string
    # newroute.tickettype  = newroute.tickettype.upper()
    if error == '':
        newform = form.save(commit=False)
        if newform.branch == None :
            error = 'An error occurcd : Branch is blank'
    if error == '':
        if newform.countertype == None :
            error = 'An error occurcd : Counter Type is blank'
    if error == '' :
        #check ticket type should be letter
        if newform.tickettype.isalpha() == False :
            error = 'An error occurcd : Ticket Type should be letter'
    # newroute.step is int so no need to check
    # if error == '' :
        #check step should be number
        # if newroute.step.isnumeric() == False :
        #     error = 'An error occurcd : Step should be number'
    return (error, newform)

def checkticketformatform(form):
    error = ''
    newform = None

    if form.is_valid() == False:
        error_string = ' '.join([' '.join(x for x in l) for l in list(form.errors.values())])
        error = 'An error occurcd during registration: '+ error_string
    
    if error == '' :
        newform = form.save(commit=False)
        if newform.branch == None :
            # Error branch is None
            error = 'Error Branch is blank'
    if error == '' :
        # check if ticket type should be letter
        if newform.ttype.isalpha() == False :
            error = 'Ticket type should be letter'
    return (error, newform)