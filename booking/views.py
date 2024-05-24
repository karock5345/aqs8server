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
from base.models import UserProfile, Branch, SubTicket
from .forms import TimeSlotForm, TimeSlotNewForm, DetailsForm, BookingForm, BookingNewForm
from django.utils.timezone import localtime, get_current_timezone
import pytz
from django.utils import timezone
from base.views import auth_data

import logging
from aqs.tasks import *
from base.api.views import funUTCtoLocal, funLocaltoUTC, funUTCtoLocaltime, funLocaltoUTCtime
from datetime import datetime
from .serializers import tsSerializer
import phonenumbers
import phonenumbers.timezone
import re
from aqs.tasks import sendemail
from django.template.loader import render_to_string
from django.db import transaction

logger = logging.getLogger(__name__)

@unauth_user
def BookingNewView(request):

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
    = auth_data(request.user)

    form = BookingNewForm(auth_branchs=auth_branchs)

    if request.method == 'POST':
        form = BookingNewForm(request.POST, auth_branchs=auth_branchs)
        
        error = ''
        errorTC = ''
        error, newform = checkbookingform(form)
            
        if error == '' :
            phone_number = phonenumbers.parse('+' + newform.mobilephone_country + newform.mobilephone)
            # add booking by user (not customer), it is no email and SMS to customer confirm
            error, errorTC = chainBookNow(newform.timeslot, newform.name, phone_number, newform.email, request.user, None)
        if error == '' :
            messages.success(request, 'Created new Booking.')
            return redirect('bookingsummary')
        if error != '':
            messages.error(request, error)

    # get the url of 'bookingtimeslot'
    back_url = reverse('bookingsummary')
    context = {'form':form}
    context = {
                'aqs_version':aqs_version,
                'en_queue':auth_en_queue, 'en_crm':auth_en_crm, 'en_booking':auth_en_booking,
                'title':'New Booking', 'back_url':back_url, 
                } | context 
    return render(request, 'base/new.html', context)

@unauth_user
def BookingDelView(request, pk):
    utcnow = timezone.now()
    booking = Booking.objects.get(id=pk) 
  
    if request.method =='POST':
        # the is fake delete, the booking will be set to 'deleted' status
        booking.status = Booking.STATUS.DELETED
        booking.save()

        # get the new timeslot and create a log
        funBookingLog(utcnow, booking.timeslot, booking, TimeSlot.ACTION.NULL, Booking.STATUS.NULL, request.user, None)

              
        messages.success(request, 'Time Slot was successfully deleted!') 
        return redirect('bookingsummary')
    context = {'obj':booking, 'text':'Warning: This action will delete the Booking.'}
    context = {'aqs_version':aqs_version} | context 
    return render(request, 'base/delete.html', context)
@unauth_user
def BookingUpdateView(request, pk):
    utcnow = timezone.now()
    booking = Booking.objects.get(id=pk)    

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
    = auth_data(request.user)

    if request.method == 'POST':
        bookingform = BookingForm(request.POST, instance=booking, prefix='bookingform', auth_branchs=auth_branchs)
        error = ''
        # check the form
        error, newform = checkbookingform(bookingform)
        
        if error == '' :         
            try :
                newform.save()
                # change user to current user
                # timeslot.user = request.user
                # timeslot.save()
                messages.success(request, 'Booking was successfully updated!')
                funBookingLog(utcnow, booking.timeslot, booking, TimeSlot.ACTION.NULL, Booking.STATUS.CHANGED, request.user, None)
                
                return redirect('bookingsummary')
            except:
                error = 'An error occurcd during updating Booking'

            

        if error != '':
            messages.error(request, error )
                
    else:
        bookingform = BookingForm(instance=booking, prefix='bookingform', auth_branchs=auth_branchs)
    context =  {'bookingform':bookingform, 'booking':booking, }
    context = {
                'aqs_version':aqs_version,
                'en_queue':auth_en_queue, 'en_crm':auth_en_crm, 'en_booking':auth_en_booking,
               } | context 
    return render(request, 'booking/booking_update.html', context)

@unauth_user
def BookingSummaryView(request):
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
    = auth_data(request.user)

 
    context = {
        'users':auth_userlist, 
        'users_active':auth_userlist_active, 
        'profiles':auth_profilelist, 
        'branchs':auth_branchs, 
        'ticketformats':auth_ticketformats, 
        'routes':auth_routes,
        'timeslots':auth_timeslots,
        'bookings':auth_bookings,
        }
    
    if request.method == 'POST':
        action = None
        pk = None
        booking = None
        action_list = ['confirm', 'reject', 'start', 'late', 'noshow', 'queue', 'complete']
        error = ''
        for a in action_list:
            if request.POST.get(a) != None:
                action = a
                pk = request.POST.get(a)
                try:
                    booking = Booking.objects.get(id=pk)
                except:
                    error = 'Booking not found'
                break
        if error == '':
            if action == None:
                error = 'No action selected'
        if error == '':
            if pk == None:
                error = 'No booking index'
        if error == '':
            utcnow = timezone.now()
            if action == 'confirm':
                booking = Booking.objects.get(id=pk)
                booking.status = Booking.STATUS.CONFIRMED
                booking.save()
                # get the new timeslot and create a log
                funBookingLog(utcnow, booking.timeslot, booking, TimeSlot.ACTION.NULL, Booking.STATUS.CONFIRMED, request.user, None)
            elif action == 'reject':
                booking = Booking.objects.get(id=pk)
                booking.status = Booking.STATUS.REJECTED
                booking.save()

                # release the slot
                booking.timeslot.slot_available = booking.timeslot.slot_available + 1
                booking.timeslot.slot_using = booking.timeslot.slot_using - 1
                booking.timeslot.save()

                funBookingLog(utcnow, booking.timeslot, booking, TimeSlot.ACTION.NULL, Booking.STATUS.REJECTED, request.user, None)
            elif action == 'start':
                booking = Booking.objects.get(id=pk)
                booking.status = Booking.STATUS.STARTED
                booking.save()
                # get the new timeslot and create a log
                funBookingLog(utcnow, booking.timeslot, booking, TimeSlot.ACTION.NULL, Booking.STATUS.STARTED, request.user, None)
                # member will marked as 'on time'
            elif action == 'late':
                booking = Booking.objects.get(id=pk)
                booking.status = Booking.STATUS.LATED
                booking.save()
                # get the new timeslot and create a log
                funBookingLog(utcnow, booking.timeslot, booking, TimeSlot.ACTION.NULL, Booking.STATUS.LATED, request.user, None)
                # member will marked as 'late'
            elif action == 'noshow':
                booking = Booking.objects.get(id=pk)
                booking.status = Booking.STATUS.NOSHOW
                booking.save()
                # get the new timeslot and create a log
                funBookingLog(utcnow, booking.timeslot, booking, TimeSlot.ACTION.NULL, Booking.STATUS.NOSHOW, request.user, None)
            elif action == 'queue':
                # Booking to queue
                error, tickettempid = bookingtoqueue(utcnow, booking, request.user)
                if error == '':
                    # get the new timeslot and create a log
                    funBookingLog(utcnow, booking.timeslot, booking, TimeSlot.ACTION.NULL, Booking.STATUS.QUEUE, request.user, None)

                
            elif action == 'complete':
                booking = Booking.objects.get(id=pk)
                booking.status = Booking.STATUS.COMPLETED
                booking.save()
                # get the new timeslot and create a log
                funBookingLog(utcnow, booking.timeslot, booking, TimeSlot.ACTION.NULL, Booking.STATUS.COMPLETED, request.user, None)
            

        if error != '': 
            messages.error(request, error)
            
            
    context = {
                'aqs_version':aqs_version,
                'en_queue':auth_en_queue, 'en_crm':auth_en_crm, 'en_booking':auth_en_booking,
               } | context 
    return render(request, 'booking/booking.html', context)

@transaction.atomic
def bookingtoqueue(utcnow, booking:Booking, user):
    error = ''
    tickettempid = None
    # datetime_now_local = funUTCtoLocal(datetime_now, booking.branch.timezone)
    ticketformat = None
    # str_now = datetime_now_local.strftime('%Y-%m-%d %H:%M:%S')

    if error == '':
        if booking.branch.bookingenabled == False:
            error = 'Booking function is disabled'
    if error == '':
        if booking.branch.queueenabled == False:
            error = 'Queue function is disabled'
    if error == '':
        if booking.branch.bookingToQueueEnabled == False:
            error = 'Booking to Queue function is disabled'
    
    if error == '' :
        # ticket format
        ticketobj = TicketFormat.objects.filter( Q(branch=booking.branch) & Q(for_booking=True))
        if ticketobj.count() == 0:
            error =  'TicketFormat not found (for_booking=True)'

    if error == '':
        # Lock the ticket format nowait=False
        try:
            ticketformat = TicketFormat.objects.select_for_update().get(id=ticketobj[0].id)
        except Exception as e:
            error = e.__str__()
    if error == '' :
        if ticketformat.enabled == False :
            error = 'Ticket disabled'
    
    if error == '' :
        # check booking status
        if booking.status != Booking.STATUS.CONFIRMED:
            error = 'Booking status is not confirmed'

    if error == '':
        # new ticket for booking to queue
        
        itype = 0 # sub ticket type 0=A, 1=B, 2=C ...
        booking_score = 0

        # lated is the time difference between now and booking timeslot start date by minutes
        # lated > 0 is lated 
        # lated = 0 is on time
        # lated < 0 is early
        lated = int((utcnow - booking.timeslot.start_date).total_seconds() / 60.0)
        if lated == 0:
            itype = 0
        elif lated > 0:
            # bookingToQueueOnTimeRangeLate (10 mins. default)
            # bookingToQueueLateUnit (5 mins. default)
            # if lated within bookingToQueueOnTimeRangeLate, the ticket not 'late'
            
            if lated > booking.branch.bookingToQueueOnTimeRangeLate:
                itype = int((lated - booking.branch.bookingToQueueOnTimeRangeLate - 1) / booking.branch.bookingToQueueLateUnit) + 1
                if itype < 0:
                    itype = 0
        elif lated < 0:
            lated = lated * -1
            if lated < booking.branch.bookingToQueueOnTimeRangeEarly:
                itype = int((lated - booking.branch.bookingToQueueOnTimeRangeEarly - 1) / booking.branch.bookingToQueueLateUnit) + 1
            lated = lated * -1
        if itype > 25 :
            itype = 25

        # sub ticket type 0=A, 1=B, 2=C ...
        subType = chr(itype + 65)
        isubTicketNo = 0


        # get the last ticket number
        subticketobj = SubTicket.objects.filter(Q(branch=booking.branch) & Q(booking_tickettype=subType))
        if subticketobj.count() == 0:
            # create new sub ticket
            subticket = SubTicket.objects.create(
                branch = booking.branch,
                booking_tickettype = subType,
                ticketnext = 2,
                )

            isubTicketNo = 1
        else:
            subticket_id = subticketobj[0].pk
            # Lock the sub ticket nowait=False
            try:
                subticket = SubTicket.objects.select_for_update().get(id=subticket_id)
            except Exception as e:
                error = e.__str__()
            isubTicketNo = subticket.ticketnext
            subticket.ticketnext = subticket.ticketnext + 1
            subticket.save()
      
        # create new ticket
        if error == '':
            # isubTicketNo
            # subType
            # ticketformat
            # booking_score
            # booking.timeslot.start_date = booking time 
            # utcnow = current time
            pass

        # change booking status to 'queue'
        # booking = Booking.objects.get(id=pk)
        # booking.status = Booking.STATUS.QUEUE
        # booking.save()
            




    return error, tickettempid
    
# version 8.3.0 add transaction select_for_update for prevent 'double bookings' problem
@transaction.atomic
def chainBookNow(timeslot, name, phone_number:phonenumbers, email, user, member):
    # check slot
    error = ''
    error_TC = ''
    utcnow = timezone.now()

    if error == '':
        # Lock the timeslot nowait=False
        try:
            timeslot = TimeSlot.objects.select_for_update().get(id=timeslot.id)
        except Exception as e:
            error = e.__str__()
            error_TC = e.__str__()
       

    if error == '':
        if timeslot.slot_available <= 0:
            error = 'No slot available'
            error_TC = '沒有可用時段, 請選擇其他時段'
    if error == '':
        timeslot.slot_available = timeslot.slot_available - 1
        timeslot.slot_using = timeslot.slot_using + 1
        timeslot.save()

        phone_number_national = ''
        phone_number_country = ''
        if phone_number != '':
            phone_number_national = phone_number.national_number
            phone_number_country = str(phone_number.country_code)
        booking = Booking.objects.create(
            branch = timeslot.branch,
            timeslot = timeslot,
            user = user,
            member = member,
            
            status = Booking.STATUS.NEW,

            name = name, 
            email = email, 
            mobilephone_country = phone_number_country,
            mobilephone = phone_number_national,
            )
        # print(booking.status)
        # aget the new timeslot and create a log
        funBookingLog(utcnow, timeslot, booking, TimeSlot.ACTION.NULL, Booking.STATUS.NEW, user, member)
    return error, error_TC

def Booking_Details_ClientView(request, pk):
    error = ''
    error_TC = ''
    name = ''
    mphone = ''
    email = ''
    phone_number =''
    context = {}
    logofile = ''
    css = ''
    bcode = ''
    scrolling = ''
    booking_str = ''
    success_str = ''

    # booking_str = \
    # '請輸入 電郵 或 手機號碼(香港)' + '\n' + \
    # '我們發送確認信給你'

    try:
        timeslot = TimeSlot.objects.get(id=pk)
        logofile = timeslot.branch.webtvlogolink
        css = timeslot.branch.webtvcsslink
        bcode = timeslot.branch.bcode
        booking_str = timeslot.branch.bookingPage2Text
        scrolling = timeslot.branch.bookingPage2ScrollingText

        startdate = funUTCtoLocal(timeslot.start_date, timeslot.branch.timezone)
        date_str = startdate.strftime('%Y-%m-%d' )
        time_str = startdate.strftime('%I:%M %p')
        week_str = funWeekStr(startdate)

        success_str = timeslot.branch.bookingPage3Text
    except:
        error = 'TimeSlot not found'
        error_TC = '沒有找到時段'

    if error != '':
        return HttpResponse(error)    
    if error == '':
        if request.method == 'POST':
            action = request.POST.get('action')
            if action == 'submit_booknow':
                form = DetailsForm(request.POST)
                name:str = form['name'].value()
                mphone = form['mphone'].value()
                email = form['email'].value()

                # print(pk, name, mphone, email)

                # check input data
                if error == '':
                    if email + mphone == '' :
                        error = 'Mobile or Email are required'
                        error_TC = '手提電話或電郵地址是必需的'
                if error == '':
                    maxlen = 10
                    if name.isascii() == True:
                        maxlen = 20
                    if len(name) > maxlen:
                        error = 'Name is too long (max. 20 characters)'
                        error_TC = '名字太長 (中文最多10個字元)'
                if error == '':
                    if mphone != '':
                        if len(mphone) == 8 and mphone.isdigit() == True:
                            mphone = '+852' + mphone
                        # check mobile first 3 digits is '852'
                        if mphone[0:3] == '852':
                            # add '+' from mobile
                            mphone = '+' + mphone                
                        try:
                            phone_number = phonenumbers.parse(mphone)
                        except:
                            error = 'Mobile format is incorrect'
                            error_TC = '手提電話格式不正確'
                        if error == '':
                            if phonenumbers.is_valid_number(phone_number) == False:
                                error = 'Mobile format is incorrect'
                                error_TC = '手提電話格式不正確'
                        if error == '':
                            if phone_number.country_code != 852:
                                error = 'Mobile should be Hong Kong number'
                                error_TC = '手提電話必須是香港號碼'
                
                if error == '':
                    if email != '':
                    # check email format
                        regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b'
                        if(re.fullmatch(regex, email)):
                            pass       
                        else:
                            error = 'Email format is incorrect'
                            error_TC = '電郵地址格式不正確'

                if error == '':
                    error, error_TC = chainBookNow(timeslot, name, phone_number, email, request.user, None)
                    pass

                if error == '':
                    # send email to customer
                    if timeslot.branch.bookingSuccessEmailEnabled == True:
                        if email != '':
                            subject = timeslot.branch.bookingSuccessEmailSubject
                            subject = subject.replace( '[[ADDR]]', timeslot.branch.address)
                            subject = subject.replace( '[[NAME]]', name)
                            subject = subject.replace( '[[DATE]]', date_str)
                            subject = subject.replace( '[[WEEK]]', week_str)
                            subject = subject.replace( '[[TIME]]', time_str)
                            
                            email_str = timeslot.branch.bookingSuccessEmailBody
                            email_str = email_str.replace( '[[ADDR]]', timeslot.branch.address)
                            email_str = email_str.replace( '[[NAME]]', name)
                            email_str = email_str.replace( '[[DATE]]', date_str)
                            email_str = email_str.replace( '[[WEEK]]', week_str)
                            email_str = email_str.replace( '[[TIME]]', time_str)

                            message = render_to_string('booking/email_booking_confirmed.html', {
                                'title': subject,
                                'body': email_str,                        
                            })
                            message = message.replace('amp;', '')

                            sendemail.delay(subject, message, email,)

                    # send email to admin
                    if timeslot.branch.bookingNewEmailEnabled == True:
                        users = timeslot.branch.bookingNewEmailUser
                        for u in users.all():
                            if u.email == '' or u.email == None:
                                pass
                            else :
                                subject = timeslot.branch.bookingNewEmailSubject
                                subject = subject.replace( '[[ADDR]]', timeslot.branch.address)
                                subject = subject.replace( '[[NAME]]', name)
                                subject = subject.replace( '[[DATE]]', date_str)
                                subject = subject.replace( '[[WEEK]]', week_str)
                                subject = subject.replace( '[[TIME]]', time_str)
                                subject = subject.replace( '[[PHONE]]', mphone)
                                subject = subject.replace( '[[EMAIL]]', email)
                                subject = subject.replace( '[[BNAME]]', timeslot.branch.name)
                                subject = subject.replace( '[[BCODE]]', timeslot.branch.bcode)
                                subject = subject.replace( '[[USER]]', u.first_name)
                                
                                email_str = timeslot.branch.bookingNewEmailBody
                                email_str = email_str.replace( '[[ADDR]]', timeslot.branch.address)
                                email_str = email_str.replace( '[[NAME]]', name)
                                email_str = email_str.replace( '[[DATE]]', date_str)
                                email_str = email_str.replace( '[[WEEK]]', week_str)
                                email_str = email_str.replace( '[[TIME]]', time_str)
                                email_str = email_str.replace( '[[PHONE]]', mphone)
                                email_str = email_str.replace( '[[EMAIL]]', email)
                                email_str = email_str.replace( '[[BNAME]]', timeslot.branch.name)
                                email_str = email_str.replace( '[[BCODE]]', timeslot.branch.bcode)
                                email_str = email_str.replace( '[[USER]]', u.first_name)                        

                                message = render_to_string('booking/email_booking_new.html', {
                                    'title': subject,
                                    'body': email_str,                        
                                })
                                message = message.replace('amp;', '')
                                sendemail.delay(subject, message, u.email,)

                    # send SMS to customer
                    if timeslot.branch.SMSenabled == True and timeslot.branch.bookingSMSSuccessEnabled == True:
                        if timeslot.branch.bookingenabled == True:
                            if phone_number != '':
                                mphone_sms = str(phone_number.country_code) + str(phone_number.national_number)
                                sms_str = timeslot.branch.bookingSMSSuccess
                                sms_str = sms_str.replace( '[[DATE]]', date_str)
                                sms_str = sms_str.replace( '[[TIME]]', time_str)

                                sendSMS.delay(mphone_sms, sms_str, timeslot.branch.bcode, 'Booking Confirmation')

                    success_str = success_str.replace( '[[ADDR]]', timeslot.branch.address)
                    success_str = success_str.replace( '[[NAME]]', name)
                    success_str = success_str.replace( '[[DATE]]', date_str)
                    success_str = success_str.replace( '[[WEEK]]', week_str)
                    success_str = success_str.replace( '[[TIME]]', time_str)
                    
                    context = {
                        'aqs_version':aqs_version,
                        'logofile' : logofile,
                        'css' : css,
                        'text':success_str,
                        }
                    return render(request, 'booking/booking_success_client.html', context)
                    

                if error != '':

                    # if error == 'No slot available' redirect to 'appointment' branch.bcode

                    # Error message
                    messages.error(request, error_TC)
                    messages.error(request, error)
        
                # if phone_number != '' :
                #     print(phonenumbers.is_valid_number(phone_number))
                #     print(phonenumbers.timezone.time_zones_for_number(phone_number))
                #     print('Country code:' + str(phone_number.country_code))
                #     print('National number:' + str(phone_number.national_number))
                



        sometext = 'This is a test'
        context = {
            'logofile' : logofile,
            'css' : css,
            'scroll': scrolling,
            'text': booking_str,
            'id':timeslot.id,
            'date':date_str,
            'time':time_str,
            'week':week_str,
            'sometext':sometext,
            'name':name,
            'mphone':mphone,
            'email':email,
            'bcode':bcode,
        }

        context = {'aqs_version':aqs_version} | context
        return render(request, 'booking/booking_details_client.html', context)
        


def BookingClientView(request, bcode):
    # http://127.0.0.1:8000/booking/KB/
    context = {}
    error = ''
    str_now = '---'
    logofile = ''
    booking_str = ''
    scrolling = ''

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
            
            scrolling = branch.bookingPage1ScrollingText
            scrolling = scrolling.replace( '[[ADDR]]', branch.address)

            booking_str = branch.bookingPage1Text
            booking_str = booking_str.replace( '[[ADDR]]', branch.address)
        else :
            error = 'Branch not found.'


    if error == '' :
        now_utc = timezone.now()

        tslist = TimeSlot.objects.filter(Q(branch=branch) & Q(enabled=True) & Q(slot_available__gt=0) & Q(show_end_date__gte=now_utc) & Q(show_date__lte=now_utc)).order_by('start_date')

        tsserializers  = tsSerializer(tslist, many=True)
        timeslots = tsserializers.data


        context = {
        'lastupdate' : str_now,
        'timeslots' : timeslots,
        'logofile' : logofile,
        'css' : css,
        'scroll': scrolling,
        'text': booking_str,
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
    return render(request , 'booking/booking_client.html', context)



@unauth_user
@allowed_users(allowed_roles=['admin','support','supervisor','manager'])
def TimeSlotDelView(request, pk):
    utcnow = timezone.now()
    timeslot = TimeSlot.objects.get(id=pk) 
  
    if request.method =='POST':
        # change user to current user
        timeslot.user = request.user
        timeslot.save()

        # get the new timeslot and create a log
        funBookingLog(utcnow, timeslot, None, TimeSlot.ACTION.DELETED, Booking.STATUS.NULL, request.user, None)

        timeslot.delete()       
        messages.success(request, 'Time Slot was successfully deleted!') 
        return redirect('bookingtimeslot')
    context = {'obj':timeslot, 'text':'Warning: This action will delete the Time Slot and all related data. Recommanded to use "Disable" instead of "Delete".'}
    context = {'aqs_version':aqs_version} | context 
    return render(request, 'base/delete.html', context)

@unauth_user
@allowed_users(allowed_roles=['admin','support','supervisor','manager'])
def TimeSlotNewView(request):

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
    = auth_data(request.user)

    tsform = TimeSlotNewForm(auth_branchs=auth_branchs)

    if request.method == 'POST':
        utcnow = timezone.now()
        tsform = TimeSlotNewForm(request.POST, auth_branchs=auth_branchs)
        
        error = ''
        error, newform = checktimeslotform(tsform)
        

        if error == '' :
            try:
                newform.save()
                # change user to current user
                newform.user = request.user

                newform.slot_using = 0
                newform.slot_available = newform.slot_total

                newform.save()

                # get the new timeslot and create a log
                timeslot = TimeSlot.objects.get(id=newform.id)
                funBookingLog(utcnow, timeslot, None, TimeSlot.ACTION.NEW,  Booking.STATUS.NULL, request.user, None)

                messages.success(request, 'Created new Time Slot.')
            except:
                error = 'An error occurcd during new Time Slot creation'          

            return redirect('bookingtimeslot')
        if error != '':
            messages.error(request, error)

    # get the url of 'bookingtimeslot'
    back_url = reverse('bookingtimeslot')
    context = {'form':tsform}
    context = {
                'aqs_version':aqs_version,
                'en_queue':auth_en_queue, 'en_crm':auth_en_crm, 'en_booking':auth_en_booking,
               } | context     
    context = {'title':'New Time Slot', 'back_url':back_url, } | context 
    return render(request, 'base/new.html', context)



@unauth_user
@allowed_users(allowed_roles=['admin','support','supervisor','manager'])
def TimeSlotUpdateView(request, pk):
    timeslot = TimeSlot.objects.get(id=pk)    

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
    = auth_data(request.user)

    if request.method == 'POST':
        utcnow = timezone.now()
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
                funBookingLog(utcnow, timeslot, None, TimeSlot.ACTION.CHANGED, Booking.STATUS.NULL, request.user, None)
                
                return redirect('bookingtimeslot')
            except:
                error = 'An error occurcd during updating TimeSlot'

            

        if error != '':
            messages.error(request, error )
                
    else:
        tsform = TimeSlotForm(instance=timeslot, prefix='timeslotform', auth_branchs=auth_branchs)
    context =  {'tsform':tsform, 'timeslot':timeslot, }
    context = {
                'aqs_version':aqs_version,
                'en_queue':auth_en_queue, 'en_crm':auth_en_crm, 'en_booking':auth_en_booking,
               } | context 
    return render(request, 'booking/timeslot_update.html', context)

@unauth_user
@allowed_users(allowed_roles=['admin','support','supervisor','manager'])
def TimeSlotSummaryView(request):
   

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
    = auth_data(request.user)
 
    context = {
        'users':auth_userlist, 
        'users_active':auth_userlist_active, 
        'profiles':auth_profilelist, 
        'branchs':auth_branchs, 
        'ticketformats':auth_ticketformats, 
        'routes':auth_routes,
        'timeslots':auth_timeslots,
        'bookings':auth_bookings,
        }
    context = {
                'aqs_version':aqs_version,
                'en_queue':auth_en_queue, 'en_crm':auth_en_crm, 'en_booking':auth_en_booking,
               } | context 
    return render(request, 'booking/timeslot.html', context)

def checktimeslotform(form):
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
        if newform.branch.enabled == False:
            error = 'Branch is disabled'            
    if error == '' :
        if newform.branch.bookingenabled == False:
            error = 'Booking function is disabled'
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

    return error, newform

def checkbookingform(form):
    error = ''
    errorTC = ''
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
        if newform.mobilephone_country == '' and newform.mobilephone == '':
            pass
        else:
            if newform.mobilephone_country == None :
                newform.mobilephone_country = ''
            if newform.mobilephone == None :
                newform.mobilephone = ''
            if newform.mobilephone_country + newform.mobilephone != '':
                error, errorTC, newphone_country, newphone = checkMphone(newform.mobilephone_country + newform.mobilephone)

                if error == '' :
                    newform.mobilephone_country = newphone_country
                    newform.mobilephone = newphone


    if error == '':
        if not(newform.email == '' or newform.email == None) :
        # check email format
            regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b'
            if(re.fullmatch(regex, newform.email)):
                pass       
            else:
                error = 'Email format is incorrect'
                error_TC = '電郵地址格式不正確'

    if error == '' :
        if newform.people < 1:
            error = 'People should be => 1'
    if error == '' :
        if newform.people > 100:
            error = 'People should be <= 100'
    
    return error, newform

def funBookingLog(now_time, timeslot, booking, action, status, user, member):

    logtext = ''
    logtext_t = ''
    logtext_b:str = ''
    branch = None
    if timeslot != None :
        branch = timeslot.branch
        bookingstart_str = funUTCtoLocal(timeslot.start_date, timeslot.branch.timezone).strftime('%Y-%m-%d %H:%M:%S' )
        bookingend_str = funUTCtoLocal(timeslot.end_date, timeslot.branch.timezone).strftime('%Y-%m-%d %H:%M:%S' )
        show_date_str = funUTCtoLocal(timeslot.show_date, timeslot.branch.timezone).strftime('%Y-%m-%d %H:%M:%S' )
        show_end_date_str = funUTCtoLocal(timeslot.show_end_date, timeslot.branch.timezone).strftime('%Y-%m-%d %H:%M:%S' )

        logtext_t = 'Branch:' + timeslot.branch.bcode + '\n'
        logtext_t += 'Booking Start Date (local time):' + bookingstart_str + '\n'
        logtext_t += 'Booking End Date (local time):' + bookingend_str + '\n'
        logtext_t += 'Show Date (local time):' + show_date_str + '\n'
        logtext_t += 'Show End Date (local time):' + show_end_date_str + '\n'
        logtext_t += 'Slot Using:' + str(timeslot.slot_using) + '\n'
        logtext_t += 'Slot Available:' + str(timeslot.slot_available) + '\n'
        logtext_t += 'Slot Total:' + str(timeslot.slot_total) + '\n' + '\n'

        if user == None:
            user = timeslot.user
    if booking != None :
        branch = booking.branch
        user_str = 'None'
        if booking.user != None:
            user_str = booking.user.username
            user = booking.user
        member_str = 'None'
        if booking.member != None:
            member_str = booking.member.username
            member = booking.member

        logtext_b = 'Status : ' + booking.status + '\n'
        logtext_b += 'Booking User : ' + user_str + '\n' 
        logtext_b += 'Booking Member : ' + member_str + '\n'
        logtext_b += 'Name : ' + booking.name + '\n'
        logtext_b += 'Email : ' + booking.email + '\n'
        logtext_b += 'Mobile : ' + str(booking.mobilephone_country) + ' ' + str(booking.mobilephone) + '\n'
        logtext_b += 'People : ' + str(booking.people) + '\n'
        logtext_b += 'Remark : ' + booking.remark + '\n'

    logtext = logtext_t + logtext_b
    BookingLog.objects.create(
        logtime = now_time,
        branch = branch,
        timeslot = timeslot, 
        booking = booking, 
        user = user, 
        member = member,
        logtext = logtext,
        timeslot_action = action, 
        booking_status = status,
        remark = None,
        )        
    return

def funWeekStr(inputdate:datetime) -> str:
    iWeek = inputdate.strftime('%w')
    week_str = ''
    if iWeek == '0':
        week_str = '星期日 Sun'
    elif iWeek == '1':
        week_str = '星期一 Mon'
    elif iWeek == '2':
        week_str = '星期二 Tue'
    elif iWeek == '3':
        week_str = '星期三 Wed'
    elif iWeek == '4':
        week_str = '星期四 Thu'
    elif iWeek == '5':
        week_str = '星期五 Fri'
    elif iWeek == '6':
        week_str = '星期六 Sat'
    return week_str

def checkMphone(mphone):
    error = ''
    error_TC = ''
    phone_number_national = ''
    phone_number_country = ''

    if mphone != '':
        if len(mphone) == 8 and mphone.isdigit() == True:
            mphone = '+852' + mphone
        # check mobile first 3 digits is '852'
        if mphone[0:3] == '852':
            # add '+' from mobile
            mphone = '+' + mphone                
        try:
            phone_number = phonenumbers.parse(mphone)
        except:
            error = 'Mobile format is incorrect'
            error_TC = '手提電話格式不正確'
        if error == '':
            if phonenumbers.is_valid_number(phone_number) == False:
                error = 'Mobile format is incorrect'
                error_TC = '手提電話格式不正確'
        if error == '':
            if phone_number.country_code != 852:
                error = 'Mobile should be Hong Kong number'
                error_TC = '手提電話必須是香港號碼'
        if error == '':
            phone_number_country = str(phone_number.country_code)
            phone_number_national = str(phone_number.national_number)


    return error, error_TC, phone_number_country, phone_number_national