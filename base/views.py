from aqs.settings import aqs_version, RECAPTCHA_ENABLED, APP_NAME
from django.shortcuts import render, redirect, HttpResponse
from django.urls import reverse
from django.contrib.auth.models import User, Group
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.hashers import make_password
from django.db.models import Q
from django.contrib.auth.forms import UserCreationForm, PasswordChangeForm
from datetime import datetime, timezone, timedelta
from base.decorators import *
# from django.urls import reverse_lazy
from .models import TicketLog, CounterStatus, CounterType, TicketData, TicketRoute, UserProfile, TicketFormat
from .models import Branch, TicketTemp, DisplayAndVoice, PrinterStatus, WebTouch, Ticket, Domain
from booking.models import TimeSlot, Booking, BookingLog, TimeslotTemplate
from .forms import TicketFormatForm, UserForm, UserFormAdmin, UserProfileForm, UserProfileFormAdmin, trForm, resetForm
from .forms import BranchSettingsForm_Admin, BranchSettingsForm_Adv, BranchSettingsForm_Basic
from .forms import CaptchaForm, getForm, voidForm, newTicketTypeForm, UserFormSuper, UserFormManager, UserFormSupport, UserFormAdminSelf
from .api.views import funUTCtoLocal, funLocaltoUTC, funUTCtoLocaltime, funLocaltoUTCtime
import pytz
from .api.serializers import displaylistSerivalizer, waitinglistSerivalizer
# from django.utils import timezone
from .api.v_softkey_sub import *
from .api.v_touch import newticket_v840, printTicket_v840, funDomain
from base.ws import wsHypertext, wscounterstatus, wssendflashlight
import logging
import csv
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from aqs.tasks import *
import pickle
from django.templatetags.static import static
from celery.result import AsyncResult
from django.conf import settings
from base.sch.views import sch_shutdown
from django.db.models import BooleanField, Value
from crm.models import CRMAdmin, Member, Company, Customer, Quotation, Invoice, Receipt, Supplier, Product, Product_Type, Category


logger = logging.getLogger(__name__)

userweb = None
try:
    userweb = User.objects.get(username='userweb')
except:
    logger.error('userweb not found.')
    

context_login = {}

sort_direction = {}



def adminlockedView(request,):
    return render(request, 'base/admin_locked.html')

def funRegenUserFunctions(user):
    userpobj = UserProfile.objects.filter(user=user)
    for userp in userpobj:
        branchs = userp.branchs.all()
        en_queue = False
        en_crm = False
        en_booking = False
        for branch in branchs:
            if branch.queueenabled == True:
                en_queue = True
            if branch.bookingenabled == True:
                en_booking = True
            if en_queue == True and en_booking == True:
                break
        # CRM enabled should be check from CRMAdmin
                
        userp.enabled_queue = en_queue
        userp.enabled_crm = en_crm
        userp.enabled_booking = en_booking
        userp.save()
    pass

@allowed_users(allowed_roles=['admin','support','supervisor','manager','reporter'])
@unauth_user
def SuperVisor_ForceLogoutView(request, pk, csid):
    context = {}
    datetime_now =datetime.now(timezone.utc)
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
    datetime_now =datetime.now(timezone.utc)
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
            status, msg = funVoid(request.user, tt, td, 'Void ticket from list ', 'Softkey-web', softkey_version,  datetime_now)
            if status['status'] == 'Error':
                messages.error(request, msg['msg'] + ' ' + tt.tickettype + tt.ticketnumber)
            elif status['status'] == 'OK':
                messages.success(request, 'Ticket ' + tt.tickettype + tt.ticketnumber + ' has been voided.')
            return redirect('softkey', pk=pk)
    return render(request , 'base/softkey_confirm.html', context)

@unauth_user
def Softkey_GetView(request, pk, ttid):
    context = {}
    datetime_now =datetime.now(timezone.utc)
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
        # old version no database lock may be cause double call
        # status, msg, context_get = funCounterGet('', tt.tickettype, tt.ticketnumber, request.user, counterstatus.countertype.branch, counterstatus.countertype, counterstatus, 'Get ticket from list ', 'Softkey-web', softkey_version, datetime_now)
        # new version with database lock
        for i in range(0, 10):
            status, msg, context_get = funCounterGet_v840(tt.tickettype_disp + tt.ticketnumber_disp, request.user, counterstatus.countertype.branch, counterstatus.countertype, counterstatus, 'Get ticket from list ', 'Softkey-web', softkey_version, datetime_now)
            if status['status'] == 'OK':
                break
            else:
                error = msg['msg']
                from base.a_global import str_db_locked
                if error == str_db_locked:
                    logger.warning('Database is locked. Retry ' + str(i + 1) + ' times.')
                    time.sleep(0.05)
                else:
                    break
        if status['status'] == 'Error':
            error = msg['msg'] + ' ' + tt.tickettype + tt.ticketnumber
    # # no need to confirm
    # if error == '':
    #     text = 'Confirm to call ticket : "' + tt.tickettype + tt.ticketnumber + '" ?'
    #     context = {'tt':tt} | {'text':text}
    #     if request.method == 'POST':
    #         action = request.POST.get('action')
    #         if action == 'confirm':           
    #             status, msg, context_get = funCounterGet('', tt.tickettype, tt.ticketnumber, request.user, counterstatus.countertype.branch, counterstatus.countertype, counterstatus, 'Get ticket from list ', 'Softkey-web', softkey_version, datetime_now)
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
    datetime_now =datetime.now(timezone.utc)

    context = getcontext(request, request.user)

    try:
        counterstatus = CounterStatus.objects.get(id=pk)
        datetime_now_local = funUTCtoLocal(datetime_now, counterstatus.countertype.branch.timezone)
        str_now = datetime_now_local.strftime('%Y-%m-%d %H:%M:%S')
        context = context | {
            'waitinglist_show':counterstatus.countertype.branch.websoftkey_show_waitinglist,
            }
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
                if userttype == None :
                    userttype = ''
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
        # non-booking ticket
        ticketlist = TicketTemp.objects.filter(Q(booking_id=None) & Q(branch=counterstatus.countertype.branch) & Q(countertype=counterstatus.countertype) & Q(status=lcounterstatus[0]) & Q(locked=False)).order_by('tickettime')
        serializers  = waitinglistSerivalizer(ticketlist, many=True)
        # booking ticket
        ticketlist_b = TicketTemp.objects.filter(~Q(booking_id=None) & (Q(booking_user=request.user) | Q(booking_user=None)) & Q(branch=counterstatus.countertype.branch) & Q(countertype=counterstatus.countertype) & Q(status=lcounterstatus[0]) & Q(locked=False)).order_by('booking_tickettype', 'tickettime')
        serializers_b  = waitinglistSerivalizer(ticketlist_b, many=True)
        context_ql = serializers_b.data + serializers.data
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
            context_ql[i]['tickettime_local_date'] = tickettime_local.strftime('%Y-%m-%d')
            context_ql[i]['tickettime_local_time'] = tickettime_local.strftime('%H:%M:%S')

    if error == '':
        printerobj = PrinterStatus.objects.filter(Q(branch=counterstatus.countertype.branch))

        if request.method == 'POST':
            action = request.POST.get('action')
            if action == 'submit':
                # add Get form to context
                getform = getForm(request.POST)
                getticket = getform['ticketnumber'].value()
                
                if error == '':
                    # old version no database lock may be cause double call
                    # status, msg, context_get = funCounterGet(getticket, '', '', request.user, counterstatus.countertype.branch, counterstatus.countertype, counterstatus, 'Get ticket ', 'Softkey-web', softkey_version, datetime_now)
                    # new version with database lock
                    for i in range(0, 10):
                        status, msg, context_get = funCounterGet_v840(getticket, request.user, counterstatus.countertype.branch, counterstatus.countertype, counterstatus, 'Get ticket ', 'Softkey-web', softkey_version, datetime_now)
                        if status['status'] == 'OK':
                            break
                        else:
                            error = msg['msg']
                            from base.a_global import str_db_locked
                            if error == str_db_locked:
                                logger.warning('Database is locked. Retry ' + str(i + 1) + ' times.')
                                time.sleep(0.05)
                            else:
                                break
                    if status['status'] == 'Error':
                        messages.error(request, msg['msg'] + ' ' + getticket)
                    context = context | context_counter | {'pk':pk} | context_get
                else :
                    messages.error(request, error)
              
                return redirect('softkey', pk=pk)
                # return render(request, 'base/softkey.html', context)
            elif action == 'call':
                # old version no database lock may be cause double call
                # status, msg, context_call = funCounterCall(request.user, counterstatus.countertype.branch, counterstatus.countertype, counterstatus, 'Call ticket ', 'Softkey-web', softkey_version, datetime_now)                
                # new version with database lock
                for i in range(0, 10):
                    status, msg, context_call = funCounterCall_v840(request.user, counterstatus.countertype.branch, counterstatus.countertype, counterstatus, 'Call ticket ', 'Softkey-web', softkey_version, datetime_now)
                    if status['status'] == 'OK':
                        break
                    else:
                        error = msg['msg']
                        from base.a_global import str_db_locked
                        if error == str_db_locked:
                            logger.warning('Database is locked. Retry ' + str(i + 1) + ' times.')
                            time.sleep(0.05)
                        else:
                            break
                
                if status['status'] == 'Error':
                    messages.error(request, msg['msg'])
                if status['status'] == 'OK' and context_call == {'data': {}} :
                    messages.success(request, 'No ticket to call.')
            elif action == 'recall':
                status, msg =  funCounterRecall(request.user, counterstatus.countertype.branch, counterstatus.countertype, counterstatus, 'Recall ticket ', 'Softkey-web', softkey_version, datetime_now)
                if status['status'] == 'OK' :
                    messages.success(request, 'Recall ticket success.')
                    # how to return to same page after post and do not refresh page
                    # return None
            elif action == 'process':
                status, msg = funCounterProcess(request.user, counterstatus.countertype.branch, counterstatus.countertype, counterstatus, 'Process ticket ', 'Softkey-web', softkey_version, datetime_now)
            elif action == 'done':
                status, msg = funCounterComplete(request.user, counterstatus.countertype.branch, counterstatus.countertype, counterstatus, 'Done ticket ', 'Softkey-web', softkey_version, datetime_now)
            elif action == 'miss':
                status, msg = funCounterMiss(request.user, counterstatus.countertype.branch, counterstatus.countertype, counterstatus, 'Miss ticket ', 'Softkey-web', softkey_version, datetime_now)
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
        elif counterstatus.countertype.countermode == 'cc':
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

        context = getcontext(request, request.user)
        context = context | {'counterstatus':counterstatus}

        return render(request, 'base/softkey_lobby_branch.html', context)
    else :
        return HttpResponse(error)

@unauth_user
def SoftkeyLoginView(request, pk):
    error = ''
    context = {}

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
            cs = CounterStatus.objects.filter(Q(countertype=ct)).exclude(enabled=False).order_by('countertype',) \
            .extra(select={'casted_object_id': 'CAST(counternumber AS INTEGER)'}).extra(order_by = ['casted_object_id'])
            counterstatus.append(cs)

        context = getcontext(request, request.user)
        context = context | {'counterstatus':counterstatus}

        return render(request, 'base/softkey_lobby.html', context)
    else :
        return HttpResponse(error)
  
@unauth_user
def SoftkeyLogoutView(request, pk):
    error = ''
    context = {}
    datetime_now =datetime.now(timezone.utc)
    
    # auth_en_queue, \
    # auth_en_crm, \
    # auth_en_booking, \
    # auth_branchs , \
    # auth_userlist, \
    # auth_userlist_active, \
    # auth_grouplist, \
    # auth_profilelist, \
    # auth_ticketformats , \
    # auth_routes, \
    # auth_countertype, \
    # auth_timeslots, \
    # auth_bookings, \
    # auth_timeslottemplist, \
    # auth_memberlist, \
    # auth_customerlist, \
    # auth_quotations, \
    # auth_invoices, \
    # auth_receipts, \
    # = auth_data(request.user)

    # context = {
    #     'users':auth_userlist, 'branchs':auth_branchs, 'ticketformats':auth_ticketformats, 'routes':auth_routes, 'timeslots':auth_timeslots,
    #     }
    # context_en = getcontext_en(request)
    # context = context | context_en
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
    datetime_now =datetime.now(timezone.utc)

    context_temp = getcontext(request, request.user)
    auth_userlist = context_temp['users']
    auth_branchs = context_temp['branchs']
    auth_ticketformats = context_temp['ticketformats']
    auth_routes = context_temp['routes']
    auth_timeslots = context_temp['timeslots']

    context = {
        'users':auth_userlist, 'branchs':auth_branchs, 'ticketformats':auth_ticketformats, 'routes':auth_routes, 'timeslots':auth_timeslots,
        }
    context_en = getcontext_en(request)
    context = context | context_en
    try:
        counterstatus = CounterStatus.objects.get(id=pk)
    except:
        error = 'CounterStatus not found.'
    if counterstatus == None:
        error = 'CounterStatus not found.'

    if error == '':
        # old version no database lock may be cause double call
        # status, msg, context = funCounterCall(request.user, counterstatus.countertype.branch, counterstatus.countertype, counterstatus, 'Call ticket:', 'Softkey-web', softkey_version, datetime_now)        
        # new version with database lock
        for i in range(0, 10):
            status, msg, context = funCounterCall_v840(request.user, counterstatus.countertype.branch, counterstatus.countertype, counterstatus, 'Call ticket:', 'Softkey-web', softkey_version, datetime_now)
            if status['status'] == 'OK':
                break
            else:
                error = msg['msg']
                from base.a_global import str_db_locked
                if error == str_db_locked:
                    logger.warning('Database is locked. Retry ' + str(i + 1) + ' times.')
                    time.sleep(0.05)
                else:
                    break        
        
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
    datetime_now =datetime.now(timezone.utc)
    
    # auth_en_queue, \
    # auth_en_crm, \
    # auth_en_booking, \
    # auth_branchs , \
    # auth_userlist, \
    # auth_userlist_active, \
    # auth_grouplist, \
    # auth_profilelist, \
    # auth_ticketformats , \
    # auth_routes, \
    # auth_countertype, \
    # auth_timeslots, \
    # auth_bookings, \
    # auth_timeslottemplist, \
    # auth_memberlist, \
    # auth_customerlist, \
    # auth_quotations, \
    # auth_invoices, \
    # auth_receipts, \
    # = auth_data(request.user)
    
    # context = {       
    #     'users':auth_userlist, 'branchs':auth_branchs, 'ticketformats':auth_ticketformats, 'routes':auth_routes, 'timeslots':auth_timeslots,
    #     }
    # context_en = getcontext_en(request)
    # context = context | context_en    
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
    datetime_now =datetime.now(timezone.utc)
    
    # auth_en_queue, \
    # auth_en_crm, \
    # auth_en_booking, \
    # auth_branchs , \
    # auth_userlist, \
    # auth_userlist_active, \
    # auth_grouplist, \
    # auth_profilelist, \
    # auth_ticketformats , \
    # auth_routes, \
    # auth_countertype, \
    # auth_timeslots, \
    # auth_bookings, \
    # auth_timeslottemplist, \
    # auth_memberlist, \
    # auth_customerlist, \
    # auth_quotations, \
    # auth_invoices, \
    # auth_receipts, \
    # = auth_data(request.user)

    # context = {
    #     'users':auth_userlist, 'branchs':auth_branchs, 'ticketformats':auth_ticketformats, 'routes':auth_routes, 'timeslots':auth_timeslots,
    #     }
    # context_en = getcontext_en(request)
    # context = context | context_en    
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
    datetime_now =datetime.now(timezone.utc)
    
    # auth_en_queue, \
    # auth_en_crm, \
    # auth_en_booking, \
    # auth_branchs , \
    # auth_userlist, \
    # auth_userlist_active, \
    # auth_grouplist, \
    # auth_profilelist, \
    # auth_ticketformats , \
    # auth_routes, \
    # auth_countertype, \
    # auth_timeslots, \
    # auth_bookings, \
    # auth_timeslottemplist, \
    # auth_memberlist, \
    # auth_customerlist, \
    # auth_quotations, \
    # auth_invoices, \
    # auth_receipts, \
    # = auth_data(request.user)

    # context = {
    #     'users':auth_userlist, 'branchs':auth_branchs, 'ticketformats':auth_ticketformats, 'routes':auth_routes, 'timeslots':auth_timeslots,
    #     }
    # context_en = getcontext_en(request)
    # context = context | context_en    
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
    datetime_now =datetime.now(timezone.utc)
    
    # auth_en_queue, \
    # auth_en_crm, \
    # auth_en_booking, \
    # auth_branchs , \
    # auth_userlist, \
    # auth_userlist_active, \
    # auth_grouplist, \
    # auth_profilelist, \
    # auth_ticketformats , \
    # auth_routes, \
    # auth_countertype, \
    # auth_timeslots, \
    # auth_bookings, \
    # auth_timeslottemplist, \
    # auth_memberlist, \
    # auth_customerlist, \
    # auth_quotations, \
    # auth_invoices, \
    # auth_receipts, \
    # = auth_data(request.user)

    # context = {
    #     'aqs_version':aqs_version, 
    #     'en_queue':auth_en_queue, 'en_crm':auth_en_crm, 'en_booking':auth_en_booking,
    #     'users':auth_userlist, 'branchs':auth_branchs, 'ticketformats':auth_ticketformats, 'routes':auth_routes, 'timeslots':auth_timeslots,
    #     }
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
    # 127.0.0.1:8000/repair?bc=MHT&note=R00124
    context = None
    error = ''
    bcode = ''
    note = ''
    str_now = '---'

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
            datetime_now = datetime.now(timezone.utc)
            datetime_now_local = funUTCtoLocal(datetime_now, branch.timezone)
            str_now = datetime_now_local.strftime('%Y-%m-%d %H:%M:%S')
        else :
            error = 'Branch not found.'
    if error == '':
        if note == 'R00124':
            counterstatus = 'done'
            # counterstatus = 'repairing'
        else :
            counterstatus = 'error'
        logo, navbar_title, css, webtvlogo, webtvcss, eticketlink = funDomain(request)
        context = {
            'ticket':note,
            'bcode':branch.bcode,
            'counterstatus':counterstatus,
            'logofile':webtvlogo,
            'lastupdate':str_now,            
            'errormsg':'',
            'css' : webtvcss,
            }
    else:
        logo, navbar_title, css, webtvlogo, webtvcss, eticketlink = funDomain(request)
        context = {
            'lastupdate':str_now, 
            'logofile':webtvlogo,
            'errormsg':error,
            }
        messages.error(request, error)

    context_mini = getcontext_mini(request)
    context = context_mini | context
    return render(request , 'base/repair.html', context)

def webmyticket(request, bcode, ttype, tno, sc):
    # ttype is ticket type
    # tno is ticket number
    # sc is ticket Security code
    # 127.0.0.1:8000/my/KB/A/001/123
    # Special for TVP MHT Project 
    # Special ticket : /my/MHT/A/003/rdA/
    
    context = None
    error = ''
    str_now = '---'
    scroll = ''

    ticket = ttype + tno
    securitycode = sc

    branch = None
    logo, navbar_title, css, webtvlogo, webtvcss, eticketlink = funDomain(request)

    datetime_now_local = None
    if error == '' :        
        branchobj = Branch.objects.filter( Q(bcode=bcode) )
        if branchobj.count() == 1:
            branch = branchobj[0]
            datetime_now = datetime.now(timezone.utc)
            datetime_now_local = funUTCtoLocal(datetime_now, branch.timezone)
            str_now = datetime_now_local.strftime('%Y-%m-%d %H:%M:%S')
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
            tickettime_str = tickettime.strftime('%Y-%m-%d %H:%M:%S')
        else :
            error = 'Ticket not found.'
    
    displaylist = None 
    if error == '' :
        # displaylist = DisplayAndVoice.objects.filter (branch=branch, countertype=countertype).order_by('-displaytime')[:5]
        displaylist = DisplayAndVoice.objects.filter (branch=branch, countertype=countertype).order_by('-displaytime')[:5]
        wdserializers  = displaylistSerivalizer(displaylist, many=True)
        ticketlist = wdserializers.data
    counter='---'
    if error == '':
        csobj = CounterStatus.objects.filter(
            Q(tickettemp = tickettemp)
        )
        if csobj.count() == 1:
            counter = csobj[0].counternumber

    # Special for TVP MHT Project 
    # Special ticket : /my/MHT/A/003/rdA/
    if bcode == 'MHT' and ttype == 'A' and tno == '003' and sc == 'rdA':
        tickettime_str = '18:39:06 16-07-2024'
        counterstatus = 'done'
        countertype = CounterType.objects.filter(branch=branch)[0]
        scroll = countertype.displayscrollingtext
        ticketlist = [{'tickettype': 'A', 'ticketnumber': '002', 'tickettime': '2024-09-29T03:10:51.396585Z', 'displaytime': '2024-09-29T03:11:16.220329Z', 'counternumber': '1', 'wait': '0', 'flashtime': 6, 'ct_lang1': 'Counter', 'ct_lang2': '櫃枱', 'ct_lang3': None, 'ct_lang4': None, 't_lang1': '維修服務', 't_lang2': 'Maintenance service', 't_lang3': None, 't_lang4': None}, {'tickettype': 'A', 'ticketnumber': '001', 'tickettime': '2024-09-29T03:10:47.624269Z', 'displaytime': '2024-09-29T03:11:10.052153Z', 'counternumber': '1', 'wait': '0', 'flashtime': 6, 'ct_lang1': 'Counter', 'ct_lang2': '櫃枱', 'ct_lang3': None, 'ct_lang4': None, 't_lang1': '維修服務', 't_lang2': 'Maintenance service', 't_lang3': None, 't_lang4': None}]
        tickettemp = None
        counter='1'
        context = {
            'wsh' : wsHypertext,
            'ticket':ticket,
            'tickettime':tickettime_str,
            'bcode':branch.bcode,
            'counterstatus':counterstatus,
            'logofile':webtvlogo,
            'css' : webtvcss,
            'lastupdate':str_now,
            'counter':counter,
            'countertype':countertype,
            'tickettemp':tickettemp,
            'ticketlist':ticketlist,
            'errormsg':'',
            'scroll':scroll,
            }
        context = {'aqs_version':aqs_version} | {'app_name':APP_NAME} | context 

        return render(request , 'base/webmyticket_tvp.html', context)
    if error == '':
        context = {
            'wsh' : wsHypertext,
            'ticket':ticket,
            'tickettime':tickettime_str,
            'bcode':branch.bcode,
            'counterstatus':counterstatus,
            'logofile':webtvlogo,
            'css' : webtvcss,
            'lastupdate':str_now,
            'counter':counter,
            'countertype':countertype,
            'tickettemp':tickettemp,
            'ticketlist':ticketlist,
            'errormsg':'',
            'scroll':scroll,
            }
    if error != '' :
        context = {
            'lastupdate':str_now, 
            'logofile':webtvlogo,
            'errormsg':error,
            'scroll':scroll,
            'css' : webtvcss,
            }
        messages.error(request, error)
    context = {'aqs_version':aqs_version} | {'app_name':APP_NAME} | context 

    return render(request , 'base/webmyticket.html', context)


# Create your views here.
def webtouchView(request):
    # 127.0.0.1:8000/touch?bc=KB&t=t1
    # t1 is Touch Name
    context = None
    error = ''
    bcode = ''
    touchname = ''
    touchkeylist= []
    
    logo, navbar_title, css, webtvlogo, webtvcss, eticketlink = funDomain(request)

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
            datetime_now = datetime.now(timezone.utc)
            datetime_now_local = funUTCtoLocal(datetime_now, branch.timezone)
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
                    # old version no database lock may be cause double ticket number
                    # ticketno_str, countertype, tickettemp, ticket, error = newticket(branch, key.ttype, '','', datetime_now, userweb, 'web', '8')
                    # new version with database lock                    
                    ticketno_str, countertype, tickettemp, ticket, error = newticket_v840(branch, key.ttype, '', '', datetime_now, userweb, 'web', aqs_version, None, eticketlink)
                    
                    if error == '' :
                        printTicket_v840(branch, tickettemp, tickettemp.ticketformat, '')
                        # add ticketlog
                        localdate_now = funUTCtoLocal(datetime_now, tickettemp.branch.timezone)
                        TicketLog.objects.create(
                            tickettemp=tickettemp,
                            ticket=ticket,
                            logtime=datetime_now,
                            app = 'web',
                            version = '8',
                            logtext='New Ticket by Web Touch: '  + tickettemp.branch.bcode + '_' + tickettemp.tickettype + '_'+ tickettemp.ticketnumber + '_' + localdate_now.strftime('%Y-%m-%d_%H:%M:%S') ,
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
        'logofile':webtvlogo,
        'errormsg':error,
        'css' : webtvcss,
        }
    return render(request, 'base/webtouch.html', context)

def CancelTicketView(request, pk, sc):
    error = ''
    url = ''
    backurl = ''

    logo, navbar_title, css, webtvlogo, webtvcss, eticketlink = funDomain(request)
   
    try:
        tt = TicketTemp.objects.get(id=pk)

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
                datetime_now =datetime.now(timezone.utc)
                # funVoid(user, tt, td, datetime_now)
                status, msg = funVoid(request.user, tt, td, 'Void ticket from e-ticket ', 'Web', '8',  datetime_now)
                if status['status'] == 'Error':
                    error = msg['msg']
                    messages.error(request, error)
                return redirect(url)
    if error != '' :
        messages.error(request, error)
        if url != '':
            return redirect(url)

    context = {
    'aqs_version':aqs_version,
    'logofile':webtvlogo,
    'errormsg':error,
    'backurl':backurl,
    'css':webtvcss,
    }
    return render(request, 'base/webmyticket_cancel.html', context)

def webtv(request, bcode, ct):
    # WebSocket version
    # http://127.0.0.1:8000/webtv/KB/Reception/
    context = None
    error = ''
    str_now = '---'
    logo, navbar_title, css, webtvlogo, webtvcss, eticketlink = funDomain(request)

    countertypename = ct

    branch = None
    if error == '' :        
        branchobj = Branch.objects.filter( Q(bcode=bcode) )
        if branchobj.count() == 1:
            branch = branchobj[0]
            datetime_now = datetime.now(timezone.utc)
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
        
        context = {
            'wsh' : wsHypertext,
            'lastupdate' : str_now,
            'ticketlist' : wdserializers.data,
            'logofile' : webtvlogo,
            'css' : webtvcss,
            'scroll':countertype.displayscrollingtext,
            }
        # print (wdserializers.data[0].wait)
    else :
        context = {
            'lastupdate' : str_now,
            'errormsg' : error,
            'logofile' : webtvlogo,
            }
        messages.error(request, error)

    context = {
        'bcode' :  bcode ,
        'ct' : ct,
        } | context
    
    context = {'aqs_version':aqs_version} | {'app_name':APP_NAME} | context 
    return render(request , 'base/webtv.html', context)


@unauth_user
@allowed_users(allowed_roles=['admin','support','supervisor','manager','reporter'])
def Report_Ticket_details_Result(request, pk):
    error = ''
    ticket = None
    branch = None
    result_task_id = ''

    try:    
        result_task_id = request.GET['result']
    except:
        pass
    ticket_id = pk
    # try:
    #     ticket_id = request.GET['id']
    # except:
    #     ticket_id = ''
    #     error = 'Error : Ticket ID is blank.'



    if error == '':
        try:
            ticket = Ticket.objects.get(id=ticket_id)
        except:
            error = 'Error : Ticket not found.'

    if error == '':
        # check the user authorization to access the branch
        branch = ticket.branch
        userp = UserProfile.objects.get(user=request.user)
        if branch in userp.branchs.all():
            pass
        else:
            error = 'Error : User not authorized to access the branch.'

    if error == '':
        # result_task_id = ''
        # localtimezone = pytz.timezone(branch.timezone)
        # table = TicketLog.objects.filter(
        #     Q(ticket=ticket),
        # ).order_by('logtime')

        if result_task_id == '':
            # run celery task for long process
            localtimezone = pytz.timezone(branch.timezone)
            
            report_text = 'Ticket Details Report\n' + \
            'Ticket: ' + ticket.tickettype + ticket.ticketnumber + '\n' + \
            'Branch: ' + branch.name + ' (' + branch.bcode + ')'
        

            task = report_ticketdetails.apply_async(args=[ticket_id,report_text], countdown=0)  # 'countdown' time delay in second before execute
            task_id = task.id
            ptask_id = task_id.replace('-', '_')

            # download path
            url_download = ''
            
            
            context = {'task_id': ptask_id}
            context = context | {'app_name':APP_NAME}
            context = context | {'wsh' : wsHypertext}
            context = context | {'url_download': url_download}

            context_mini = getcontext_mini(request)
            context = context_mini | context
            return render(request, 'base/in_progress.html', context)
        else :
            # long process is done output result to HTML
            # task id is result_task_id
            task_id = result_task_id.replace('_', '-')
            # print ('task_id', task_id)
            task = AsyncResult(task_id, app=report_ticketdetails)
            status, header, report_table, report_text = task.get()

            # print ('status:', status)
            # print ('report_table:', report_table)
            # print ('count:', count)

            if request.method != 'POST':
                localtimezone = pytz.timezone(branch.timezone)
                # if ticketformat == None  :
                #     report_result = 'Total ticket Report\n' + 'Branch:' + branch.name + '(' + branch.bcode + ')\n' +  'Start datetime:' + s_startdate + '\n' + 'End datetime:' + s_enddate + '\nTicket Type:ALL'
                # else:
                #     # report_result = 'Total ticket Report  Branch:' + branch.name + '(' + branch.bcode + ') Start datetime:' + s_startdate + ' End datetime:' + s_enddate + ' Ticket Type:' + ticketformat.ttype
                #     report_result = 'Total ticket Report\n' + 'Branch:' + branch.name + '(' + branch.bcode + ')\n' +  'Start datetime:' + s_startdate + '\n' + 'End datetime:' + s_enddate + '\nTicket Type:' + ticketformat.ttype
               
                # report_result = status


                # Pagination
                table100 = None
                page = request.GET.get('page') if request.GET.get('page') != None else '1'
                page = int(page)
                per_page = 100  # Number of items per page

                paginator = Paginator(report_table, per_page)
                try:
                    table100 = paginator.page(page)
                except PageNotAnInteger:
                    table100 = paginator.page(1)
                except EmptyPage:
                    table100 = paginator.page(paginator.num_pages) 

                context = {
                'app_name':APP_NAME,
                # 'id':ticket_id,
                'task_id': result_task_id,
                'localtimezone':localtimezone,
                'text':report_text,
                'header':header,
                'table':table100,        
                }

                context = {'aqs_version':aqs_version} | context 
                return render(request, 'base/r-result.html', context)

            elif request.method == 'POST':
                action = request.POST.get('action')
                if action == 'excel':
                    # convert list (report_table) to string
                    # querystr = pickle.dumps(report_table.query)
                    
                    # print(querystr)
                    filename = 'details_' 
                    task = export_report.apply_async(args=[header,report_table,report_text,branch.bcode,filename], countdown=0)  # 'countdown' time delay in second before execute
                    task_id = task.id
                    ptask_id = task_id.replace('-', '_')
                    filename = 'details_' + ptask_id + '.csv'
                    
                    # download path
                    url_download = static('download/'+ branch.bcode + '/' + filename)

                    context = {'task_id': ptask_id}
                    context = context | {'wsh' : wsHypertext} 
                    context = context | {'url_download': url_download}
                    context = {'aqs_version':aqs_version} | {'app_name':APP_NAME} | context 
                    return render(request, 'base/in_progress.html', context)

    if error != '':
        messages.error(request, error)
        context = {
        'result':error,
        }
        return redirect('reports')
    # context = {'aqs_version':aqs_version} | context 
    # return render(request, 'base/r-result.html', context)

@unauth_user
@allowed_users(allowed_roles=['admin','support','supervisor','manager','reporter'])
def Report_NoOfQueue_Result(request):
    error = ''
    
    result_task_id = request.GET.get('result') if request.GET.get('result') != None else ''

    if result_task_id == '':
        branch = None
        ticketformat = None
        # change code to if request.GET.get('x') != None else ''
        bcode = request.GET.get('branch') if request.GET.get('branch') != None else ''
        # bcode = request.GET['branch']
        l_startdate = request.GET.get('startdate') if request.GET.get('startdate') != None else ''
        # s_startdate = request.GET['startdate']
        l_enddate = request.GET.get('enddate') if request.GET.get('enddate') != None else ''
        # s_enddate = request.GET['enddate']
        tickettype = request.GET.get('tickettype') if request.GET.get('tickettype') != None else ''
        # ticketformat_id = request.GET['ticketformats']
        result_task_id = request.GET.get('result') if request.GET.get('result') != None else ''
        report_type = request.GET.get('report_type') if request.GET.get('report_type') != None else ''

        s_startdate = l_startdate + ' 00:00:00.000000'
        # convert to datetime
        d_startdate = datetime.strptime(s_startdate, '%Y-%m-%d %H:%M:%S.%f')
        s_enddate = l_enddate + ' 23:59:59.999999'
        # convert to datetime
        d_enddate = datetime.strptime(s_enddate, '%Y-%m-%d %H:%M:%S.%f')
        # convert to UTC
        utc_startdate = funLocaltoUTC(d_startdate, 'UTC')
        utc_enddate = funLocaltoUTC(d_enddate, 'UTC')

        # check input data

        if error == '':
            if d_enddate < d_startdate :
                error = 'Error : Start datetime > End datetime.'
        if error == '':
            if (d_enddate - d_startdate).days > 100 :
                error = 'Error : Date range do not more then 100 days.'
        if error == '':
            if bcode == '':
                error = 'Error : Branch is blank.'
            else:
                try:
                    branch = Branch.objects.get(bcode=bcode)
                except:
                    error = 'Error : Branch not found.'
        if error == '':
            if tickettype != '':
                try:
                    ticketformat = TicketFormat.objects.filter(ttype=tickettype, branch=branch).first()
                except:
                    error = 'Error : Ticket Format not found.'
        if error == '':
            # result_task_id = ''
            # localtimezone = pytz.timezone(branch.timezone)
            # table = TicketLog.objects.filter(
            #     Q(ticket=ticket),
            # ).order_by('logtime')
            if report_type == 'queue':
                report_text = 'Number of queue per timeslot Report' + '\n'
            elif report_type == 'miss':
                report_text = 'Number of no show per timeslot Report' + '\n'
            elif report_type == 'done':
                report_text = 'Number of completed ticket per timeslot Report' + '\n'
            elif report_type == 'void':
                report_text = 'Number of void ticket per timeslot Report' + '\n'

            report_text = report_text + 'Date range: ' + l_startdate + ' to ' + l_enddate + '\n' \
            + 'Branch: ' + branch.name + ' (' + bcode + ')' + '\n' 
            if ticketformat == None:
                report_text = report_text + 'Ticket Type: ALL'
            else:
                report_text = report_text + 'Ticket Type: ' +  ticketformat.ttype

            tt = ''
            if ticketformat != None:
                tt = ticketformat.ttype
            task = report_NoOfQueue.apply_async(args=[report_type, utc_startdate, utc_enddate, report_text, bcode, tt], countdown=0)  # 'countdown' time delay in second before execute
            task_id = task.id
            ptask_id = task_id.replace('-', '_')

            url_download = ''

            context = {'task_id': ptask_id}
            context = context | {'app_name':APP_NAME}
            context = context | {'wsh' : wsHypertext}
            context = context | {'url_download': url_download}
            context_mini = getcontext_mini(request)
            context = context_mini | context
            return render(request, 'base/in_progress.html', context)
        else:
            messages.error(request, error)
            return redirect('reports')
    else :        
        # long process is done output result to HTML
        # task id is result_task_id        
        task_id = result_task_id.replace('_', '-')
        task = AsyncResult(task_id, app=report_NoOfQueue)
        status, header, report_table, report_text, bcode, report_type = task.get()

        if request.method != 'POST':
            # Pagination
            table100 = None
            page = request.GET.get('page') if request.GET.get('page') != None else '1'
            page = int(page)
            per_page = 100  # Number of items per page

            paginator = Paginator(report_table, per_page)
            try:
                table100 = paginator.page(page)
            except PageNotAnInteger:
                table100 = paginator.page(1)
            except EmptyPage:
                table100 = paginator.page(paginator.num_pages) 

            context = {
            'app_name':APP_NAME,
            'task_id': result_task_id,
            # 'localtimezone':localtimezone,
            'text':report_text,
            'header':header,
            'table':table100,        
            }
            context_mini = getcontext_mini(request)
            context = context_mini | context
            return render(request, 'base/r-result.html', context)
        elif request.method == 'POST':
            action = request.POST.get('action')
            if action == 'excel':
                # convert list (report_table) to string
                # querystr = pickle.dumps(report_table.query)
                
                # print(querystr)
                filename = report_type + '_' 
                task = export_report.apply_async(args=[header,report_table,report_text,bcode,filename], countdown=0)  # 'countdown' time delay in second before execute
                task_id = task.id
                ptask_id = task_id.replace('-', '_')
                filename = filename + ptask_id + '.csv'
                
                # download path
                url_download = static('download/'+ bcode + '/' + filename)

                context = {'task_id': ptask_id}
                context = context | {'wsh' : wsHypertext} 
                context = context | {'url_download': url_download}
                context = {'aqs_version':aqs_version} | {'app_name':APP_NAME} | context 
                return render(request, 'base/in_progress.html', context)

@unauth_user
@allowed_users(allowed_roles=['admin','support','supervisor','manager','reporter'])
def Report_QSum(request):
    error = ''
    
    result_task_id = request.GET.get('result') if request.GET.get('result') != None else ''

    if result_task_id == '':
        branch = None
        ticketformat = None
        # change code to if request.GET.get('x') != None else ''
        bcode = request.GET.get('branch') if request.GET.get('branch') != None else ''
        # bcode = request.GET['branch']
        l_startdate = request.GET.get('startdate') if request.GET.get('startdate') != None else ''
        # s_startdate = request.GET['startdate']
        l_enddate = request.GET.get('enddate') if request.GET.get('enddate') != None else ''
        # s_enddate = request.GET['enddate']
        tickettype = request.GET.get('tickettype') if request.GET.get('tickettype') != None else ''
        # ticketformat_id = request.GET['ticketformats']
        result_task_id = request.GET.get('result') if request.GET.get('result') != None else ''

        s_startdate = l_startdate + ' 00:00:00.000000'
        # convert to datetime
        d_startdate = datetime.strptime(s_startdate, '%Y-%m-%d %H:%M:%S.%f')
        s_enddate = l_enddate + ' 23:59:59.999999'
        # convert to datetime
        d_enddate = datetime.strptime(s_enddate, '%Y-%m-%d %H:%M:%S.%f')
        # convert to UTC
        utc_startdate = funLocaltoUTC(d_startdate, 'UTC')
        utc_enddate = funLocaltoUTC(d_enddate, 'UTC')

        # check input data

        if error == '':
            if d_enddate < d_startdate :
                error = 'Error : Start datetime > End datetime.'
        if error == '':
            if (d_enddate - d_startdate).days > 100 :
                error = 'Error : Date range do not more then 100 days.'
        if error == '':
            if bcode == '':
                error = 'Error : Branch is blank.'
            else:
                try:
                    branch = Branch.objects.get(bcode=bcode)
                except:
                    error = 'Error : Branch not found.'
        if error == '':
            if tickettype != '':
                try:
                    ticketformat = TicketFormat.objects.filter(ttype=tickettype, branch=branch).first()
                except:
                    error = 'Error : Ticket Format not found.'
        if error == '':
            # result_task_id = ''
            # localtimezone = pytz.timezone(branch.timezone)
            # table = TicketLog.objects.filter(
            #     Q(ticket=ticket),
            # ).order_by('logtime')
            report_text = 'Queue summary per day' + '\n' \
            + 'Date range: ' + l_startdate + ' to ' + l_enddate + '\n' \
            + 'Branch: ' + branch.name + ' (' + bcode + ')' + '\n' 
            if ticketformat == None:
                report_text = report_text + 'Ticket Type: ALL'
            else:
                report_text = report_text + 'Ticket Type: ' +  ticketformat.ttype

            tt = ''
            if ticketformat != None:
                tt = ticketformat.ttype
            task = t_Report_QSum.apply_async(args=[utc_startdate, utc_enddate, report_text, bcode, tt], countdown=0)  # 'countdown' time delay in second before execute
            task_id = task.id
            ptask_id = task_id.replace('-', '_')

            url_download = ''

            context = {'task_id': ptask_id}
            context = context | {'app_name':APP_NAME}
            context = context | {'wsh' : wsHypertext}
            context = context | {'url_download': url_download}
            context_mini = getcontext_mini(request)
            context = context_mini | context
            return render(request, 'base/in_progress.html', context)
        else:
            messages.error(request, error)
            return redirect('reports')
    else :
        # long process is done output result to HTML
        # task id is result_task_id        
        task_id = result_task_id.replace('_', '-')
        task = AsyncResult(task_id, app=t_Report_QSum)
        status, header, report_table, report_text, bcode = task.get()

        if request.method != 'POST':
            # Pagination
            table100 = None
            page = request.GET.get('page') if request.GET.get('page') != None else '1'
            page = int(page)
            per_page = 100  # Number of items per page

            paginator = Paginator(report_table, per_page)
            try:
                table100 = paginator.page(page)
            except PageNotAnInteger:
                table100 = paginator.page(1)
            except EmptyPage:
                table100 = paginator.page(paginator.num_pages) 

            context = {
            'app_name':APP_NAME,
            'task_id': result_task_id,
            # 'localtimezone':localtimezone,
            'text':report_text,
            'header':header,
            'table':table100,        
            }
            context_mini = getcontext_mini(request)
            context = context_mini | context
            return render(request, 'base/r-result.html', context)
        elif request.method == 'POST':
            action = request.POST.get('action')
            if action == 'excel':
                # convert list (report_table) to string
                # querystr = pickle.dumps(report_table.query)
                
                # print(querystr)
                filename = 'qsum_' 
                task = export_report.apply_async(args=[header,report_table,report_text,bcode,filename], countdown=0)  # 'countdown' time delay in second before execute
                task_id = task.id
                ptask_id = task_id.replace('-', '_')
                filename = filename + ptask_id + '.csv'
                
                # download path
                url_download = static('download/'+ bcode + '/' + filename)

                context = {'task_id': ptask_id}
                context = context | {'wsh' : wsHypertext} 
                context = context | {'url_download': url_download}
                context = {'aqs_version':aqs_version} | {'app_name':APP_NAME} | context 
                return render(request, 'base/in_progress.html', context)    


@unauth_user
@allowed_users(allowed_roles=['admin','support','supervisor','manager','reporter'])
def Report_RAW_Result2(request):
    error = ''
    
    result_task_id = request.GET.get('result') if request.GET.get('result') != None else ''

    if result_task_id == '':
        bcode = request.GET.get('branch') if request.GET.get('branch') != None else ''
        s_startdate = request.GET['startdate'] if request.GET.get('startdate') != None else ''
        s_enddate = request.GET['enddate'] if request.GET.get('enddate') != None else ''
        countertype_id = request.GET['countertype'] if request.GET.get('countertype') != None else ''

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

        s_startdate = s_startdate + 'T00:00:00.000000'

        if error == '':
            try:
                startdate = datetime.strptime(s_startdate, '%Y-%m-%dT%H:%M:%S.%f')
                utc_startdate = funLocaltoUTC(startdate, branch.timezone)
            
            except:
                error = 'Error : Start Datetime not found.'
        s_enddate = s_enddate + 'T23:59:59.999999'
        if error == '':
            try:
                enddate = datetime.strptime(s_enddate, '%Y-%m-%dT%H:%M:%S.%f')
                utc_enddate = funLocaltoUTC(enddate, branch.timezone)
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
            # report_result = 'RAW Data Report\nBranch:' + branch.name + '(' + branch.bcode + ')\nStart datetime:' + s_startdate + '\nEnd datetime:' + s_enddate 
            report_text = 'RAW Data Report' + '\n' \
            + 'Branch:' + branch.name + '(' + branch.bcode + ')' + '\n' \
            + 'Start datetime:' + s_startdate + '\n' \
            + 'End datetime:' + s_enddate + '\n'
            if countertype == None  :
                report_text = report_text + 'Counter Type:ALL'            
            else:
                report_text = report_text + 'Counter Type:' + countertype.name 

            #         table = TicketData.objects.filter(
            # Q(branch=branch),
            # Q(starttime__range=[startdate,enddate]),
            # ~Q(ticket = None),
            # Q(countertype=countertype),
            task = t_Report_RAW.apply_async(args=[utc_startdate, utc_enddate, report_text, branch.bcode, countertype_id], countdown=0)  # 'countdown' time delay in second before execute
            task_id = task.id
            ptask_id = task_id.replace('-', '_')

            url_download = ''

            context = {'task_id': ptask_id}
            context = context | {'app_name':APP_NAME}
            context = context | {'wsh' : wsHypertext}
            context = context | {'url_download': url_download}
            context_mini = getcontext_mini(request)
            context = context_mini | context
            return render(request, 'base/in_progress.html', context)
        else:
            messages.error(request, error)
            return redirect('reports')
    else :        
        # long process is done output result to HTML
        # task id is result_task_id        
        task_id = result_task_id.replace('_', '-')
        task = AsyncResult(task_id, app=t_Report_RAW)
        status, header, report_table, report_text, bcode = task.get()

        if request.method != 'POST':
            # Pagination
            table100 = None
            page = request.GET.get('page') if request.GET.get('page') != None else '1'
            page = int(page)
            per_page = 100  # Number of items per page

            paginator = Paginator(report_table, per_page)
            try:
                table100 = paginator.page(page)
            except PageNotAnInteger:
                table100 = paginator.page(1)
            except EmptyPage:
                table100 = paginator.page(paginator.num_pages) 

            context = {
            'app_name':APP_NAME,
            'task_id': result_task_id,
            # 'localtimezone':localtimezone,
            'text':report_text,
            'header':header,
            'table':table100,        
            }
            context_mini = getcontext_mini(request)
            context = context_mini | context
            return render(request, 'base/r-result_raw.html', context)
        elif request.method == 'POST':  
            action = request.POST.get('action')
            if action == 'excel':
                # convert list (report_table) to string
                # querystr = pickle.dumps(report_table.query)
                
                # print(querystr)
                filename = 'tickettype_' 
                task = export_report.apply_async(args=[header,report_table,report_text, bcode ,filename], countdown=0)  # 'countdown' time delay in second before execute
                task_id = task.id
                ptask_id = task_id.replace('-', '_')
                filename = filename + ptask_id + '.csv'
                
                # download path
                url_download = static('download/' + bcode + '/' + filename)

                context = {'task_id': ptask_id}
                context = context | {'wsh' : wsHypertext} 
                context = context | {'url_download': url_download}
                context = {'aqs_version':aqs_version} | {'app_name':APP_NAME} | context 
                return render(request, 'base/in_progress.html', context)








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

    s_startdate = s_startdate + 'T00:00:00.000000'

    if error == '':
        try:
            startdate = datetime.strptime(s_startdate, '%Y-%m-%dT%H:%M:%S.%f')
            startdate = funLocaltoUTC(startdate, branch.timezone)
        
        except:
            error = 'Error : Start Datetime not found.'
    s_enddate = s_enddate + 'T23:59:59.999999'
    if error == '':
        try:
            enddate = datetime.strptime(s_enddate, '%Y-%m-%dT%H:%M:%S.%f')
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
            )#.order_by('starttime')
            
        else:
            table = TicketData.objects.filter(
                Q(branch=branch),
                Q(starttime__range=[startdate,enddate]),
                ~Q(ticket = None),
                Q(countertype=countertype),
            )#.order_by('starttime') 
            report_result5 = 'Counter Type:' + countertype.name 
        report_result6 = 'Total records:' + str(table.count())
        report_result = report_result1 + '\n' + report_result2 + '\n' + report_result3 + '\n' + report_result4 + '\n' + report_result5 + '\n' + report_result6

        # testing only table repeat data 100 times
        # table2 = table
        # for i in range(10):
        #     table2 = table2.union( table, all=True )
        # table = table2
    
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
                task = export_raw.apply_async(args=[querystr,report_result1,report_result2,report_result3,report_result4,report_result5, bcode], countdown=0)  # 'countdown' time delay in second before execute
                task_id = task.id
                ptask_id = task_id.replace('-', '_')

                # download path
                url_download = static('download/'+ bcode + '/raw_' + task_id + '.csv')

                
                context = {'task_id': ptask_id}
                context = context | {'app_name':APP_NAME}
                context = context | {'wsh' : wsHypertext}
                context = context | {'url_download': url_download}
                context_mini = getcontext_mini(request)
                context = context_mini | context
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
    context_mini = getcontext_mini(request)
    context = context_mini | context
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
            context_mini = getcontext_mini(request)
            context = context_mini | context
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
                context_mini = getcontext_mini(request)
                context = context_mini | context
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
    context_mini = getcontext_mini(request)
    context = context_mini | context
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
        
        auth_branchs , \
        auth_userlist, \
        auth_userlist_active, \
        auth_grouplist, \
        auth_profilelist, \
        auth_ticketformats , \
        auth_routes, \
        auth_countertype, \
        auth_timeslots, \
        = auth_data(request.user)

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
            context_mini = getcontext_mini(request)
            context = context_mini | context
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
                context_mini = getcontext_mini(request)
                context = context_mini | context
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
    context_mini = getcontext_mini(request)
    context = context_mini | context
    return render(request, 'base/r-staff.html', context)

@unauth_user
@allowed_users(allowed_roles=['admin','support','supervisor','manager','reporter'])
def Report_StaffPerformance(request):
    error = ''
    
    result_task_id = request.GET.get('result') if request.GET.get('result') != None else ''

    if result_task_id == '':
        user_id = request.GET.get('user') if request.GET.get('user') != None else ''
        l_startdate = request.GET.get('startdate') if request.GET.get('startdate') != None else ''
        l_enddate = request.GET.get('enddate') if request.GET.get('enddate') != None else ''
        result_task_id = request.GET.get('result') if request.GET.get('result') != None else ''

        s_startdate = l_startdate + ' 00:00:00.000000'
        # convert to datetime
        d_startdate = datetime.strptime(s_startdate, '%Y-%m-%d %H:%M:%S.%f')
        s_enddate = l_enddate + ' 23:59:59.999999'
        # convert to datetime
        d_enddate = datetime.strptime(s_enddate, '%Y-%m-%d %H:%M:%S.%f')
        # convert to UTC
        utc_startdate = funLocaltoUTC(d_startdate, 'UTC')
        utc_enddate = funLocaltoUTC(d_enddate, 'UTC')

        # check input data

        if error == '':
            if d_enddate < d_startdate :
                error = 'Error : Start datetime > End datetime.'
        if error == '':
            if (d_enddate - d_startdate).days > 100 :
                error = 'Error : Date range do not more then 100 days.'

        if error == '':
            user_id_list = []
            if user_id == '':
                auth_en_queue, \
                auth_en_crm, \
                auth_en_booking, \
                auth_branchs , \
                auth_userlist, \
                auth_userlist_active, \
                auth_grouplist, \
                auth_profilelist, \
                auth_ticketformats , \
                auth_routes, \
                auth_countertype, \
                auth_timeslots, \
                auth_bookings, \
                auth_timeslottemplist, \
                = auth_data(request.user)
                # convert auth_userlist to user id list
                for user in auth_userlist:
                    user_id_list.append(user.pk)
            else:
                user_id_list.append(int(user_id))
        if error == '':
            # result_task_id = ''
            # localtimezone = pytz.timezone(branch.timezone)
            # table = TicketLog.objects.filter(
            #     Q(ticket=ticket),
            # ).order_by('logtime')
            report_text = 'Staff performance report' + '\n' \
            + 'Date range: ' + l_startdate + ' to ' + l_enddate + '\n'
            if user_id == '':
                report_text = report_text + 'User: ALL'
            else:
                report_text = report_text + 'User id: ' + str(user_id)

            task = t_Report_UserPerf.apply_async(args=[utc_startdate, utc_enddate, report_text, user_id_list], countdown=0)  # 'countdown' time delay in second before execute
            task_id = task.id
            ptask_id = task_id.replace('-', '_')

            url_download = ''

            context = {'task_id': ptask_id}
            context = context | {'app_name':APP_NAME}
            context = context | {'wsh' : wsHypertext}
            context = context | {'url_download': url_download}
            context_mini = getcontext_mini(request)
            context = context_mini | context
            return render(request, 'base/in_progress.html', context)
        else:
            messages.error(request, error)
            return redirect('reports')
    else :        
        # long process is done output result to HTML
        # task id is result_task_id        
        task_id = result_task_id.replace('_', '-')
        task = AsyncResult(task_id, app=t_Report_UserPerf)
        status, header, report_table, report_text = task.get()

        if request.method != 'POST':
            # Pagination
            table100 = None
            page = request.GET.get('page') if request.GET.get('page') != None else '1'
            page = int(page)
            per_page = 100  # Number of items per page

            paginator = Paginator(report_table, per_page)
            try:
                table100 = paginator.page(page)
            except PageNotAnInteger:
                table100 = paginator.page(1)
            except EmptyPage:
                table100 = paginator.page(paginator.num_pages) 

            context = {
            'app_name':APP_NAME,
            'task_id': result_task_id,
            # 'localtimezone':localtimezone,
            'text':report_text,
            'header':header,
            'table':table100,        
            }
            context_mini = getcontext_mini(request)
            context = context_mini | context
            return render(request, 'base/r-result.html', context)
        elif request.method == 'POST':
            action = request.POST.get('action')
            if action == 'excel':
                # convert list (report_table) to string
                # querystr = pickle.dumps(report_table.query)
                
                # print(querystr)
                filename = 'staffperf_' 
                task = export_report.apply_async(args=[header,report_table,report_text, None ,filename], countdown=0)  # 'countdown' time delay in second before execute
                task_id = task.id
                ptask_id = task_id.replace('-', '_')
                filename = filename + ptask_id + '.csv'
                
                # download path
                url_download = static('download/'+ filename)

                context = {'task_id': ptask_id}
                context = context | {'wsh' : wsHypertext} 
                context = context | {'url_download': url_download}
                context = {'aqs_version':aqs_version} | {'app_name':APP_NAME} | context 
                return render(request, 'base/in_progress.html', context)    

@unauth_user
@allowed_users(allowed_roles=['admin','support','supervisor','manager','reporter'])
def Report_TicketType(request):
    error = ''
    
    result_task_id = request.GET.get('result') if request.GET.get('result') != None else ''

    if result_task_id == '':
        branch = None
        ticketformat = None
        bcode = request.GET.get('branch') if request.GET.get('branch') != None else ''
        tickettype = request.GET.get('tickettype') if request.GET.get('tickettype') != None else ''
        l_startdate = request.GET.get('startdate') if request.GET.get('startdate') != None else ''
        l_enddate = request.GET.get('enddate') if request.GET.get('enddate') != None else ''
        result_task_id = request.GET.get('result') if request.GET.get('result') != None else ''

        s_startdate = l_startdate + ' 00:00:00.000000'
        # convert to datetime
        d_startdate = datetime.strptime(s_startdate, '%Y-%m-%d %H:%M:%S.%f')
        s_enddate = l_enddate + ' 23:59:59.999999'
        # convert to datetime
        d_enddate = datetime.strptime(s_enddate, '%Y-%m-%d %H:%M:%S.%f')
        # convert to UTC
        utc_startdate = funLocaltoUTC(d_startdate, 'UTC')
        utc_enddate = funLocaltoUTC(d_enddate, 'UTC')

        # check input data
        if error == '': 
            try:
                branch = Branch.objects.get(bcode=bcode)
            except:
                error = 'Error : Branch not found.'
        if error == '':
            if tickettype != '':
                try:
                    ticketformat = TicketFormat.objects.filter(ttype=tickettype, branch=branch).first()
                except:
                    error = 'Error : Ticket Format not found.'
        if error == '':
            if d_enddate < d_startdate :
                error = 'Error : Start datetime > End datetime.'
        if error == '':
            if (d_enddate - d_startdate).days > 100 :
                error = 'Error : Date range do not more then 100 days.'

        if error == '':
            ticketformat_id_list = []
            if ticketformat == None:
                ticketformats = TicketFormat.objects.filter(branch=branch)
                # convert auth_userlist to user id list
                for tf in ticketformats:
                    ticketformat_id_list.append(tf.pk)
            else:
                ticketformat_id_list.append(ticketformat.pk)
        if error == '':
            # result_task_id = ''
            # localtimezone = pytz.timezone(branch.timezone)
            # table = TicketLog.objects.filter(
            #     Q(ticket=ticket),
            # ).order_by('logtime')
            report_text = 'Ticket Type report' + '\n' \
            + 'Date range: ' + l_startdate + ' to ' + l_enddate + '\n' \
            + 'Branch: ' + branch.name + '(' + branch.bcode + ')\n'
            if ticketformat == None:
                report_text = report_text + 'Ticket Type: ALL'
            else:
                report_text = report_text + 'Ticket Type: ' + ticketformat.ttype

            task = t_Report_TicketType.apply_async(args=[utc_startdate, utc_enddate, report_text, branch.bcode, ticketformat_id_list], countdown=0)  # 'countdown' time delay in second before execute
            task_id = task.id
            ptask_id = task_id.replace('-', '_')

            url_download = ''

            context = {'task_id': ptask_id}
            context = context | {'app_name':APP_NAME}
            context = context | {'wsh' : wsHypertext}
            context = context | {'url_download': url_download}
            context_mini = getcontext_mini(request)
            context = context_mini | context
            return render(request, 'base/in_progress.html', context)
        else:
            messages.error(request, error)
            return redirect('reports')
    else :        
        # long process is done output result to HTML
        # task id is result_task_id        
        task_id = result_task_id.replace('_', '-')
        task = AsyncResult(task_id, app=t_Report_TicketType)
        status, header, report_table, report_text, bcode = task.get()

        if request.method != 'POST':
            # Pagination
            table100 = None
            page = request.GET.get('page') if request.GET.get('page') != None else '1'
            page = int(page)
            per_page = 100  # Number of items per page

            paginator = Paginator(report_table, per_page)
            try:
                table100 = paginator.page(page)
            except PageNotAnInteger:
                table100 = paginator.page(1)
            except EmptyPage:
                table100 = paginator.page(paginator.num_pages) 

            context = {
            'app_name':APP_NAME,
            'task_id': result_task_id,
            # 'localtimezone':localtimezone,
            'text':report_text,
            'header':header,
            'table':table100,        
            }
            context_mini = getcontext_mini(request)
            context = context_mini | context
            return render(request, 'base/r-result.html', context)
        elif request.method == 'POST':
            action = request.POST.get('action')
            if action == 'excel':
                # convert list (report_table) to string
                # querystr = pickle.dumps(report_table.query)
                
                # print(querystr)
                filename = 'tickettype_' 
                task = export_report.apply_async(args=[header,report_table,report_text, bcode ,filename], countdown=0)  # 'countdown' time delay in second before execute
                task_id = task.id
                ptask_id = task_id.replace('-', '_')
                filename = filename + ptask_id + '.csv'
                
                # download path
                url_download = static('download/' + bcode + '/' + filename)

                context = {'task_id': ptask_id}
                context = context | {'wsh' : wsHypertext} 
                context = context | {'url_download': url_download}
                context = {'aqs_version':aqs_version} | {'app_name':APP_NAME} | context 
                return render(request, 'base/in_progress.html', context)    
@unauth_user
@allowed_users(allowed_roles=['admin','support','supervisor','manager','reporter'])
def Report_TicketTypeDay(request):
    error = ''
    
    result_task_id = request.GET.get('result') if request.GET.get('result') != None else ''

    if result_task_id == '':
        branch = None
        ticketformat = None
        bcode = request.GET.get('branch') if request.GET.get('branch') != None else ''
        tickettype = request.GET.get('tickettype') if request.GET.get('tickettype') != None else ''
        l_startdate = request.GET.get('startdate') if request.GET.get('startdate') != None else ''
        l_enddate = request.GET.get('enddate') if request.GET.get('enddate') != None else ''
        result_task_id = request.GET.get('result') if request.GET.get('result') != None else ''

        s_startdate = l_startdate + ' 00:00:00.000000'
        # convert to datetime
        d_startdate = datetime.strptime(s_startdate, '%Y-%m-%d %H:%M:%S.%f')
        s_enddate = l_enddate + ' 23:59:59.999999'
        # convert to datetime
        d_enddate = datetime.strptime(s_enddate, '%Y-%m-%d %H:%M:%S.%f')
        # convert to UTC
        utc_startdate = funLocaltoUTC(d_startdate, 'UTC')
        utc_enddate = funLocaltoUTC(d_enddate, 'UTC')

        # check input data
        if error == '': 
            try:
                branch = Branch.objects.get(bcode=bcode)
            except:
                error = 'Error : Branch not found.'
        if error == '':
            if tickettype == '':
                error = 'Error : Ticket Type is blank.'
        if error == '':
            if tickettype != '':
                try:
                    ticketformat = TicketFormat.objects.filter(ttype=tickettype, branch=branch).first()
                except:
                    error = 'Error : Ticket Format not found.'
        if error == '':
            if d_enddate < d_startdate :
                error = 'Error : Start datetime > End datetime.'
        if error == '':
            if (d_enddate - d_startdate).days > 100 :
                error = 'Error : Date range do not more then 100 days.'

        if error == '':
            ticketformat_id_list = []

            ticketformat_id_list.append(ticketformat.pk)
        if error == '':
            # result_task_id = ''
            # localtimezone = pytz.timezone(branch.timezone)
            # table = TicketLog.objects.filter(
            #     Q(ticket=ticket),
            # ).order_by('logtime')
            report_text = 'Ticket Type report' + '\n' \
            + 'Date range: ' + l_startdate + ' to ' + l_enddate + '\n' \
            + 'Branch: ' + branch.name + '(' + branch.bcode + ')\n'
            if ticketformat == None:
                report_text = report_text + 'Ticket Type: ALL'
            else:
                report_text = report_text + 'Ticket Type: ' + ticketformat.ttype

            task = t_Report_TicketType_day.apply_async(args=[utc_startdate, utc_enddate, report_text, branch.bcode, ticketformat_id_list], countdown=0)  # 'countdown' time delay in second before execute
            task_id = task.id
            ptask_id = task_id.replace('-', '_')

            url_download = ''

            context = {'task_id': ptask_id}
            context = context | {'app_name':APP_NAME}
            context = context | {'wsh' : wsHypertext}
            context = context | {'url_download': url_download}
            context_mini = getcontext_mini(request)
            context = context_mini | context
            return render(request, 'base/in_progress.html', context)
        else:
            messages.error(request, error)
            return redirect('reports')
    else :        
        # long process is done output result to HTML
        # task id is result_task_id        
        task_id = result_task_id.replace('_', '-')
        task = AsyncResult(task_id, app=t_Report_TicketType)
        status, header, report_table, report_text, bcode = task.get()

        if request.method != 'POST':
            # Pagination
            table100 = None
            page = request.GET.get('page') if request.GET.get('page') != None else '1'
            page = int(page)
            per_page = 100  # Number of items per page

            paginator = Paginator(report_table, per_page)
            try:
                table100 = paginator.page(page)
            except PageNotAnInteger:
                table100 = paginator.page(1)
            except EmptyPage:
                table100 = paginator.page(paginator.num_pages) 

            context = {
            'app_name':APP_NAME,
            'task_id': result_task_id,
            # 'localtimezone':localtimezone,
            'text':report_text,
            'header':header,
            'table':table100,        
            }
            context_mini = getcontext_mini(request)
            context = context_mini | context
            return render(request, 'base/r-result.html', context)
        elif request.method == 'POST':
            action = request.POST.get('action')
            if action == 'excel':
                # convert list (report_table) to string
                # querystr = pickle.dumps(report_table.query)
                
                # print(querystr)
                filename = 'tickettype_' 
                task = export_report.apply_async(args=[header,report_table,report_text, bcode ,filename], countdown=0)  # 'countdown' time delay in second before execute
                task_id = task.id
                ptask_id = task_id.replace('-', '_')
                filename = filename + ptask_id + '.csv'
                
                # download path
                url_download = static('download/' + bcode + '/' + filename)

                context = {'task_id': ptask_id}
                context = context | {'wsh' : wsHypertext} 
                context = context | {'url_download': url_download}
                context = {'aqs_version':aqs_version} | {'app_name':APP_NAME} | context 
                return render(request, 'base/in_progress.html', context)    


@unauth_user
@allowed_users(allowed_roles=['admin','support','supervisor','manager','reporter'])
def Reports(request):

    context = getcontext(request, request.user)

    # get ticketformats from context
    auth_ticketformats = context['ticketformats']
    auth_countertype = context['countertypes']
    
    ttdict = {}
    # ttdict format: { tickettype : {lang1: 'name1', lang2: 'name2'} }
    for tf in auth_ticketformats:
        # check the tickettype is in the dict
        if tf.ttype not in ttdict:
            ttdict[tf.ttype] = {}
            ttdict[tf.ttype]['lang1'] = tf.touchkey_lang1
            ttdict[tf.ttype]['lang2'] = tf.touchkey_lang2
        
    now_l = datetime.now()
    snow_l = now_l.strftime('%Y-%m-%d')
    
    context = context | {'now':snow_l, 'tickettypes':ttdict, 'countertypes':auth_countertype}

    return render(request, 'base/r-main_standard.html', context)

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

        cs = CounterStatus.objects.filter(Q(countertype=ct)).order_by('countertype', ) \
        .extra(select={'casted_object_id': 'CAST(counternumber AS INTEGER)'}).extra(order_by = ['casted_object_id'])
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
    context_mini = getcontext_mini(request)
    context = context_mini | context
    return render(request, 'base/supervisor.html', context)


@unauth_user
@allowed_users(allowed_roles=['admin','support','supervisor','manager','reporter'])
def SuperVisorListView(request):  
    
    context = getcontext(request, request.user)
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

    context_mini = getcontext_mini(request)
    context = context_mini | context
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

    context_mini = getcontext_mini(request)
    context = context_mini | context
    return render(request, 'base/delete.html', context)

@unauth_user
@allowed_users(allowed_roles=['admin','support','supervisor','manager'])
def TicketRouteUpdateView(request, pk):
    route = TicketRoute.objects.get(id=pk)
       
    auth_branchs = getcontext(request, request.user)['branchs']
    
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

    context_en = getcontext_en(request)
    context = context_en | context

    return render(request, 'base/route-update.html', context)


@unauth_user
@allowed_users(allowed_roles=['admin','support','supervisor','manager'])
def TicketRouteSummaryView(request):  
    
    context = getcontext(request, request.user)
    return render(request, 'base/routes.html', context)

@unauth_user
@allowed_users(allowed_roles=['admin','support','supervisor','manager'])
def TicketFormatNewView(request):

    context_en = getcontext(request, request.user)
    auth_branchs = context_en['branchs']
    
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
    context = context_en | context
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
    context_mini = getcontext_mini(request)
    context = context_mini | context
    return render(request, 'base/delete.html', context)

@unauth_user
@allowed_users(allowed_roles=['admin','support','supervisor','manager'])
def TicketFormatUpdateView(request, pk):
    ticketformat = TicketFormat.objects.get(id=pk)

    auth_branchs = getcontext(request, request.user)['branchs']

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
    context_en = getcontext_en(request)
    context = context_en | context
    return render(request, 'base/tf-update.html', context)

@unauth_user
@allowed_users(allowed_roles=['admin','support','supervisor','manager'])
def TicketFormatSummaryView(request):
    
    context = getcontext(request, request.user)
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
        s_smsenabled = request.GET['SMSenabled']
    except:
        s_smsenabled = 'off'   
    if s_smsenabled == 'on':
        new_smsenabled = True
    else:
        new_smsenabled  = False  

    new_SMSmsg = request.GET['SMSmsg']
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
        branch.SMSenabled = new_smsenabled
        branch.SMSmsg = new_SMSmsg
        
    if result == '' :
        branch.save()
        datetime_now = datetime.now(timezone.utc)
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
@allowed_users(allowed_roles=['admin','support','supervisor','manager'])
def SettingsUpdateView(request, pk):
    branch = Branch.objects.get(id=pk)
    bcode = branch.bcode
    branchname = branch.name
    countertypes = CounterType.objects.filter(Q(branch=branch))
    subend = branch.subend
    subend = funUTCtoLocal(subend, branch.timezone).strftime('%Y-%m-%d %H:%M:%S')
    subscribe = branch.subscribe
    
    userright = 'counter'
    if request.user.is_superuser == True :
        userright = 'admin'
    elif request.user.groups.filter(name='admin').exists() == True :
        userright = 'admin'
    elif request.user.groups.filter(name='support').exists() == True :
        userright = 'support'
    elif request.user.groups.filter(name='supervisor').exists() == True :
        userright = 'supervisor'
    elif request.user.groups.filter(name='manager').exists() == True :
        userright = 'manager'
    elif request.user.groups.filter(name='reporter').exists() == True :
        userright = 'reporter'
    else:
        userright = 'counter'
       
    # print(userright)
    if request.method == 'POST':
        if userright == 'admin':
            branchsettingsform = BranchSettingsForm_Admin(request.POST, instance=branch, prefix='branchsettingsform')
            # print('branchsettingsform.bookingNewEmailUser.all()')
            # print(branchsettingsform.fields['bookingNewEmailUser'].value.values_list('username', flat=True))
        elif userright == 'support' or userright == 'supervisor':
            branchsettingsform = BranchSettingsForm_Adv(request.POST, instance=branch, prefix='branchsettingsform')
        elif userright == 'manager': 
            branchsettingsform = BranchSettingsForm_Basic(request.POST, instance=branch, prefix='branchsettingsform')
        error = ''
        error, bsf = checkbranchsettingsform(branchsettingsform)
        
        # print branch.bookingNewEmailUser list username
        # print(branch.bookingNewEmailUser.all().values_list('username', flat=True))

        # print bsf bookingNewEmailUser list username
        # print(bsf.bookingNewEmailUser.all().values_list('username', flat=True))


        if error == '':
            try:
                
                bsf.save()
                branchsettingsform.save_m2m()
                # print bsf bookingNewEmailUser list username
                # print(branch.bookingNewEmailUser.all().values_list('username', flat=True))

                datetime_now = datetime.now(timezone.utc)
                sch_shutdown(branch, datetime_now)
            except:
                error = 'An error occurcd during updating Branch settings'
        # regenrate user auth function : Queue, CRM, Booking
        userps = UserProfile.objects.all()
        for userp in userps:
            branchs = userp.branchs.all()
            if branch in branchs:                
                funRegenUserFunctions(userp.user)
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
        if userright == 'admin':
            branchsettingsform = BranchSettingsForm_Admin(instance=branch, prefix='branchsettingsform')
        elif userright == 'support' or userright == 'supervisor':
            branchsettingsform = BranchSettingsForm_Adv(instance=branch, prefix='branchsettingsform')
        elif userright == 'manager': 
            branchsettingsform = BranchSettingsForm_Basic(instance=branch, prefix='branchsettingsform')

    context = {'bcode':bcode,
               'branchname':branchname , 'countertypes':countertypes, 
               'branchsettingsform':branchsettingsform, 
               'subend':subend , 'subscribe':subscribe}

    context_mini = getcontext_mini(request)
    context = context_mini | context
    return render(request, 'base/settings-update.html', context)

@unauth_user
@allowed_users(allowed_roles=['admin','support','supervisor','manager'])
def SettingsSummaryView(request):  

    context = getcontext(request, request.user)
    return render(request, 'base/settings.html', context)

@unauth_user
def homeView(request):

    context = getcontext(request, request.user)

    context = context
    return render(request, 'base/home.html', context)

@unauth_user
@allowed_users(allowed_roles=['admin','support','supervisor','manager'])
def UserSummaryView(request):     
    
    context = getcontext(request, request.user)
    auth_userlist_active = context['users_active']
    auth_grouplist = context['grouplist']
    auth_profilelist  = context['profilelist']

    context = context | {'users_active':auth_userlist_active}
    context = context | {'profiles':auth_profilelist}
    context = context | {'auth_grouplist':auth_grouplist}
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

    context = getcontext(request, request.user)
    auth_userlist = context['users']
    # auth_userlist_active = context['users_active']
    # auth_grouplist = context['grouplist']
    # auth_profilelist  = context['profilelist']
    auth_ticketformats = context['ticketformats']

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

    context = context | {'q': q}
    context = context | {'qactive':q_active}
    context = context | {'qbranch':q_branch}
    context = context | {'qtt':q_tt}
    context = context | {'qgroup':q_group}
    context = context | {'result_users':result_userlist}

    return render(request, 'base/user_details.html', context)

def UserLogoutView(request):   
    logout(request)
    return redirect('login')

@unauth_user_login
def UserLoginView(request):
    context = {}
    page = 'login'
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        username = request.POST.get('username').lower()
        password = request.POST.get('password')
        human = True

        if RECAPTCHA_ENABLED == True :
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
        if RECAPTCHA_ENABLED == True :
            captchaform = CaptchaForm()
        pass

    context_mini = getcontext_mini(request)
    context = context_mini | context

    context = context | {'page':page} 
    if RECAPTCHA_ENABLED == True :
        context = context | {'captcha_form':captchaform}
    return render(request, 'base/login_register.html', context)
    
@unauth_user
@allowed_users(allowed_roles=['admin','support','supervisor','manager'])
def UserUpdateView(request, pk):

    temp_context = getcontext(request, request.user)
    auth_branchs = temp_context['branchs']
    auth_grouplist = temp_context['grouplist']


    user = User.objects.get(id=pk)
    userp = UserProfile.objects.get(user__exact=user)
    error = ''

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
        if request.user.is_superuser == True or request.user.groups.filter(name='admin').exists() == True:
            profileform = UserProfileFormAdmin(instance=userp, prefix='pform', auth_branchs=auth_branchs)
        
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
        if request.user.is_superuser == True or request.user.groups.filter(name='admin').exists() == True:
            profileform = UserProfileFormAdmin(request.POST, instance=userp, prefix='pform', auth_branchs=auth_branchs)

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

            # regenrate user auth function : Queue, CRM, Booking
            funRegenUserFunctions(user)

            # profileform_temp = profileform.save(commit=False)
            # profileform_temp.tickettype = profileform_temp.tickettype.upper()
            # profileform_temp.branchs = profileform.branchs
            
            # profileform_temp.save()
            messages.success(request, 'Profile was successfully updated!')
            return redirect('usersummary')
        else:
            messages.error(request, error)

    context =  {'userform':userform , 'profileform':profileform, 'user':user, 'userp':userp,'ticketformat':ticketformat2,'userptt':listusertt, }
    context_en = getcontext_en(request)
    context = context_en | context
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
    context_mini = getcontext_mini(request)
    context = context_mini | context
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
    context_mini = getcontext_mini(request)
    context = context_mini | context
    return render(request, 'base/usernew.html', context)

@unauth_user
@allowed_users(allowed_roles=['admin','support','supervisor','manager'])
def UserNewView2(request, pk):
    user = User.objects.get(id=pk)
    userp = UserProfile.objects.get(user__exact=user)

    context_temp = getcontext(request, request.user)
    auth_en_queue = context_temp['en_queue']
    auth_en_crm = context_temp['en_crm']
    auth_en_booking = context_temp['en_booking']
    aqs_version = context_temp['aqs_version']
    auth_branchs = context_temp['branchs']
    auth_grouplist = context_temp['grouplist']


    if request.method == 'POST':
        if request.user.is_superuser == True :
            userform = UserFormSuper(request.POST, instance=user, prefix='uform', auth_grouplist=auth_grouplist)
        elif user == request.user:
            userform = UserFormAdminSelf(request.POST, instance=user, prefix='uform')        
        elif request.user.groups.filter(name='admin').exists() == True :
            userform = UserFormAdmin(request.POST, instance=user, prefix='uform', auth_grouplist=auth_grouplist)            
        elif request.user.groups.filter(name='support').exists() == True :
            userform = UserFormSupport(request.POST, instance=user, prefix='uform', auth_grouplist=auth_grouplist)
        elif request.user.groups.filter(name='manager').exists() == True :
            userform = UserFormManager(request.POST, instance=user, prefix='uform', auth_grouplist=auth_grouplist)
        else :
            userform = UserForm(request.POST, instance=user, prefix='uform', auth_grouplist=auth_grouplist)

        profileform = UserProfileForm(request.POST, instance=userp, prefix='pform', auth_branchs=auth_branchs)
        if request.user.is_superuser == True or request.user.groups.filter(name='admin').exists() == True:
            profileform = UserProfileFormAdmin(request.POST, instance=userp, prefix='pform', auth_branchs=auth_branchs)

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
            userform = UserFormSuper(instance=user, prefix='uform', auth_grouplist=auth_grouplist)
        elif user == request.user:
            userform = UserFormAdminSelf(instance=user, prefix='uform')
        elif request.user.groups.filter(name='admin').exists() == True :
            userform = UserFormAdmin(instance=user, prefix='uform', auth_grouplist=auth_grouplist)
        elif request.user.groups.filter(name='support').exists() == True :
            userform = UserFormSupport(instance=user, prefix='uform', auth_grouplist=auth_grouplist)
        elif request.user.groups.filter(name='manager').exists() == True :
            userform = UserFormManager(instance=user, prefix='uform', auth_grouplist=auth_grouplist)
        else :
            userform = UserForm(instance=user, prefix='uform', auth_grouplist=auth_grouplist)            

        profileform = UserProfileForm(instance=userp, prefix='pform', auth_branchs=auth_branchs)
        if request.user.is_superuser == True or request.user.groups.filter(name='admin').exists() == True:
            profileform = UserProfileFormAdmin(instance=userp, prefix='pform', auth_branchs=auth_branchs)
    context =  {'user':user , 'userp':userp, 'userform':userform, 'profileform':profileform, 'auth_grouplist':auth_grouplist}
    context = {
            'aqs_version':aqs_version,
            'en_queue':auth_en_queue, 'en_crm':auth_en_crm, 'en_booking':auth_en_booking,
            } | context 
    return render(request, 'base/usernew2.html', context)

@unauth_user
@allowed_users(allowed_roles=['admin','support','supervisor','manager'])
def UserNewView3(request, pk):
    user = User.objects.get(id=pk)
    userp = UserProfile.objects.get(user__exact=user)

    context_temp = getcontext(request, request.user)
    auth_en_queue = context_temp['en_queue']
    auth_en_crm = context_temp['en_crm']
    auth_en_booking = context_temp['en_booking']
    aqs_version = context_temp['aqs_version']
    auth_branchs = context_temp['branchs']


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
        if request.user.is_superuser == True or request.user.groups.filter(name='admin').exists() == True:
            profileform = UserProfileFormAdmin(request.POST, instance=userp, prefix='pform', auth_branchs=auth_branchs)
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
        if request.user.is_superuser == True or request.user.groups.filter(name='admin').exists() == True:
            profileform = UserProfileFormAdmin(instance=userp, prefix='pform', auth_branchs=auth_branchs)
    context =  {'profileform':profileform, 'user':user, 'userp':userp,'ticketformat':ticketformat2,'userptt':listusertt, }
    context = {
            'aqs_version':aqs_version,
            'en_queue':auth_en_queue, 'en_crm':auth_en_crm, 'en_booking':auth_en_booking,
            } | context 
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
    context_mini = getcontext_mini(request)
    context = context_mini | context
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
    context_mini = getcontext_mini(request)
    context = context_mini | context 
    return render(request, 'base/delete.html', context)

@unauth_user
@allowed_users(allowed_roles=['admin','support','supervisor','manager'])
def UserResetView(request, pk):
    user = User.objects.get(id=pk)

    if request.user == user :
        messages.error(request, 'You can not reset password yourself!')
        return redirect('usersummary')   

    # check user group auth
    
    # auth_en_queue, auth_en_crm, auth_en_booking, \
    # auth_branchs , \
    # auth_userlist, \
    # auth_userlist_active, \
    # auth_grouplist, \
    # auth_profilelist, \
    # auth_ticketformats , \
    # auth_routes, \
    # auth_countertype, \
    # auth_timeslots, \
    # auth_bookings, \
    # auth_timeslottemplist, \
    # auth_memberlist, \
    # auth_customerlist, \
    # auth_quotations, \
    # auth_invoices, \
    # auth_receipts, \
    # auth_suppliers, \
    # = auth_data(request.user)
    context_temp = getcontext(request, request.user)
    auth_en_queue = context_temp['en_queue']
    auth_en_crm = context_temp['en_crm']
    auth_en_booking = context_temp['en_booking']
    aqs_version = context_temp['aqs_version']
    auth_userlist = context_temp['users']    

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
    context_en = getcontext_en(request)
    context = context_en | context
    return render(request, 'base/reset.html', context)


def MenuView(request):

    context = getcontext(request, request.user)
        
    # context =  {'users':auth_userlist , 'branchs':auth_branchs, 'ticketformats':auth_ticketformats, 'routes':auth_routes, 'timeslots':auth_timeslots, 'bookings':auth_bookings, 'temp':auth_timeslottemplist}
    context_en = getcontext_en(request)
    context = context_en | context
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
    datetime_now =datetime.now(timezone.utc)
    userprofile = UserProfile.objects.get(user=user)
    auth_en_queue = userprofile.enabled_queue
    auth_en_crm = userprofile.enabled_crm
    auth_en_booking = userprofile.enabled_booking

    auth_memberlist = Member.objects.all()
    auth_customerlist = Customer.objects.all()
    auth_bookings = Booking.objects.filter(~Q(status=Booking.STATUS.DELETED)).annotate(bookingtoqueue=Value(False, output_field=BooleanField()))
    auth_quotations = Quotation.objects.filter(Q(company=userprofile.company)).order_by('-created')
    auth_invoices = Invoice.objects.filter(Q(company=userprofile.company)).order_by('-created')
    auth_receipts = Receipt.objects.filter(Q(company=userprofile.company)).order_by('-created')
    auth_suppliers = Supplier.objects.filter(Q(company=userprofile.company)).order_by('-created')
    auth_products = Product.objects.filter(Q(company=userprofile.company))
    auth_producttypes = Product_Type.objects.filter(Q(company=userprofile.company))
    auth_categorys = Category.objects.filter(Q(company=userprofile.company))

    # add column for bookingtoqueue
    auth_bookings = auth_bookings.annotate(bookingforceontime=Value(False, output_field=BooleanField()))
    for booking in auth_bookings :
        booking.bookingtoqueue = True
        if booking.branch.queueenabled == False :
            booking.bookingtoqueue = False
        if booking.branch.bookingToQueueEnabled == False :
            booking.bookingtoqueue = False
        booking.bookingforceontime = False
        if booking.branch.bookingForceOnTime == True :
            booking.bookingforceontime = True
        booking.save()

    if user.is_superuser == True :
        auth_en_queue = True
        auth_en_crm = True
        auth_en_booking = True

        auth_profilelist = UserProfile.objects.all()
        auth_userlist = User.objects.all()
        auth_grouplist = Group.objects.all()
        auth_userlist_active = User.objects.filter(Q(is_active=True))
        # auth_userlist_active = User.objects.filter(Q(is_active=True)).exclude(Q(groups__name='web'))
        auth_branchs = Branch.objects.all()
        auth_ticketformats = TicketFormat.objects.all().order_by('branch','ttype')
        auth_routes = TicketRoute.objects.all().order_by('branch','countertype', 'tickettype', 'step')
        auth_countertype = CounterType.objects.all()
        
        # add column for active to True
        auth_timeslots_active = TimeSlot.objects.filter(Q(start_date__gte=datetime_now))\
            .annotate(active=Value(True, output_field=BooleanField()))
        # add column for active to False
        auth_timeslots_disactive = TimeSlot.objects.filter(Q(start_date__lt=datetime_now))\
            .annotate(active=Value(False, output_field=BooleanField()))
        auth_timeslots = auth_timeslots_disactive.union(auth_timeslots_active).order_by('branch', 'start_date')

        # auth_bookings = Booking.objects.filter(~Q(status=Booking.STATUS.DELETED))
        auth_timeslottemplist = TimeslotTemplate.objects.all()
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
        # add column for active to True
        auth_timeslots_active = TimeSlot.objects.filter(Q(start_date__gte=datetime_now))\
            .annotate(active=Value(True, output_field=BooleanField()))
        # add column for active to False
        auth_timeslots_disactive = TimeSlot.objects.filter(Q(start_date__lt=datetime_now))\
            .annotate(active=Value(False, output_field=BooleanField()))
        auth_timeslots = auth_timeslots_disactive.union(auth_timeslots_active).order_by('branch', 'start_date')

        auth_timeslottemplist = TimeslotTemplate.objects.all()

        # # add column for bookingtoqueue
        # auth_bookings = Booking.objects.filter(~Q(status=Booking.STATUS.DELETED)).annotate(bookingtoqueue=Value(False, output_field=BooleanField()))
                
        # for booking in auth_bookings :
        #     booking.bookingtoqueue = True
        #     logger.info("checking")
        #     if booking.branch.queueenabled == False :
        #         booking.bookingtoqueue = False
        #         logger.info('booking.branch.queueenabled = ' + str(booking.branch.queueenabled))
        #     if booking.branch.bookingToQueueEnabled == False :
        #         booking.bookingtoqueue = False
        #         logger.info('booking.branch.bookingToQueueEnabled = ' + str(booking.branch.bookingToQueueEnabled))

    else : 
        profid_list = []
        userid_list = []
        grouplist = []
        # if user.groups.filter(name='admin').exists() == True :
        #     auth_branchs = Branch.objects.all()
        #     auth_grouplist = Group.objects.all()
        auth_branchs = UserProfile.objects.get(user=user).branchs.all()
        if user.groups.filter(name='support').exists() == True :
            auth_branchs = Branch.objects.all()
            grouplist.append('support')
            grouplist.append('supervisor')
            grouplist.append('manager')
            grouplist.append('reporter')
            grouplist.append('counter')
        elif user.groups.filter(name='supervisor').exists() == True :
            grouplist.append('supervisor')
            grouplist.append('manager')
            grouplist.append('reporter')
            grouplist.append('counter')
        elif user.groups.filter(name='manager').exists() == True :
            grouplist.append('manager')
            grouplist.append('reporter')
            grouplist.append('counter')        
        elif user.groups.filter(name='reporter').exists() == True :
            grouplist.append('reporter')
            grouplist.append('counter')           
        elif user.groups.filter(name='counter').exists() == True :
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
       
        temp_list = userid_list.copy()
        for pk in temp_list :
            # take out superuser
            if User.objects.get(id=pk).is_superuser == True :
                userid_list.remove(pk)
                profid_list.remove(UserProfile.objects.get(user__exact=pk).id) 
            # remove user is group 'web' in userlist
            if User.objects.get(id=pk).groups.filter(name='web').exists() == True :
                userid_list.remove(pk)
                profid_list.remove(UserProfile.objects.get(user__exact=pk).id)
            # remove user is group 'api' in userlist
            if User.objects.get(id=pk).groups.filter(name='api').exists() == True :
                userid_list.remove(pk)
                profid_list.remove(UserProfile.objects.get(user__exact=pk).id)

        # auth_userlist = User.objects.filter(id__in=userid_list).exclude(Q(Group__name='web'))
        auth_userlist = User.objects.filter(id__in=userid_list)            
        auth_userlist_active = auth_userlist.filter(Q(is_active=True))
        auth_profilelist = UserProfile.objects.filter(id__in=profid_list)
        auth_ticketformats = TicketFormat.objects.filter(branch__in=auth_branchs).order_by('branch','ttype')
        auth_routes = TicketRoute.objects.filter(branch__in=auth_branchs).order_by('branch','countertype', 'tickettype', 'step')
        auth_countertype = CounterType.objects.filter(branch__in=auth_branchs)
        auth_grouplist = Group.objects.filter(name__in=grouplist)
        # sort auth_grouplist by name
        auth_grouplist = auth_grouplist.order_by('name')

        # add column for active to True
        auth_timeslots_active = TimeSlot.objects.filter(Q(start_date__gte=datetime_now),Q(branch__in=auth_branchs))\
            .annotate(active=Value(True, output_field=BooleanField()))
        # add column for active to False
        auth_timeslots_disactive = TimeSlot.objects.filter(Q(start_date__lt=datetime_now),Q(branch__in=auth_branchs))\
            .annotate(active=Value(False, output_field=BooleanField()))
        auth_timeslots = auth_timeslots_disactive.union(auth_timeslots_active).order_by('branch', 'start_date')

        auth_timeslottemplist = TimeslotTemplate.objects.filter(Q(branch__in=auth_branchs))

        # auth_bookings = auth_bookings.filter(Q(branch__in=auth_branchs))
        # remove booking not in auth_branchs
        for booking in auth_bookings :
            if booking.branch not in auth_branchs :
                auth_bookings = auth_bookings.exclude(id=booking.id)
        
        if userprofile.company == None :
            auth_memberlist = Member.objects.filter(Q(company=None))
            auth_customerlist = Customer.objects.filter(Q(company=None))
        else:
            auth_memberlist = Member.objects.filter(Q(company=userprofile.company))
            auth_customerlist = Customer.objects.filter(Q(sales=user))

        auth_quotations = Quotation.objects.filter(Q(sales=user)).order_by('-created')
        auth_invoices = Invoice.objects.filter(Q(sales=user)).order_by('-created')
        auth_receipts = Receipt.objects.filter(Q(sales=user)).order_by('-created')
        # auth_suppliers = Supplier.objects.filter(Q(sales=user)).order_by('-created')
        
    return(
            auth_en_queue,
            auth_en_crm,
            auth_en_booking,
            auth_branchs, 
            auth_userlist, auth_userlist_active,
            auth_grouplist, 
            auth_profilelist, 
            auth_ticketformats, 
            auth_routes, 
            auth_countertype, 
            auth_timeslots,
            auth_bookings,
            auth_timeslottemplist,
            auth_memberlist,
            auth_customerlist,
            auth_quotations,
            auth_invoices,
            auth_receipts,
            auth_suppliers,
            auth_products,
            auth_producttypes,
            auth_categorys,
            )

def getcontext(request, user, context=None):
    if context == None :
        context = {}

    auth_en_queue, auth_en_crm, auth_en_booking, \
    auth_branchs , \
    auth_userlist, \
    auth_userlist_active, \
    auth_grouplist, \
    auth_profilelist, \
    auth_ticketformats , \
    auth_routes, \
    auth_countertype, \
    auth_timeslots, \
    auth_bookings, \
    auth_timeslottemplist, \
    auth_memberlist, \
    auth_customerlist, \
    auth_quotations, auth_invoices, auth_receipts, auth_suppliers, \
    auth_products, auth_producttypes, auth_categorys, \
    = auth_data(request.user)

    logo, navbar_title, css, webtvlogo, webtvcss, eticketlink = funDomain(request)
    context = context | {
        'app_name':APP_NAME,
        'logo':logo,
        'navbar_title':navbar_title,
        'css':css,
        'aqs_version':aqs_version, 
        'en_queue':auth_en_queue, 'en_crm':auth_en_crm, 'en_booking':auth_en_booking,
        'users':auth_userlist, 'users_active':auth_userlist_active, 'grouplist':auth_grouplist, 'profilelist':auth_profilelist,
        'branchs':auth_branchs, 
        'ticketformats':auth_ticketformats, 
        'routes':auth_routes, 
        'countertypes':auth_countertype,
        'timeslots':auth_timeslots, 
        'bookings':auth_bookings,
        'temps':auth_timeslottemplist,
        'members':auth_memberlist,
        'customers':auth_customerlist,
        'quotations':auth_quotations,
        'invoices':auth_invoices,
        'receipts':auth_receipts,
        'suppliers':auth_suppliers,
        'products':auth_products,
        'producttypes':auth_producttypes,
        'productstatus':Product.STATUS,
        'categorys':auth_categorys,
        }    

    return context


def getcontext_mini(request):
    logo, navbar_title, css, webtvlogo, webtvcss, eticketlink = funDomain(request)
    context = {
        'app_name':APP_NAME,
        'aqs_version':aqs_version,
        'logo':logo,
        'navbar_title':navbar_title,
        'css':css,        
    }

    return context

def getcontext_en(request):

    auth_data = getcontext(request, request.user)
    auth_en_queue = auth_data['en_queue']
    auth_en_crm = auth_data['en_crm']
    auth_en_booking = auth_data['en_booking']

    logo, navbar_title, css, webtvlogo, webtvcss, eticketlink = funDomain(request)

    context = {
        'app_name':APP_NAME,
        'aqs_version':aqs_version,
        'logo':logo,
        'navbar_title':navbar_title,
        'css':css,        
        'en_queue':auth_en_queue, 
        'en_crm':auth_en_crm, 
        'en_booking':auth_en_booking,
        }
    return context

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
    if error == '':
        if newform.voice_volume < 0 or newform.voice_volume > 100 :
            error = 'An error occurcd : Voice volume should be 0-100.'
    return (error, newform)


def PrivacyView(request):
    return render(request, 'base/privacy.html')