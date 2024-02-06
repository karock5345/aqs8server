from aqs.settings import aqs_version
from django.shortcuts import render, redirect, HttpResponse
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.hashers import make_password
from django.db.models import Q
from django.contrib.auth.forms import UserCreationForm, PasswordChangeForm
# from datetime import datetime
from base.decorators import *
# from django.contrib.auth.views import PasswordChangeView
from django.urls import reverse_lazy, reverse

from .models import *
from base.models import UserProfile, Branch
from .forms import TimeSlotForm
from django.utils.timezone import localtime, get_current_timezone
import pytz
from django.utils import timezone
from base.views import auth_data

import logging
from aqs.tasks import *
from base.api.views import funUTCtoLocal, funLocaltoUTC, funUTCtoLocaltime, funLocaltoUTCtime
from .models import ACTION
from datetime import datetime
from .serializers import tsSerializer


logger = logging.getLogger(__name__)


def webAppointmentView(request, bcode):
    # http://127.0.0.1:8000/booking/KB/
    context = {}
    error = ''
    str_now = '---'
    logofile = ''

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


    if error == '' :
        now_utc = timezone.now()
        print(now_utc)
        tslist = TimeSlot.objects.filter(Q(branch=branch) & Q(enabled=True) & Q(slot_available__gt=0) & Q(show_end_date__gte=now_utc) & Q(show_date__lte=now_utc)).order_by('start_date')
        #tslist= []
        tsserializers  = tsSerializer(tslist, many=True)
        timeslots = tsserializers.data
        

        context = {
        'lastupdate' : str_now,
        'timeslots' : timeslots,
        'logofile' : logofile,
        'css' : css,
        'scroll': '維修請帶發票'
        }
        pass
    else :
        context = {
        'lastupdate' : str_now,
        'errormsg' : error,
        'logofile' : logofile,
        'css' : 'styles/styletv.css',
        }
        messages.error(request, error)




    context = context | {
    'bcode' :  bcode ,
    }
    
    context = {'aqs_version':aqs_version} | context 
    return render(request , 'booking/appointment.html', context)



@unauth_user
@allowed_users(allowed_roles=['admin','support','supervisor','manager'])
def TimeSlotDelView(request, pk):
 
    timeslot = TimeSlot.objects.get(id=pk) 
  
    if request.method =='POST':
        # change user to current user
        timeslot.user = request.user
        timeslot.save()

        # get the new timeslot and create a log
        funBookingLog(timeslot, None, A_DELETE)

        timeslot.delete()       
        messages.success(request, 'Time Slot was successfully deleted!') 
        return redirect('bookingtimeslot')
    context = {'obj':timeslot, 'text':'Warning: This action will delete the Time Slot and all related data. Recommanded to use "Disable" instead of "Delete".'}
    context = {'aqs_version':aqs_version} | context 
    return render(request, 'base/delete.html', context)

@unauth_user
@allowed_users(allowed_roles=['admin','support','supervisor','manager'])
def TimeSlotNewView(request):

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

    tsform = TimeSlotForm(auth_branchs=auth_branchs)

    if request.method == 'POST':
        tsform = TimeSlotForm(request.POST, auth_branchs=auth_branchs)
        
        error = ''
        error, newform = checktimeslotform(tsform)
        
        if error == '' :
            try:
                newform.save()
                # change user to current user
                newform.user = request.user
                newform.save()

                # get the new timeslot and create a log
                timeslot = TimeSlot.objects.get(id=newform.id)
                funBookingLog(timeslot, None, A_NEW)

                messages.success(request, 'Created new Time Slot.')
            except:
                error = 'An error occurcd during new Time Slot creation'          

            return redirect('bookingtimeslot')
        if error != '':
            messages.error(request, error)
    # get the url of 'bookingtimeslot'
    back_url = reverse('bookingtimeslot')
    context = {'form':tsform}
    context = {'aqs_version':aqs_version, 'title':'New Time Slot', 'back_url':back_url, } | context 
    return render(request, 'base/new.html', context)



@unauth_user
@allowed_users(allowed_roles=['admin','support','supervisor','manager'])
def TimeSlotUpdateView(request, pk):
    timeslot = TimeSlot.objects.get(id=pk)    

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

    if request.method == 'POST':
        tsform = TimeSlotForm(request.POST, instance=timeslot, prefix='timeslotform', auth_branchs=auth_branchs)
        error = ''
        error, newform = checktimeslotform(tsform)
        if error == '' :         
            try :
                newform.save()
                # change user to current user
                timeslot.user = request.user
                timeslot.save()
                messages.success(request, 'TimeSlot was successfully updated!')
                funBookingLog(timeslot, None, A_CHANGE)
                
                return redirect('bookingtimeslot')
            except:
                error = 'An error occurcd during updating TimeSlot'

            

        if error != '':
            messages.error(request, error )
                
    else:
        tsform = TimeSlotForm(instance=timeslot, prefix='timeslotform', auth_branchs=auth_branchs)
    context =  {'tsform':tsform, 'timeslot':timeslot, }
    context = {'aqs_version':aqs_version} | context 
    return render(request, 'booking/timeslot_update.html', context)

@unauth_user
@allowed_users(allowed_roles=['admin','support','supervisor','manager'])
def TimeSlotSummaryView(request):
   

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
 
    context = {
        'users':auth_userlist, 
        'users_active':auth_userlist_active, 
        'profiles':auth_profilelist, 
        'branchs':auth_branchs, 
        'ticketformats':auth_ticketformats, 
        'routes':auth_routes,
        'timeslots':auth_timeslots,
        }
    context = {'aqs_version':aqs_version} | context 
    return render(request, 'booking/timeslot.html', context)

def checktimeslotform(form):
    error = ''
    newform = None

    if form.is_valid() == False:
        error_string = ' '.join([' '.join(x for x in l) for l in list(form.errors.values())])
        error = 'An error occurcd during registration: '+ error_string
    
    if error == '' :
        newform = form.save(commit=False)
    if error == '':
        try:
            newform.start_date = funLocaltoUTC(newform.start_date, newform.branch.timezone)
        except:
            error = 'An error occurcd : Booking date is not correct'
    if error == '':
        try:
            newform.end_date = funLocaltoUTC(newform.end_date, newform.branch.timezone)
        except:
            error = 'An error occurcd : Booking date is not correct'            
    if error == '':
        try:
            newform.show_date = funLocaltoUTC(newform.show_date, newform.branch.timezone)
        except:
            error = 'An error occurcd : Show date is not correct'
    if error == '':
        try:
            newform.show_end_date = funLocaltoUTC(newform.show_end_date, newform.branch.timezone)
        except:
            error = 'An error occurcd : Show_end date is not correct'            
    if error == '' :
        if newform.branch == None :
            # Error branch is None
            error = 'Error Branch is blank'
    if error == '' :
        #  end_date < start_date
        if newform.end_date < newform.start_date :
            error = 'Booking END date should be greater than Booking START date'            
    if error == '' :
        #  show_date < show_date_end <= start_date
        if newform.show_date > newform.show_end_date :
            error = 'Show date end should be greater than show date'
    if error == '' :
        if newform.show_end_date > newform.start_date :
            error = 'Booking date should be greater than show date end'        
    if error == '' :
        if newform.slot_total < 0:
            error = 'Slot total should be => 0' 
    if error == '' :
        if newform.slot_available < 0 :
            error = 'Slot available should be => 0'

    return (error, newform)


def funBookingLog(timeslot, booking, action):
    if timeslot != None :
        bookingstart_str = funUTCtoLocal(timeslot.start_date, timeslot.branch.timezone).strftime('%Y-%m-%d %H:%M:%S' )
        bookingend_str = funUTCtoLocal(timeslot.end_date, timeslot.branch.timezone).strftime('%Y-%m-%d %H:%M:%S' )
        show_date_str = funUTCtoLocal(timeslot.show_date, timeslot.branch.timezone).strftime('%Y-%m-%d %H:%M:%S' )
        show_end_date_str = funUTCtoLocal(timeslot.show_end_date, timeslot.branch.timezone).strftime('%Y-%m-%d %H:%M:%S' )
        logtext = \
            'Branch:' + timeslot.branch.bcode + '\n' + \
            'Booking Start Date (local time):' + bookingstart_str + '\n' + \
            'Booking End Date (local time):' + bookingend_str + '\n' + \
            'Show Date (local time):' + show_date_str + '\n' + \
            'Show End Date (local time):' + show_end_date_str + '\n' + \
            'Slot Total:' + str(timeslot.slot_total) + '\n' + \
            'Slot Available:' + str(timeslot.slot_available) 
        

        BookingLog.objects.create(
            timeslot=timeslot, 
            booking=booking, 
            user=timeslot.user, 
            member = None,
            logtext = logtext,
            action=action, 
            remark = None,
            )
    return