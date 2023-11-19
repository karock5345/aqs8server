from aqs.settings import aqs_version
from django.shortcuts import render, redirect, HttpResponse
from django.urls import reverse
from urllib.parse import urlencode
from django.contrib.auth.models import User, Group
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.hashers import make_password
from django.db.models import Q
from django.contrib.auth.forms import UserCreationForm, PasswordChangeForm
# from datetime import datetime
from base.decorators import *
# from django.contrib.auth.views import PasswordChangeView
from django.urls import reverse_lazy

from .models import TicketLog, CounterStatus, CounterType, TicketData, TicketRoute, UserProfile, TicketFormat, Branch, TicketTemp, DisplayAndVoice, PrinterStatus, WebTouch, Ticket, UserStatusLog
from .forms import TicketFormatForm, UserForm, UserFormAdmin, UserProfileForm,trForm, resetForm, BranchSettingsForm_Admin
from .forms import CaptchaForm, getForm, voidForm, newTicketTypeForm, UserFormSuper, UserFormManager, UserFormSupport, UserFormAdminSelf
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
import csv
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from aqs.tasks import *
import pickle
from django.templatetags.static import static
from celery.result import AsyncResult
from django.conf import settings
from base.sch.views import sch_shutdown

logger = logging.getLogger(__name__)

enable_captcha = False

userweb = None
try:
    userweb = User.objects.get(username='userweb')
except:
    logger.error('userweb not found.')
    

context_login = {}

sort_direction = {}



@allowed_users(allowed_roles=['admin','support','supervisor','manager','reporter'])
@unauth_user
def SuperVisor_ForceLogoutView(request, pk, csid):
    context = {}
    datetime_now =timezone.now()
    username = ''
    try:
        cs = CounterStatus.objects.get(id=csid)
        datetime_now_local = funUTCtoLocal(datetime_now, cs.countertype.branch.timezone)
        str_now = datetime_now_local.strftime('%Y-%m-%d %H:%M:%S')
    except:
        messages.error(request, 'Counter Status not found.')
        return redirect('supervisor', pk=pk)
    # check counterstatus is loged in and user is not None
    if cs.loged == True and cs.user != None:       
        username = cs.user.first_name + ' ' + cs.user.last_name + ' (' + cs.user.username + ')'
    else:
        messages.error(request, 'No user login on this counter number ' + cs.counternumber + '.')
        return redirect('supervisor', pk=pk)
    
    context = {'aqs_version':aqs_version, 'confirm_obj':cs, 'confirm_text':'Could you please confirm to force logout ' + username + '?'}
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'confirm':           
            result = ForceLogout(cs, datetime_now)
            if result == 'OK':
                # websocket to web softkey for update counter status
                wscounterstatus(cs)
                messages.success(request, 'User ' + username + ' has been force logout.')
            else:
                messages.error(request, result)
            return redirect('supervisor', pk=pk)
    return render(request , 'base/confirm.html', context)
    
def ForceLogout(cs, datetime_now):
    # update counter login log
    # update user status log
    result = logcounterlogout(cs.user, cs.countertype, cs.counternumber, cs.logintime, datetime_now)

    if result == 'OK':
        # update counterstatus
        cs.loged = False
        cs.user = None
        cs.status = lcounterstatus[lcounterstatus.index('waiting')]
        cs.tickettemp = None
        cs.save()

        # send websocket to counterstatus
        wscounterstatus(cs)
    return result


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
    
    text = 'Confirm to void ticket : "' + tt.tickettype + tt.ticketnumber + '" ?'
    context = {'aqs_version':aqs_version} | {'tt':tt} | {'text':text}
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'confirm':           
            funVoid(request.user, tt, td, datetime_now)
            messages.success(request, 'Ticket ' + tt.tickettype + tt.ticketnumber + ' has been voided.')
            return redirect('softkey', pk=pk)
    return render(request , 'base/softkey_confirm.html', context)

@unauth_user
def Softkey_GetView(request, pk, ttid):
    context = {}
    datetime_now =timezone.now()
    error = ''

    if error == '':
        try:
            tt = TicketTemp.objects.get(id=ttid)
            datetime_now_local = funUTCtoLocal(datetime_now, tt.branch.timezone)
            str_now = datetime_now_local.strftime('%Y-%m-%d %H:%M:%S')
        except:
            error = 'TicketTemp not found.'
    if error == '':
        try:
            td = TicketData.objects.get(Q(tickettemp=tt))
        except:
            error = 'TicketData not found.'
    
    if error == '':
        try:
            counterstatus = CounterStatus.objects.get(id=pk)
        except:
            error = 'CounterStatus not found.'
    
    # no need to confirm
    if error == '':
        status, msg, context_get = funCounterGet('', tt.tickettype, tt.ticketnumber, request.user, counterstatus.countertype.branch, counterstatus.countertype, counterstatus, 'Get ticket from list', 'Softkey-web', softkey_version, datetime_now)
        if status['status'] == 'Error':
            error = msg['msg'] + ' ' + tt.tickettype + tt.ticketnumber
    # # no need to confirm
    # if error == '':
    #     text = 'Confirm to call ticket : "' + tt.tickettype + tt.ticketnumber + '" ?'
    #     context = {'tt':tt} | {'text':text}
    #     if request.method == 'POST':
    #         action = request.POST.get('action')
    #         if action == 'confirm':           
    #             status, msg, context_get = funCounterGet('', tt.tickettype, tt.ticketnumber, request.user, counterstatus.countertype.branch, counterstatus.countertype, counterstatus, 'Get ticket from list', 'Softkey-web', softkey_version, datetime_now)
    #             if status['status'] == 'Error':
    #                 error = msg['msg'] + ' ' + tt.tickettype + tt.ticketnumber
    # if error != '':
    #     messages.error(request, error)
    #     return redirect('softkey', pk=pk)
    # else :
    #     return render(request , 'base/softkey_confirm.html', context)

    if error != '':
        messages.error(request, error)
    return redirect('softkey', pk=pk)



                


@unauth_user
def SoftkeyView(request, pk):
    context = {}
    context_counter = {}
    error = ''
    str_now = '--:--'
    datetime_now =timezone.now()

    auth_branchs , auth_userlist, auth_userlist_active, auth_grouplist, auth_profilelist, auth_ticketformats , auth_routes, auth_countertype = auth_data(request.user)
    context = {
    'aqs_version':aqs_version, 
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

                b_userttype = False
                userttype = context_counter['data']['userttype']
                # convert userttype to list split by comma
                l_userttype = []
                l_userttype = userttype.split(',')
                # check if tr.tickettype in l_userttype
                if tr.tickettype in l_userttype:
                    b_userttype = True
                    # print (tr.tickettype + ' in ' + str(l_userttype))
                # if context_counter['data']['userttype'].find(tr.tickettype + ',') != -1:
                #     b_userttype = True
                newrow = {
                    'tickettype' : tr.tickettype,
                    'lang1' : lang1,
                    'lang2' : lang2,
                    'wait' : tr.waiting,
                    'userttype' : b_userttype,             
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

            tickettime_local = funUTCtoLocal(utctt, counterstatus.countertype.branch.timezone)
            # context_ql[i]['tickettime_local'] = funUTCtoLocal(utctt, counterstatus.countertype.branch.timezone)
            context_ql[i]['tickettime_local'] = tickettime_local.strftime('%H:%M:%S %Y-%m-%d')
            context_ql[i]['tickettime_local_short'] = tickettime_local.strftime('%H:%M:%S %m-%d')

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

    auth_branchs , auth_userlist, auth_userlist_active, auth_grouplist, auth_profilelist, auth_ticketformats , auth_routes, auth_countertype = auth_data(request.user)

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
        'aqs_version':aqs_version, 
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

    auth_branchs , auth_userlist, auth_userlist_active, auth_grouplist, auth_profilelist, auth_ticketformats , auth_routes, auth_countertype = auth_data(request.user)

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
        'aqs_version':aqs_version, 
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
    auth_branchs , auth_userlist, auth_userlist_active, auth_grouplist, auth_profilelist, auth_ticketformats , auth_routes, auth_countertype = auth_data(request.user)
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
    auth_branchs , auth_userlist, auth_userlist_active, auth_grouplist, auth_profilelist, auth_ticketformats , auth_routes, auth_countertype = auth_data(request.user)

    context = {
        'aqs_version':aqs_version, 
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
    auth_branchs , auth_userlist, auth_userlist_active, auth_grouplist, auth_profilelist, auth_ticketformats , auth_routes, auth_countertype = auth_data(request.user)
    context = {
        'aqs_version':aqs_version, 
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
    auth_branchs , auth_userlist, auth_userlist_active, auth_grouplist, auth_profilelist, auth_ticketformats , auth_routes, auth_countertype = auth_data(request.user)
    context = {
        'aqs_version':aqs_version, 
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
    auth_branchs , auth_userlist, auth_userlist_active, auth_grouplist, auth_profilelist, auth_ticketformats , auth_routes, auth_countertype = auth_data(request.user)
    context = {
        'aqs_version':aqs_version, 
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
    auth_branchs , auth_userlist, auth_userlist_active, auth_grouplist, auth_profilelist, auth_ticketformats , auth_routes, auth_countertype = auth_data(request.user)
    context = {
        'aqs_version':aqs_version, 
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
    context = {'aqs_version':aqs_version} | context 
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
    context = {'aqs_version':aqs_version} | context 
    return render(request , 'base/webmyticket.html', context)

# Create your views here.
def webtouchView(request):
    # 127.0.0.1:8000/touch?bc=KB&t=t1
    # t1 is Touch Name
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
        wtobj = WebTouch.objects.filter( Q(branch=branch) & Q(name=touchname))
        if wtobj.count() == 1:
            wt = wtobj[0]
            touchkeylist = wt.touchkey.filter(Q(branch=branch))
            # sort touchkeylist by tickettype
            touchkeylist = sorted(touchkeylist, key=lambda x: x.ttype)
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
                        # ip/my/KB/A/003/vVL
                        base_url = reverse('myticket', args=[tickettemp.branch.bcode, tickettemp.tickettype, tickettemp.ticketnumber, tickettemp.securitycode] )
                        url = base_url

                        # for old version (webmyticket_old_school) ip/my/?tt=A&no=003&bc=KB&sc=vVL
                        # query_string =  urlencode({
                        #             'tt':tickettemp.tickettype , 
                        #             'no':tickettemp.ticketnumber, 
                        #             'bc':tickettemp.branch.bcode, 
                        #             'sc':tickettemp.securitycode,
                        #             })
                        # url = '{}?{}'.format(base_url, query_string)  # 3 ip/my/?tt=A&no=003&bc=KB&sc=vVL
                        # backurl = '{0}://{1}'.format(request.scheme, request.get_host()) +   url
                        # print (backurl)
                        if url != '':
                            return redirect(url)
                        

    if error != '' :
        touchkeylist= []
        messages.error(request, error)
    context = {
        'aqs_version':aqs_version,
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
        messages.error(request, error)
        if url != '':
            return redirect(url)

    context = {
    'aqs_version':aqs_version,
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
    context = {'aqs_version':aqs_version} | context 
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
    context = {'aqs_version':aqs_version} | context 
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
    
    context = {'aqs_version':aqs_version} | context 
    return render(request , 'base/webtv.html', context)


@unauth_user
@allowed_users(allowed_roles=['admin','support','supervisor','manager','reporter'])
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

    if error == '':
        # check enddate - startdate > 200 days
        if (enddate - startdate).days > 200 :
            error = 'Error : Date range do not more then 200 days.'

    table = None
    if error == '':
        localtimezone = pytz.timezone(branch.timezone)
        # report_result = 'RAW Data Report\nBranch:' + branch.name + '(' + branch.bcode + ')\nStart datetime:' + s_startdate + '\nEnd datetime:' + s_enddate 
        report_result1 = 'RAW Data Report'
        report_result2 = 'Branch:' + branch.name + '(' + branch.bcode + ')'
        report_result3 = 'Start datetime:' + s_startdate
        report_result4 = 'End datetime:' + s_enddate 
        report_result5 = 'Counter Type:ALL'        
        
        if countertype == None  :
            table = TicketData.objects.filter(
                Q(branch=branch),
                Q(starttime__range=[startdate,enddate]),
                ~Q(ticket = None),
            ).order_by('starttime')
            
        else:
            table = TicketData.objects.filter(
                Q(branch=branch),
                Q(starttime__range=[startdate,enddate]),
                ~Q(ticket = None),
                Q(countertype=countertype),
            ).order_by('starttime') 
            report_result5 = 'Counter Type:' + countertype.name 
        report_result6 = 'Total records:' + str(table.count())
        report_result = report_result1 + '\n' + report_result2 + '\n' + report_result3 + '\n' + report_result4 + '\n' + report_result5 + '\n' + report_result6

        # # check if rows > 10000 then error
        # if table.count() > 10000 :
        #     error = 'Error : Records more then 10000'
    
    table100 = None
    if error == '':            
        # Pagination

        page = request.GET.get('page') if request.GET.get('page') != None else '1'
        page = int(page)
        per_page = 100  # Number of items per page

        paginator = Paginator(table, per_page)
        try:
            table100 = paginator.page(page)
        except PageNotAnInteger:
            table100 = paginator.page(1)
        except EmptyPage:
            table100 = paginator.page(paginator.num_pages)    

    if error == '':    
        if request.method == 'POST':
        # Export and download excel file
            action = request.POST.get('action')
            if action == 'excel':

                

                # convert table to string
                querystr = pickle.dumps(table.query)

                # # debug only
                # table2 = TicketData.objects.all() 
                # table2.query = pickle.loads(querystr)
                # task_id = '1234'
                # print('is same?' + str(table2 == table))

                # print(querystr)
                task = export_raw.apply_async(args=[querystr,report_result1,report_result2,report_result3,report_result4,report_result5], countdown=0)  # 'countdown' time delay in second before execute
                task_id = task.id
                ptask_id = task_id.replace('-', '_')

                # download path
                url_download = static('download/'+ bcode + '/raw_' + task_id + '.csv')

                
                context = {'task_id': ptask_id}
                context = context | {'wsh' : wsHypertext}
                context = context | {'url_download': url_download}
                context = {'aqs_version':aqs_version} | context 
                return render(request, 'base/in_progress.html', context)


                # table convert to csv
                response = HttpResponse(content_type='text/csv')
                response['Content-Disposition'] = 'attachment; filename="raw.csv"'
                writer = csv.writer(response)                
                # add table header
                writer.writerow(['Ticket', 'Branch', 'Counter Type', 'Step', 'Start Time', 'Start by', 'Call Time', 'Call by', 'Process Time', 'Process by', 'Done Time', 'Done by', 'No Show Time', 'No Show by', 'Void Time', 'Void by', 'Waiting Time (s)', 'Walking time (s)', 'Process time (s)', 'Total time (s)'])

                for row in table2:

                    starttime = None
                    if row.starttime != None:
                        starttime = funUTCtoLocal(row.starttime, row.branch.timezone).strftime('%Y-%m-%d %H:%M:%S')
                    calltime = None
                    if row.calltime != None:                        
                        calltime = funUTCtoLocal(row.calltime, row.branch.timezone).strftime('%Y-%m-%d %H:%M:%S')
                    processtime = None
                    if row.processtime != None:
                        processtime = funUTCtoLocal(row.processtime, row.branch.timezone).strftime('%Y-%m-%d %H:%M:%S')
                    donetime = None
                    if row.donetime != None:
                        donetime = funUTCtoLocal(row.donetime, row.branch.timezone).strftime('%Y-%m-%d %H:%M:%S')
                    misstime = None
                    if row.misstime != None:
                        misstime = funUTCtoLocal(row.misstime, row.branch.timezone).strftime('%Y-%m-%d %H:%M:%S')
                    voidtime = None
                    if row.voidtime != None:
                        voidtime = funUTCtoLocal(row.voidtime, row.branch.timezone).strftime('%Y-%m-%d %H:%M:%S')

                    writer.writerow([
                                    row.ticket.tickettype + row.ticket.ticketnumber,  
                                    row.branch.bcode,
                                    row.countertype.name,
                                    row.step,
                                    starttime,
                                    row.startuser,
                                    calltime,
                                    row.calluser,
                                    processtime,
                                    row.processuser,
                                    donetime,
                                    row.doneuser,
                                    misstime,
                                    row.missuser,
                                    voidtime,
                                    row.voiduser,
                                    row.waitingperiod,
                                    row.walkingperiod,
                                    row.processingperiod,
                                    row.totalperiod,
                                        ])
                return response


        else:
            context = {
            'localtimezone':localtimezone,
            'result':report_result,
            'table':table100,        
            }
    else:
        messages.error(request, error)
        context = {
        'result':error,
        }
        return redirect('reports')
    context = {'aqs_version':aqs_version} | context 
    return render(request, 'base/r-raw.html', context)

@unauth_user
@allowed_users(allowed_roles=['admin','support','supervisor','manager','reporter'])
def Report_Ticket_Result(request):
    # change code to if request.GET.get('x') != None else ''
    bcode = request.GET.get('branch') if request.GET.get('branch') != None else ''
    # bcode = request.GET['branch']
    s_startdate = request.GET.get('startdate') if request.GET.get('startdate') != None else ''
    # s_startdate = request.GET['startdate']
    s_enddate = request.GET.get('enddate') if request.GET.get('enddate') != None else ''
    # s_enddate = request.GET['enddate']
    ticketformat_id = request.GET.get('ticketformats') if request.GET.get('ticketformats') != None else ''
    # ticketformat_id = request.GET['ticketformats']
    result_task_id = request.GET.get('result') if request.GET.get('result') != None else ''

    error = ''

    if error == '':
        try:
            branch = Branch.objects.get(bcode=bcode)
        except:
            error = 'Error : Branch not found.'
    
    ticketformat = None            
    if error == '':
        if ticketformat_id == '':
            # error = 'Error : Counter Type is blank.'
            pass
        else:
            try:
                ticketformat = TicketFormat.objects.get(id=int(ticketformat_id))
            except:
                error = 'Error : Ticket Format not found.'

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

    if error == '':
        # check enddate - startdate > 200 days
        if (enddate - startdate).days > 200 :
            error = 'Error : Date range do not more then 200 days.'
    
    if error == '':
        report_table = []
        report_result1 = 'Total ticket Report'
        report_result2 = 'Branch:' + branch.name + '(' + branch.bcode + ')'
        report_result3 = 'Start datetime:' + s_startdate
        report_result4 = 'End datetime:' + s_enddate

        if ticketformat == None  :
            report_result5 = 'Ticket Type:All'
        else:
            # report_result = 'Total ticket Report  Branch:' + branch.name + '(' + branch.bcode + ') Start datetime:' + s_startdate + ' End datetime:' + s_enddate + ' Ticket Type:' + ticketformat.ttype
            # report_result = 'Total ticket Report\n' + 'Branch:' + branch.name + '(' + branch.bcode + ')\n' +  'Start datetime:' + s_startdate + '\n' + 'End datetime:' + s_enddate + '\nTicket Type:' + ticketformat.ttype
            report_result5 = 'Ticket Type:' + ticketformat.ttype
        report_result = report_result1 + '\n' + report_result2 + '\n' + report_result3 + '\n' + report_result4 + '\n' + report_result5
     
        if result_task_id == '':
            # run celery task for long process
            localtimezone = pytz.timezone(branch.timezone)


            task = report_ticket.apply_async(args=[branch.pk, ticketformat_id, startdate, enddate], countdown=0)  # 'countdown' time delay in second before execute
            task_id = task.id
            ptask_id = task_id.replace('-', '_')

            # download path
            url_download = ''
            
            
            context = {'task_id': ptask_id}
            context = context | {'wsh' : wsHypertext}
            context = context | {'url_download': url_download}
            context = {'aqs_version':aqs_version} | context 
            return render(request, 'base/in_progress.html', context)
        else :
            # long process is done output result to HTML
            # task id is result_task_id
            task_id = result_task_id.replace('_', '-')
            # print ('task_id', task_id)
            task = AsyncResult(task_id, app=report_ticket)
            status, report_table = task.get()
                      
            if request.method != 'POST':
                localtimezone = pytz.timezone(branch.timezone)
                # if ticketformat == None  :
                #     report_result = 'Total ticket Report\n' + 'Branch:' + branch.name + '(' + branch.bcode + ')\n' +  'Start datetime:' + s_startdate + '\n' + 'End datetime:' + s_enddate + '\nTicket Type:ALL'
                # else:
                #     # report_result = 'Total ticket Report  Branch:' + branch.name + '(' + branch.bcode + ') Start datetime:' + s_startdate + ' End datetime:' + s_enddate + ' Ticket Type:' + ticketformat.ttype
                #     report_result = 'Total ticket Report\n' + 'Branch:' + branch.name + '(' + branch.bcode + ')\n' +  'Start datetime:' + s_startdate + '\n' + 'End datetime:' + s_enddate + '\nTicket Type:' + ticketformat.ttype
               
                # report_result = status
                context = {
                'localtimezone':localtimezone,
                'result':report_result,
                'table':report_table,        
                }
                context = {'aqs_version':aqs_version} | context 
                return render(request, 'base/r-ticket.html', context)
            elif request.method == 'POST':
                # Export and download excel file
                action = request.POST.get('action')
                if action == 'excel':
                    # table convert to csv
                    response = HttpResponse(content_type='text/csv')
                    response['Content-Disposition'] = 'attachment; filename="totalticket.csv"'
                    writer = csv.writer(response)   
                    # add report header
                    writer.writerow([report_result1])
                    writer.writerow([report_result2])
                    writer.writerow([report_result3])
                    writer.writerow([report_result4])
                    writer.writerow([report_result5])

                    # add table header
                    writer.writerow(['Ticket Type', 'Done', 'Miss', 'Total'])
                    for row in report_table:
                        writer.writerow([
                                    row[0], 
                                    row[1],
                                    row[2],
                                    row[3],
                                        ])
                    return response  
    if error == '':
        context = {
        'localtimezone':localtimezone,
        'result':report_result,
        'table':report_table,        
        }
    else:
        messages.error(request, error)
        context = {
        'result':error,
        }
        return redirect('reports')
    context = {'aqs_version':aqs_version} | context 
    return render(request, 'base/r-ticket.html', context)
@unauth_user
@allowed_users(allowed_roles=['admin','support','supervisor','manager','reporter'])
def Report_Staff_Result(request):
    # change code to if request.GET.get('x') != None else ''
    bcode = request.GET.get('branch') if request.GET.get('branch') != None else ''
    bcode = request.GET['branch']
    s_startdate = request.GET['startdate']
    s_enddate = request.GET['enddate']
    user_id = request.GET['users']
    result_task_id = ''
    try:    
        result_task_id = request.GET['result']
    except:
        pass

    error = ''

    if error == '':
        try:
            branch = Branch.objects.get(bcode=bcode)
        except:
            error = 'Error : Branch not found.'
    
    selected_user = None            
    if error == '':
        if user_id == '':
            # error = 'Error : Counter Type is blank.'
            pass
        else:
            try:
                selected_user = User.objects.get(id=int(user_id))
            except:
                error = 'Error : Selected user not found.'
             
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

    if error == '':
        # check enddate - startdate > 200 days
        if (enddate - startdate).days > 200 :
            error = 'Error : Date range do not more then 200 days.'
    
    if error == '':
        localtimezone = pytz.timezone(branch.timezone)

        report_result1 = 'Staff performance report'
        report_result2 = 'Branch:' + branch.name + '(' + branch.bcode + ')'
        report_result3 = 'Start datetime:' + s_startdate
        report_result4 = 'End datetime:' + s_enddate 
        report_result5 = 'User:ALL'
        if selected_user != None  :
            report_result5 ='User:' + selected_user.username
        report_result = report_result1 + '\n' + report_result2 + '\n' + report_result3 + '\n' + report_result4 + '\n' + report_result5
        auth_branchs , auth_userlist, auth_userlist_active, auth_grouplist, auth_profilelist, auth_ticketformats , auth_routes, auth_countertype = auth_data(request.user)
        # convert queryset to string
        querystr_auth_userlist = pickle.dumps(auth_userlist.query)

        if result_task_id == '':
            # run celery task for long process
            localtimezone = pytz.timezone(branch.timezone)


            task = report_staff.apply_async(args=[user_id, querystr_auth_userlist, startdate, enddate], countdown=0)  # 'countdown' time delay in second before execute
            task_id = task.id
            ptask_id = task_id.replace('-', '_')

            # download path
            url_download = ''
            
            
            context = {'task_id': ptask_id}
            context = context | {'wsh' : wsHypertext}
            context = context | {'url_download': url_download}
            context = {'aqs_version':aqs_version} | context 
            return render(request, 'base/in_progress.html', context)
        else :
            # long process is done output result to HTML

            # task id is result_task_id
            task_id = result_task_id.replace('_', '-')
            # print ('task_id', task_id)
            task = AsyncResult(task_id, app=report_ticket)
            status, report_table = task.get()

            # terminal task
            # task.revoke()
            
            # report_ticket.control.revoke(task_id, terminate=True)
           
            if request.method != 'POST':

                # report_result = status
                context = {
                'localtimezone':localtimezone,
                'result':report_result,
                'table':report_table,        
                }
                context = {'aqs_version':aqs_version} | context 
                return render(request, 'base/r-staff.html', context)

            elif request.method == 'POST':
                # Export and download excel file
                action = request.POST.get('action')
                if action == 'excel':
                    # table convert to csv
                    response = HttpResponse(content_type='text/csv')
                    response['Content-Disposition'] = 'attachment; filename="staffperf.csv"'
                    writer = csv.writer(response)   
                    # add report header
                    writer.writerow([report_result1])
                    writer.writerow([report_result2])
                    writer.writerow([report_result3])
                    writer.writerow([report_result4])
                    writer.writerow([report_result5])

                    # add table header
                    writer.writerow(['User', 'Name', 'Logon time', 'Ready time', 'Waiting time', 'Walking time', 'Process time', 'ACW', 'AUX'])
                    for row in report_table:
                        writer.writerow([
                                    row[0], 
                                    row[1],
                                    row[2],
                                    row[3],
                                    row[4], 
                                    row[5],
                                    row[6],
                                    row[7],                                    
                                    row[8],                                    
                                        ])
                    return response  

        '''

        if user == None  :
            auth_branchs , auth_userlist, auth_userlist_active, auth_grouplist, auth_profilelist, auth_ticketformats , auth_routes, auth_countertype = auth_data(request.user)
          
            for user in auth_userlist:
                userlogobj = UserStatusLog.objects.filter(
                    Q(starttime__range=[startdate,enddate]),
                    Q(user=user),
                    ~Q(starttime = None),
                    ~Q(endtime = None),
                )
                login = 0
                ready = 0
                waiting = 0
                walking = 0
                process = 0
                acw = 0
                aux =0
                for ul in userlogobj:
                    seconds = (ul.endtime - ul.starttime).seconds
                    if ul.status == 'login':
                        login = login + seconds
                    elif ul.status == 'ready':
                        ready = ready + seconds
                    elif ul.status == 'waiting':
                        waiting = waiting + seconds
                    elif ul.status == 'walking':
                        walking = walking + seconds
                    elif ul.status == 'processing':
                        process = process + seconds
                    elif ul.status == 'ACW':
                        acw = acw + seconds
                    elif ul.status == 'AUX':
                        aux = aux + seconds
                # convert all to '00:00:00' string
                login_s = str(timedelta(seconds=login))
                ready_s = str(timedelta(seconds=ready))
                waiting_s = str(timedelta(seconds=waiting))
                walking_s = str(timedelta(seconds=walking))
                process_s = str(timedelta(seconds=process))
                acw_s = str(timedelta(seconds=acw))
                aux_s = str(timedelta(seconds=aux))

                # print('AUX seconds:' + str(aux) + ' AUX string:' + aux_s)
                # print('Login seconds:' + str(login) + ' Login string:' + login_s)
                # print('Ready seconds:' + str(ready) + ' Ready string:' + ready_s)
                # print('Waiting seconds:' + str(waiting) + ' Waiting string:' + waiting_s)
                # print('Walking seconds:' + str(walking) + ' Walking string:' + walking_s)
                # print('Process seconds:' + str(process) + ' Process string:' + process_s)
                # print('ACW seconds:' + str(acw) + ' ACW string:' + acw_s)
                # print('AUX seconds:' + str(aux) + ' AUX string:' + aux_s)

                report_table.append([user.username, user.first_name + ' ' + user.last_name, login_s, ready_s, waiting_s, walking_s, process_s, acw_s, aux_s])


        else:
            userlogobj = UserStatusLog.objects.filter(
                Q(starttime__range=[startdate,enddate]),
                Q(user=user),
                ~Q(starttime = None),
                ~Q(endtime = None),
            )
            login = 0
            ready = 0
            waiting = 0
            walking = 0
            process = 0
            acw = 0
            aux =0
            for ul in userlogobj:
                seconds = (ul.endtime - ul.starttime).seconds
                if ul.status == 'login':
                    login = login + seconds
                elif ul.status == 'ready':
                    ready = ready + seconds
                elif ul.status == 'waiting':
                    waiting = waiting + seconds
                elif ul.status == 'walking':
                    walking = walking + seconds
                elif ul.status == 'processing':
                    process = process + seconds
                elif ul.status == 'ACW':
                    acw = acw + seconds
                elif ul.status == 'AUX':
                    aux = aux + seconds
            # convert all to '00:00:00' string
            login_s = str(timedelta(seconds=login))
            ready_s = str(timedelta(seconds=ready))
            waiting_s = str(timedelta(seconds=waiting))
            walking_s = str(timedelta(seconds=walking))
            process_s = str(timedelta(seconds=process))
            acw_s = str(timedelta(seconds=acw))
            aux_s = str(timedelta(seconds=aux))

            # print('AUX seconds:' + str(aux) + ' AUX string:' + aux_s)
            # print('Login seconds:' + str(login) + ' Login string:' + login_s)
            # print('Ready seconds:' + str(ready) + ' Ready string:' + ready_s)
            # print('Waiting seconds:' + str(waiting) + ' Waiting string:' + waiting_s)
            # print('Walking seconds:' + str(walking) + ' Walking string:' + walking_s)
            # print('Process seconds:' + str(process) + ' Process string:' + process_s)
            # print('ACW seconds:' + str(acw) + ' ACW string:' + acw_s)
            # print('AUX seconds:' + str(aux) + ' AUX string:' + aux_s)

            report_table.append([user.username, user.first_name + ' ' + user.last_name, login_s, ready_s, waiting_s, walking_s, process_s, acw_s, aux_s])

        '''
        

    if error == '':
        context = {
        'localtimezone':localtimezone,
        'result':report_result,
        'table':report_table,        
        }
    else:
        messages.error(request, error)
        context = {
        'result':error,
        }
        return redirect('reports')
    context = {'aqs_version':aqs_version} | context 
    return render(request, 'base/r-staff.html', context)

@unauth_user
@allowed_users(allowed_roles=['admin','support','supervisor','manager','reporter'])
def Reports(request):

    auth_branchs , auth_userlist, auth_userlist_active, auth_grouplist, auth_profilelist, auth_ticketformats , auth_routes, auth_countertype = auth_data(request.user)
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
    context = {'aqs_version':aqs_version} | context 
    return render(request, 'base/r-main.html', context)

@unauth_user
@allowed_users(allowed_roles=['admin','support','supervisor','manager','reporter'])
def SuperVisorView(request, pk):

    branch = Branch.objects.get(id=pk)    
    countertypes = CounterType.objects.filter(Q(branch=branch))
    
    qlists = []    
    counterstatus =[] 
    for ct in countertypes :
        t = TicketTemp.objects.filter( Q(branch=branch) & Q(locked=False) & Q(status='waiting') & Q(countertype=ct)).order_by('tickettime')
        qlists.append(t)

        cs = CounterStatus.objects.filter(Q(countertype=ct)).order_by('countertype', 'counternumber',)
        counterstatus.append(cs)
        
    # qlists[0] = Ticket.objects.filter( Q(branch=branch) & Q(locked=False) & Q(status='waiting') & Q(countertype=countertypes[0]))
    # qlists[1] = Ticket.objects.filter( Q(branch=branch) & Q(locked=False) & Q(status='waiting') & Q(countertype=countertypes[1]))
    localtimezone = pytz.timezone(branch.timezone)



    donelist = TicketTemp.objects.filter( Q(branch=branch) & Q(locked=False) & Q(status='done')).order_by('tickettime')
    
    misslist = TicketTemp.objects.filter( Q(branch=branch) & Q(locked=False) & (Q(status='miss') | Q(status='void'))  ).order_by('tickettime')

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
    context = {'aqs_version':aqs_version} | context 
    return render(request, 'base/supervisor.html', context)


@unauth_user
@allowed_users(allowed_roles=['admin','support','supervisor','manager','reporter'])
def SuperVisorListView(request):  
    auth_branchs , auth_userlist, auth_userlist_active, auth_grouplist, auth_profilelist, auth_ticketformats , auth_routes, auth_countertype = auth_data(request.user)
 
    # users = User.objects.exclude( Q(is_superuser=True) | Q(groups__name='api'))
    #users = User.objects.exclude( Q(is_superuser=True) )
    # profiles = UserProfile.objects.all()
    # branchs = Branch.objects.all()    
    # ticketformats = TicketFormat.objects.all()
    # routes = TicketRoute.objects.all()
    # profiles = UserProfile.objects.filter(Q(user=users.user))
    #profiles = users.userprofile_set.all()
    
    context = {'users':auth_userlist, 'profiles':auth_profilelist, 'branchs':auth_branchs, 'ticketformats':auth_ticketformats, 'routes':auth_routes}
    context = {'aqs_version':aqs_version} | context 
    return render(request, 'base/supervisors.html', context)

@unauth_user
@allowed_users(allowed_roles=['admin','support','supervisor','manager'])
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
    context = {'form':form}

    context = {'aqs_version':aqs_version} | context 
    return render(request, 'base/routenew.html', context)

@unauth_user
@allowed_users(allowed_roles=['admin','support','supervisor','manager'])
def TicketRouteDelView(request, pk):
 
    route = TicketRoute.objects.get(id=pk)
  
    if request.method =='POST':
        route.delete()
        messages.success(request, 'Ticket Route was successfully Deleted!')
        return redirect('routesummary')
    context = {'obj':route}

    context = {'aqs_version':aqs_version} | context 
    return render(request, 'base/delete.html', context)

@unauth_user
@allowed_users(allowed_roles=['admin','support','supervisor','manager'])
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
    context = {'aqs_version':aqs_version} | context 
    return render(request, 'base/route-update.html', context)


@unauth_user
@allowed_users(allowed_roles=['admin','support','supervisor','manager'])
def TicketRouteSummaryView(request):  
    auth_branchs , auth_userlist, auth_userlist_active, auth_grouplist, auth_profilelist, auth_ticketformats , auth_routes, auth_countertype = auth_data(request.user)
 
    # users = User.objects.exclude( Q(is_superuser=True) | Q(groups__name='api'))
    # branchs = Branch.objects.all()
    # ticketformats = TicketFormat.objects.all().order_by('branch','ttype')
    # routes = TicketRoute.objects.all().order_by('branch','tickettype','step')

    context = {'users':auth_userlist, 'branchs':auth_branchs, 'ticketformats':auth_ticketformats, 'routes':auth_routes}
    context = {'aqs_version':aqs_version} | context 
    return render(request, 'base/routes.html', context)

@unauth_user
@allowed_users(allowed_roles=['admin','support','supervisor','manager'])
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
    context = {'form':form}
    context = {'aqs_version':aqs_version} | context 
    return render(request, 'base/tfnew.html', context)

@unauth_user
@allowed_users(allowed_roles=['admin','support','supervisor','manager'])
def TicketFormatDelView(request, pk):
 
    ticketformat = TicketFormat.objects.get(id=pk)
  
    if request.method =='POST':
        ticketformat.delete()       
        messages.success(request, 'Ticket Format was successfully deleted!') 
        return redirect('tfsummary')
    context = {'obj':ticketformat}
    context = {'aqs_version':aqs_version} | context 
    return render(request, 'base/delete.html', context)

@unauth_user
@allowed_users(allowed_roles=['admin','support','supervisor','manager'])
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
    context = {'aqs_version':aqs_version} | context 
    return render(request, 'base/tf-update.html', context)

@unauth_user
@allowed_users(allowed_roles=['admin','support','supervisor','manager'])
def TicketFormatSummaryView(request):
    auth_branchs , auth_userlist, auth_userlist_active, auth_grouplist, auth_profilelist, auth_ticketformats , auth_routes, auth_countertype = auth_data(request.user)
  
    # users = User.objects.exclude( Q(is_superuser=True) | Q(groups__name='api'))
    # branchs = Branch.objects.all()
    # ticketformats = TicketFormat.objects.all().order_by('branch','ttype')
    # routes = TicketRoute.objects.all()
    context = {'users':auth_userlist, 'branchs':auth_branchs, 'ticketformats':auth_ticketformats, 'routes':auth_routes}
    context = {'aqs_version':aqs_version} | context 
    return render(request, 'base/tfs.html', context)

@unauth_user
@allowed_users(allowed_roles=['admin','support','supervisor','manager','reporter'])
def Settings_Save(request, pk):
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
        datetime_now = timezone.now()
        sch_shutdown(branch, datetime_now)

        countertypes = CounterType.objects.filter(Q(branch=branch))
        for ct in countertypes:
            ct.displayscrollingtext = request.GET[branch.bcode + '-' + ct.name]
            ct.save()
        messages.success(request, 'Branch settings was successfully changed!')
        result = ''
    else :
        messages.error(request, result)
    
    # context = {'result':result}
    return redirect('settingssummary')
    # return render(request, 'base/branchresult.html', context)

@unauth_user
@allowed_users(allowed_roles=['admin','support','supervisor','manager','reporter'])
def SettingsUpdateView(request, pk):
    branch = Branch.objects.get(id=pk)
    bcode = branch.bcode
    branchname = branch.name
    countertypes = CounterType.objects.filter(Q(branch=branch))
    subend = branch.subend
    subend = funUTCtoLocal(subend, branch.timezone).strftime('%Y-%m-%d %H:%M:%S')
    subscribe = branch.subscribe
    # auth_branchs , auth_userlist, auth_userlist_active, auth_grouplist, auth_profilelist, auth_ticketformats , auth_routes, auth_countertype = auth_data(request.user)

    userright = 'counter'
    if request.user.is_superuser == True :
        userright = 'admin'
    elif request.user.groups.filter(name='admin').exists() == True :
        userright = 'admin'


    if request.method == 'POST':
        branchsettingsform = BranchSettingsForm_Admin(request.POST, instance=branch, prefix='branchsettingsform')
        error = ''
        error, bsf = checkbranchsettingsform(branchsettingsform)
        if error == '':
            try:
                bsf.save()
                datetime_now = timezone.now()
                sch_shutdown(branch, datetime_now)
            except:
                error = 'An error occurcd during updating Branch settings'
        if error == '':
            countertypes = CounterType.objects.filter(Q(branch=branch))
            for ct in countertypes:
                ct.displayscrollingtext = request.POST.get(branch.bcode + '-' + ct.name)
                ct.save()
        if error == '':
            messages.error(request, error )
            messages.success(request, 'Branch settings was successfully updated!')
            return redirect('settingssummary')
        else:
            messages.error(request, error )
    else:
        branchsettingsform = BranchSettingsForm_Admin(instance=branch, prefix='branchsettingsform')
        
    context = {'aqs_version':aqs_version, 'bcode':bcode,
               'branchname':branchname , 'countertypes':countertypes, 
               'branchsettingsform':branchsettingsform, 
               'subend':subend , 'subscribe':subscribe}
    return render(request, 'base/settings-update.html', context)

@unauth_user
@allowed_users(allowed_roles=['admin','support','supervisor','manager','reporter'])
def SettingsSummaryView(request):  
    # users = User.objects.exclude( Q(is_superuser=True) | Q(groups__name='api'))
    #users = User.objects.exclude( Q(is_superuser=True) )
    # profiles = UserProfile.objects.all()
    # branchs = Branch.objects.all()    
    # ticketformats = TicketFormat.objects.all()
    # routes = TicketRoute.objects.all()
    # profiles = UserProfile.objects.filter(Q(user=users.user))
    #profiles = users.userprofile_set.all()
    auth_branchs , auth_userlist, auth_userlist_active, auth_grouplist, auth_profilelist, auth_ticketformats , auth_routes, auth_countertype = auth_data(request.user)


    context = {'users':auth_userlist, 'profiles':auth_profilelist, 'branchs':auth_branchs, 'ticketformats':auth_ticketformats, 'routes':auth_routes}
    context = {'aqs_version':aqs_version} | context 
    return render(request, 'base/settings.html', context)

@unauth_user
def homeView(request):
    
    auth_branchs , auth_userlist, auth_userlist_active, auth_grouplist, auth_profilelist, auth_ticketformats , auth_routes, auth_countertype = auth_data(request.user)

    # users = User.objects.exclude( Q(is_superuser=True) | Q(groups__name='api'))
    # branchs = Branch.objects.all()
    # ticketformats = TicketFormat.objects.all()
    # routes = TicketRoute.objects.all()
    # users = User.objects.exclude(is_superuser=True)





    context =  {'users':auth_userlist , 'users_active':auth_userlist_active, 'branchs':auth_branchs, 'ticketformats':auth_ticketformats, 'routes':auth_routes}
    context = {'aqs_version':aqs_version} | context 
    return render(request, 'base/home.html', context)

@unauth_user
@allowed_users(allowed_roles=['admin','support','supervisor','manager'])
def UserSummaryView(request):     
    auth_branchs , auth_userlist, auth_userlist_active, auth_grouplist, auth_profilelist, auth_ticketformats , auth_routes, auth_countertype = auth_data(request.user)
 
    context = {'users':auth_userlist, 'users_active':auth_userlist_active, 'profiles':auth_profilelist, 'branchs':auth_branchs, 'ticketformats':auth_ticketformats, 'routes':auth_routes}
    context = {'aqs_version':aqs_version} | context 
    return render(request, 'base/user.html', context)

@unauth_user
@allowed_users(allowed_roles=['admin','support','supervisor','manager'])
def UserSummaryListView(request):
    global sort_direction    

    q = request.GET.get('q') if request.GET.get('q') != None else ''
    q_active = request.GET.get('qactive') if request.GET.get('qactive') != None else 'all'
    q_branch = request.GET.get('qbranch') if request.GET.get('qbranch') != None else 'all'
    q_tt = request.GET.get('qtt') if request.GET.get('qtt') != None else 'all'
    q_group = request.GET.get('qgroup') if request.GET.get('qgroup') != None else 'all'
    q_sort = request.GET.get('sort') if request.GET.get('sort') != None else ''

    auth_branchs , auth_userlist, auth_userlist_active, auth_grouplist, auth_profilelist, auth_ticketformats , auth_routes, auth_countertype = auth_data(request.user)

    result_userlist = auth_userlist
    # print(result_userlist.count())

    # auth_ticketformats keep ttype is not repeated
    auth_ticketformats = auth_ticketformats.order_by('ttype')
    for tf in auth_ticketformats:
        for tf2 in auth_ticketformats:
            if tf != tf2:
                if tf.ttype == tf2.ttype:
                    auth_ticketformats = auth_ticketformats.exclude(id=tf.id)
 
    if q != '':
        result_userlist = result_userlist.filter(Q(username__icontains=q) | Q(first_name__icontains=q) | Q(last_name__icontains=q) | Q(email__icontains=q) 
                                             | Q(userprofile__staffnumber__icontains=q)
                                             | Q(userprofile__mobilephone__icontains=q)
                                             )
    
    if q_active != '' and q_active != 'all':
        active_bool = True
        if q_active == 'inactive':
            active_bool = False
        result_userlist = result_userlist.filter(Q(is_active=active_bool))
    
    if q_branch == 'none':
        result_userlist = result_userlist.filter(Q(userprofile__branchs=None))
    elif q_branch != '' and q_branch != 'all':
        result_userlist = result_userlist.filter(Q(userprofile__branchs__bcode=q_branch))

    if q_group == 'none':
        result_userlist = result_userlist.filter(Q(groups=None))  
    elif q_group != '' and q_group != 'all':
        result_userlist = result_userlist.filter(Q(groups__name__icontains=q_group))        
  
    if q_tt == 'none':
        result_userlist = result_userlist.filter(Q(userprofile__tickettype=''))
    elif q_tt != '' and q_tt != 'all':
        result_userlist = result_userlist.filter(Q(userprofile__tickettype__icontains=q_tt))

    direct = ''
    if q_sort != '':
        # find out the sort_list
        try:
            direct = sort_direction[q_sort]
        except:
            direct = ''
            sort_direction[q_sort] = ''
        if direct == '':
            sort_direction[q_sort] = '-'
        elif direct == '-':
            sort_direction[q_sort] = ''

    if q_sort == 'username':
        result_userlist = result_userlist.order_by(direct + 'username')
    elif q_sort == 'active':
        result_userlist = result_userlist.order_by(direct + 'is_active')
    elif q_sort == 'fname':
        result_userlist = result_userlist.order_by(direct + 'first_name')
    elif q_sort == 'lname':
        result_userlist = result_userlist.order_by(direct + 'last_name')
    elif q_sort == 'email':
        result_userlist = result_userlist.order_by(direct + 'email')
    elif q_sort == 'groups':
        result_userlist = result_userlist.order_by(direct + 'groups__name')
    elif q_sort == 'branchs':
        result_userlist = result_userlist.order_by(direct + 'userprofile__branchs__bcode')
    elif q_sort == 'tt':
        result_userlist = result_userlist.order_by(direct + 'userprofile__tickettype')
    elif q_sort == 'qpriority':
        result_userlist = result_userlist.order_by(direct + 'userprofile__queuepriority')
    elif q_sort == 'sno':
        result_userlist = result_userlist.order_by(direct + 'userprofile__staffnumber')
    elif q_sort == 'phone':
        result_userlist = result_userlist.order_by(direct + 'userprofile__mobilephone')

    print(auth_grouplist)
    print(auth_branchs)
    context = {'users':auth_userlist, 'users_active':auth_userlist_active, 'profiles':auth_profilelist, 'auth_grouplist':auth_grouplist, 'branchs':auth_branchs, 'ticketformats':auth_ticketformats, 'routes':auth_routes}
    context = context | {'q':q}
    context = context | {'qactive':q_active}
    context = context | {'qbranch':q_branch}
    context = context | {'qtt':q_tt}
    context = context | {'qgroup':q_group}
    context = context | {'result_users':result_userlist}
    
    context = {'aqs_version':aqs_version} | context 
    return render(request, 'base/user_details.html', context)

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
    context = {'aqs_version':aqs_version} | context 
    return render(request, 'base/login_register.html', context)
    
@unauth_user
@allowed_users(allowed_roles=['admin','support','supervisor','manager'])
def UserUpdateView(request, pk):

    auth_branchs , auth_userlist, auth_userlist_active, auth_grouplist, auth_profilelist, auth_ticketformats , auth_routes, auth_countertype = auth_data(request.user)


    user = User.objects.get(id=pk)
    userp = UserProfile.objects.get(user__exact=user)
    error = ''
    # if request.user.is_superuser == True or request.user.groups.filter(name='support').exists() == True or request.user.groups.filter(name='admin').exists() == True:
    #     auth_branchs = Branch.objects.all()
    # else :
    #     auth_userp = UserProfile.objects.get(user__exact=request.user)
    #     auth_branchs = auth_userp.branchs.all()

    # get all ticketformat but not ttype is repeated 
    ticketformat = TicketFormat.objects.all().order_by('ttype')
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
    
    # for tt in ticketformat2:
    #     # check if userp.branchs is not in tt.branchs
    #     if tt.branch not in userp.branchs.all():
    #         ticketformat2 = ticketformat2.exclude(id=tt.id)

    # add column for checked or unchecked to ticketformat2
    if userp.tickettype != None:
        listusertt = userp.tickettype.split(',')
    else:
        sTemp = ''
        listusertt = sTemp.split(',')
    for tt in ticketformat2:
        if tt.ttype in listusertt:
            tt.checked = 'checked'
        else:
            tt.checked = 'unchecked'
        tt.save()

    if request.method != 'POST':
        # if request.user.is_superuser == True :
        #     userform = UserFormSuper(instance=user, prefix='uform')
        if user == request.user:
            userform = UserFormAdminSelf(instance=user, prefix='uform')
        # elif request.user.groups.filter(name='admin').exists() == True :
        #     userform = UserFormAdmin(instance=user, prefix='uform')
        # elif request.user.groups.filter(name='support').exists() == True :
        #     userform = UserFormSupport(instance=user, prefix='uform')
        # elif request.user.groups.filter(name='manager').exists() == True :
        #     userform = UserFormManager(instance=user, prefix='uform')
        else :
            userform = UserForm(instance=user, prefix='uform', auth_grouplist=auth_grouplist)
        profileform = UserProfileForm(instance=userp, prefix='pform', auth_branchs=auth_branchs)
        print(auth_branchs)
    elif request.method == 'POST':
        # if request.user.is_superuser == True :
        #     userform = UserFormSuper(request.POST, instance=user, prefix='uform')
        if user == request.user:
            userform = UserFormAdminSelf(request.POST, instance=user, prefix='uform')        
        # elif request.user.groups.filter(name='admin').exists() == True :
        #     userform = UserFormAdmin(request.POST, instance=user, prefix='uform')
        # elif request.user.groups.filter(name='support').exists() == True :
        #     userform = UserFormSupport(request.POST, instance=user, prefix='uform')
        # elif request.user.groups.filter(name='manager').exists() == True :
        #     userform = UserFormManager(request.POST, instance=user, prefix='uform')
        else :
            userform = UserForm(request.POST, instance=user, prefix='uform', auth_grouplist=auth_grouplist)

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
            # print ('new_tt = ' + new_tt)
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

    context =  {'userform':userform , 'profileform':profileform, 'user':user, 'userp':userp,'ticketformat':ticketformat2,'userptt':listusertt, }
    context = {'aqs_version':aqs_version} | context 
    return render(request, 'base/user-update.html', context)

@unauth_user
@allowed_users(allowed_roles=['admin','support','supervisor','manager'])
def UserUpdateTTView(request, pk):
    userp = UserProfile.objects.get(id=pk)
    # get all ticketformat but not ttype is repeated 
    ticketformat = TicketFormat.objects.all().order_by('ttype')
    ticketformat2 = TicketFormat.objects.all().order_by('ttype')
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
    ticketformat2 = ticketformat2.order_by('ttype')
    context =  {'userp':userp, 'ticketformat':ticketformat2, }
    context = {'aqs_version':aqs_version} | context 
    return render(request, 'base/user-update-tickettype.html', context)

@unauth_user
@allowed_users(allowed_roles=['admin','support','supervisor','manager'])
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
            userp = UserProfile.objects.create(user=user)
                   
            #login(request, user)        
            # context =  {'user':user , 'userp':userp}
            # return render(request, 'base/usernew2.html' + user.id + '/', context)
            pk = user.id
            return redirect('new-user2', pk=pk)
        else:
            # messages.error(request, 'An error occurcd during registration')
            # get all error message from form.errors
            for field, items in form.errors.items():
                for item in items:
                    messages.error(request, item)
            
    context = {'form':form}
    context = {'aqs_version':aqs_version} | context 
    return render(request, 'base/usernew.html', context)

@unauth_user
@allowed_users(allowed_roles=['admin','support','supervisor','manager'])
def UserNewView2(request, pk):
    user = User.objects.get(id=pk)
    userp = UserProfile.objects.get(user__exact=user)

    # check user group auth
    auth_branchs , auth_userlist, auth_userlist_active, auth_grouplist, auth_profilelist, auth_ticketformats , auth_routes, auth_countertype = auth_data(request.user)

    if request.method == 'POST':
        if request.user.is_superuser == True :
            userform = UserFormSuper(request.POST, instance=user, prefix='uform')
        elif user == request.user:
            userform = UserFormAdminSelf(request.POST, instance=user, prefix='uform')        
        elif request.user.groups.filter(name='admin').exists() == True :
            userform = UserFormAdmin(request.POST, instance=user, prefix='uform')            
        elif request.user.groups.filter(name='support').exists() == True :
            userform = UserFormSupport(request.POST, instance=user, prefix='uform')
        elif request.user.groups.filter(name='manager').exists() == True :
            userform = UserFormManager(request.POST, instance=user, prefix='uform')
        else :
            userform = UserForm(request.POST, instance=user, prefix='uform')
        
        profileform = UserProfileForm(request.POST, instance=userp, prefix='pform', auth_branchs=auth_branchs)
        if (userform.is_valid() & profileform.is_valid()):
            profileform.save() 
            userform.save()
                                   
            return redirect('new-user3', pk=pk)
        else:
            # messages.error(request, 'An error occurcd during registration')
            # get all error message from form.errors
            for field, items in profileform.errors.items():
                for item in items:
                    messages.error(request, item + ' ' + field)
    else:
        if request.user.is_superuser == True :
            userform = UserFormSuper(instance=user, prefix='uform')
        elif user == request.user:
            userform = UserFormAdminSelf(instance=user, prefix='uform')
        elif request.user.groups.filter(name='admin').exists() == True :
            userform = UserFormAdmin(instance=user, prefix='uform')
        elif request.user.groups.filter(name='support').exists() == True :
            userform = UserFormSupport(instance=user, prefix='uform')
        elif request.user.groups.filter(name='manager').exists() == True :
            userform = UserFormManager(instance=user, prefix='uform')
        else :
            userform = UserForm(instance=user, prefix='uform')

        profileform = UserProfileForm(instance=userp, prefix='pform', auth_branchs=auth_branchs)
    context =  {'user':user , 'userp':userp, 'userform':userform, 'profileform':profileform, 'auth_grouplist':auth_grouplist}
    context = {'aqs_version':aqs_version} | context 
    return render(request, 'base/usernew2.html', context)

@unauth_user
@allowed_users(allowed_roles=['admin','support','supervisor','manager'])
def UserNewView3(request, pk):
    user = User.objects.get(id=pk)
    userp = UserProfile.objects.get(user__exact=user)

    # check user group auth
    auth_branchs , auth_userlist, auth_userlist_active, auth_grouplist, auth_profilelist, auth_ticketformats , auth_routes, auth_countertype = auth_data(request.user)


    ticketformat = TicketFormat.objects.all().order_by('ttype')
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
    


    # add column for checked or unchecked to ticketformat2
    if userp.tickettype != None:
        listusertt = userp.tickettype.split(',')
    else:
        sTemp = ''
        listusertt = sTemp.split(',')
    for tt in ticketformat2:
        if tt.ttype in listusertt:
            tt.checked = 'checked'
        else:
            tt.checked = 'unchecked'
        tt.save()


    if request.method == 'POST':
        profileform = UserProfileForm(request.POST, instance=userp, prefix='pform', auth_branchs=auth_branchs)
        newtickettypeform = newTicketTypeForm(request.POST)

        if (profileform.is_valid() & newtickettypeform.is_valid()):
            profileform_temp = profileform.save(commit=False)
            # get data from html, and update to profileform_temp
            new_tt = newtickettypeform['new_tickettype'].value()
            # print ('new_tt = ' + new_tt)
            if new_tt == '<No ticket type>':
                new_tt = ''
            profileform_temp.tickettype = new_tt
            profileform.save()
            profileform_temp.save()
            messages.success(request, 'New User successfully')            
            return redirect('update-user', pk=pk)

        else:
            # messages.error(request, 'An error occurcd during registration')
            # get all error message from form.errors
            for field, items in profileform.errors.items():
                for item in items:
                    messages.error(request, item + ' ' + field)
    else:
        profileform = UserProfileForm(instance=userp, prefix='pform', auth_branchs=auth_branchs)
    context =  {'profileform':profileform, 'user':user, 'userp':userp,'ticketformat':ticketformat2,'userptt':listusertt, }
    context = {'aqs_version':aqs_version} | context 
    return render(request, 'base/usernew3.html', context)




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
    context = {'form': form}
    context = {'aqs_version':aqs_version} | context 
    return render(request, 'base/changepassword.html', context)

@unauth_user
@allowed_users(allowed_roles=['admin','support','supervisor','manager'])
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
    context = {'obj':user}
    context = {'aqs_version':aqs_version} | context  
    return render(request, 'base/delete.html', context)

@unauth_user
@allowed_users(allowed_roles=['admin','support','supervisor','manager'])
def UserResetView(request, pk):
    user = User.objects.get(id=pk)

    if request.user == user :
        messages.error(request, 'You can not reset password yourself!')
        return redirect('usersummary')   

    # check user group auth
    auth_branchs , auth_userlist, auth_userlist_active, auth_grouplist, auth_profilelist, auth_ticketformats , auth_routes, auth_countertype = auth_data(request.user)
    if user in auth_userlist :
        # print('Request user:' + request.user.username)
        # for iuser in auth_userlist :
        #     str_g = ''
        #     for ig in iuser.groups.all() :
        #         str_g = str_g + ig.name + ','
        #     print('Auth list:' + str_g + ' ' + iuser.username )
        pass
    else:
        messages.error(request, 'You are not authorized to reset this user.')
        return redirect('usersummary') 
    if request.method =='POST':
        form = resetForm(request.POST)
        new_pw = form['new_password1'].value()
        password_hash = make_password(new_pw)
        user.password = password_hash
        user.save()

        messages.success(request, 'Reset password successfully.')
        return redirect('usersummary')
    context = {'obj':user}
    context = {'aqs_version':aqs_version} | context 
    return render(request, 'base/reset.html', context)


def MenuView(request):

    auth_branchs , auth_userlist, auth_userlist_active, auth_grouplist, auth_profilelist, auth_ticketformats , auth_routes, auth_countertype = auth_data(request.user)
        
    context =  {'users':auth_userlist , 'branchs':auth_branchs, 'ticketformats':auth_ticketformats, 'routes':auth_routes}
    context = {'aqs_version':aqs_version} | context 
    return render(request, 'base/m-menu.html', context)

    # users = User.objects.exclude( Q(is_superuser=True) | Q(groups__name='api'))
    # branchs = Branch.objects.all()
    # ticketformats = TicketFormat.objects.all().order_by('branch','ttype')
    # routes = TicketRoute.objects.all()
    
    # adminuser = '0'
    # reportuser = '0'
    # for group in request.user.groups.all() :
    #     if group.name == 'admin':
    #         adminuser = '1'
    #         reportuser = '1'
    #     elif group.name == 'report':
    #         reportuser = '1'
    # if request.user.is_superuser :
    #     adminuser = '1'
    #     reportuser = '1'

    # context = {'users':users, 'branchs':branchs, 'ticketformats':ticketformats, 'routes':routes, 'admin':adminuser, 'report':reportuser}
    # return render (request, 'base/m-menu.html', context)

def auth_data(user):

    if user.is_superuser == True :
        auth_profilelist = UserProfile.objects.all()
        auth_userlist = User.objects.all()
        auth_grouplist = Group.objects.all()
        auth_userlist_active = User.objects.filter(Q(is_active=True))
        # auth_userlist_active = User.objects.filter(Q(is_active=True)).exclude(Q(groups__name='web'))
        auth_branchs = Branch.objects.all()
        auth_ticketformats = TicketFormat.objects.all().order_by('branch','ttype')
        auth_routes = TicketRoute.objects.all().order_by('branch','countertype', 'tickettype', 'step')
        auth_countertype = CounterType.objects.all()
    elif user.groups.filter(name='admin').exists() == True:
        auth_profilelist = UserProfile.objects.all()
        auth_userlist = User.objects.all().exclude(Q(is_superuser=True))
        auth_grouplist = Group.objects.all()
        auth_userlist_active = User.objects.filter(Q(is_active=True))
        # auth_userlist_active = User.objects.filter(Q(is_active=True)).exclude(Q(groups__name='web'))
        auth_branchs = Branch.objects.all()
        auth_ticketformats = TicketFormat.objects.all().order_by('branch','ttype')
        auth_routes = TicketRoute.objects.all().order_by('branch','countertype', 'tickettype', 'step')
        auth_countertype = CounterType.objects.all()
        '''
        elif user.groups.filter(name='admin').exists() == True or user.groups.filter(name='support').exists() == True:
            profiles = UserProfile.objects.all()
            auth_branchs = Branch.objects.all()

            # profid_list = []
            # userid_list = []
            # for prof in profiles :
            #     not_auth = False
            #     for b in prof.branchs.all():
            #         if (b in auth_branchs) == True :
            #             pass                
            #         else :
            #             not_auth = True
            #     if not_auth == False :
            #         if prof.user.is_superuser == False :
            #             if ('api' in prof.user.groups.all()) == False :
            #                 if ('web' in prof.user.groups.all()) == False :
            #                     profid_list.append(prof.id)
            #                     userid_list.append(prof.user.id)
                            
            # rewrote by below
            # userid_list only include user.group = frontline,  manager
            # profid_list only include user.group = frontline,  manager
            profid_list = []
            userid_list = []
            auth_grouplist = []
            if user.groups.filter(name='admin').exists() == True :
                auth_grouplist.append('admin')
                auth_grouplist.append('support')
                auth_grouplist.append('manager')
                auth_grouplist.append('frontline')
            elif user.groups.filter(name='support').exists() == True :
                auth_grouplist.append('support')
                auth_grouplist.append('manager')
                auth_grouplist.append('frontline')
            elif user.groups.filter(name='manager').exists() == True :
                auth_grouplist.append('manager')
                auth_grouplist.append('frontline')
            
            for prof in profiles :
                not_auth = False
                for b in prof.branchs.all():
                    if (b in auth_branchs) == True :
                        pass                
                    else :
                        not_auth = True
                if not_auth == False :
                    if prof.user.is_superuser == False :
                        for usergroup in prof.user.groups.all() :
                            if (usergroup.name in auth_grouplist) == True :                   
                                profid_list.append(prof.id)
                                userid_list.append(prof.user.id)
                                break



            auth_userlist = User.objects.filter(id__in=userid_list)
            auth_profilelist = UserProfile.objects.filter(id__in=profid_list)
            auth_ticketformats = TicketFormat.objects.filter(branch__in=auth_branchs).order_by('branch','ttype')
            auth_routes = TicketRoute.objects.filter(branch__in=auth_branchs).order_by('branch','countertype', 'tickettype', 'step')
            auth_countertype = CounterType.objects.filter(branch__in=auth_branchs)
        '''
    else : 
        profid_list = []
        userid_list = []
        grouplist = []
        # if user.groups.filter(name='admin').exists() == True :
        #     auth_branchs = Branch.objects.all()
        #     auth_grouplist = Group.objects.all()
        if user.groups.filter(name='support').exists() == True :
            auth_branchs = Branch.objects.all()
            grouplist.append('support')
            grouplist.append('supervisor')
            grouplist.append('manager')
            grouplist.append('reporter')
            grouplist.append('counter')
        elif user.groups.filter(name='supervisor').exists() == True :
            auth_branchs = Branch.objects.all()
            grouplist.append('supervisor')
            grouplist.append('manager')
            grouplist.append('reporter')
            grouplist.append('counter')
        elif user.groups.filter(name='manager').exists() == True :
            auth_branchs = UserProfile.objects.get(user=user).branchs.all()
            grouplist.append('manager')
            grouplist.append('reporter')
            grouplist.append('counter')        
        elif user.groups.filter(name='reporter').exists() == True :
            auth_branchs = UserProfile.objects.get(user=user).branchs.all()
            grouplist.append('reporter')
            grouplist.append('counter')           
        elif user.groups.filter(name='counter').exists() == True :
            auth_branchs = UserProfile.objects.get(user=user).branchs.all()
            grouplist.append('counter')         
        
        # profid_list = []
        # userid_list = []
        # for prof in profiles :
        #     not_auth = False
        #     for b in prof.branchs.all():
        #         if (b in auth_branchs) == True :
        #             pass                
        #         else :
        #             not_auth = True
        #     if not_auth == False :
        #         if prof.user.is_superuser == False :
        #             if ('api' in prof.user.groups.all()) == False :
        #                 if ('web' in prof.user.groups.all()) == False :
        #                     profid_list.append(prof.id)
        #                     userid_list.append(prof.user.id)


        profiles = UserProfile.objects.all()        
        for prof in profiles :
            not_auth = False
            if prof.branchs.all().count() == 0 :
                profid_list.append(prof.id)
                userid_list.append(prof.user.id)
            else:
                for b in prof.branchs.all():                
                    if (b in auth_branchs) == True  :
                        pass                
                    else :
                        not_auth = True
            if not_auth == False :
                if prof.user.is_superuser == False :
                    for usergroup in prof.user.groups.all() :
                        if (usergroup.name in grouplist) == True :                   
                            profid_list.append(prof.id)
                            userid_list.append(prof.user.id)
                            break
        # take out superuser
        for user in userid_list :
            if User.objects.get(id=user).is_superuser == True :
                userid_list.remove(user)
                profid_list.remove(UserProfile.objects.get(user__exact=user).id)                


        auth_userlist = User.objects.filter(id__in=userid_list)
        auth_userlist_active = auth_userlist.filter(Q(is_active=True))
        auth_profilelist = UserProfile.objects.filter(id__in=profid_list)
        auth_ticketformats = TicketFormat.objects.filter(branch__in=auth_branchs).order_by('branch','ttype')
        auth_routes = TicketRoute.objects.filter(branch__in=auth_branchs).order_by('branch','countertype', 'tickettype', 'step')
        auth_countertype = CounterType.objects.filter(branch__in=auth_branchs)
        auth_grouplist = Group.objects.filter(name__in=grouplist)
        # sort auth_grouplist by name
        auth_grouplist = auth_grouplist.order_by('name')
    return(auth_branchs, auth_userlist, auth_userlist_active, auth_grouplist, auth_profilelist, auth_ticketformats, auth_routes, auth_countertype)


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
    if error == '' :
        if newform.branch == None :
            # Error branch is None
            error = 'Error Branch is blank'
    if error == '' :
        # check if ticket type should be letter
        if newform.ttype.isalpha() == False :
            error = 'Ticket type should be letter'
    # for PCCW Ticket type should be 2 letter
    # if error == '' :
    #     if len(newform.ttype) != 2 :
    #         error = 'Ticket type should be 2 letters'
    # Ticket type should be upper case
    if error == '' :
        if newform.ttype != newform.ttype.upper():
            error = 'Ticket type should be upper case'
    return (error, newform)

def checkbranchsettingsform(form):
    error = ''
    newform = None
    if error == '':
        if form.is_valid() == False:
            error_string = ' '.join([' '.join(x for x in l) for l in list(form.errors.values())])
            error = 'An error occurcd during registration: '+ error_string
    if error == '':
        newform = form.save(commit=False)
        if newform.name == '':
            error = 'An error occurcd : Branch name is blank'
    # if error == '':
    #     # check  newform.branchname is aplha or number
    #     if newform.branchname.isalnum() == False :
    #         error = 'An error occurcd : Branch should be letter or number'
    if error == '':
        # check newform.timezone is right format
        if newform.timezone not in pytz.all_timezones:
            error = 'An error occurcd : Timezone is not correct'
    if error == '':
        try:
            newform.officehourstart = funLocaltoUTCtime(newform.officehourstart, newform.timezone)
        except:
            error = 'An error occurcd : Office hour start is not correct'
    if error == '':
        try:
            newform.officehourend = funLocaltoUTCtime(newform.officehourend, newform.timezone)
        except:
            error = 'An error occurcd : Office hour end is not correct'
    if error == '':
        try:
            newform.tickettimestart = funLocaltoUTCtime(newform.tickettimestart, newform.timezone)
        except:
            error = 'An error occurcd : Ticket start time is not correct'
    if error == '':
        try:
            newform.tickettimeend = funLocaltoUTCtime(newform.tickettimeend, newform.timezone)
        except:
            error = 'An error occurcd : Ticket end time is not correct'
    if error == '':
        try:
            newform.substart = funLocaltoUTC(newform.substart, newform.timezone)
        except:
            error = 'An error occurcd : Subscribe start time is not correct'
    if error == '':
        try:
            newform.subend = funLocaltoUTC(newform.subend, newform.timezone)
        except:
            error = 'An error occurcd : Subscribe end time is not correct'            
    if error == '':
        if newform.queuepriority == '':
            error = 'An error occurcd : Queue priority is blank'
    if error == '':
        if newform.queuemask == '':
            error = 'An error occurcd : Queue mask is blank' 
    if error == '':
        if newform.ticketmax < 1 :
            error = 'An error occurcd : Ticket max is not correct'
    if error == '':
        if newform.ticketnext < 1 :
            error = 'An error occurcd : Ticket next is not correct'            
    if error == '':
        if newform.ticketnoformat == '':
            error = 'An error occurcd : Ticket format is blank'
    if error == '':
        for c in newform.ticketnoformat:
            if c != '0':
                error = 'An error occurcd : Ticket number format should be "0".'
                break
    if error == '':
        if 0 < newform.displayflashtime and newform.displayflashtime <= 50 :
            pass
        else :
            error = 'An error occurcd : Display flash time should be 1-50.'
    if error == '':
        if -1 < newform.language1 and newform.language1 <= 4 :
            pass
        else :
            error = 'An error occurcd : Language 1 should be 0-4.'
    if error == '':
        if -1 < newform.language2 and newform.language2 <= 4 :
            pass
        else :
            error = 'An error occurcd : Language 2 should be 0-4.'
    if error == '':
        if -1 < newform.language3 and newform.language3 <= 4 :
            pass
        else :
            error = 'An error occurcd : Language 3 should be 0-4.'
    if error == '':
        if -1 < newform.language4 and newform.language4 <= 4 :
            pass
        else :
            error = 'An error occurcd : Language 4 should be 0-4.'   
    if error == '':
        if newform.substart > newform.subend :
            error = 'An error occurcd : subscribe start time should be earlier than sub end time.'
    return (error, newform)