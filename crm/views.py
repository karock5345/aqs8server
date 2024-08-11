from aqs.settings import APP_NAME, aqs_version
from django.shortcuts import render, redirect, HttpResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from base.decorators import allowed_users
from crm.models import Member
from base.models import Branch, APILog
import random
import string
from datetime import datetime, timedelta, timezone
from base.api.views import setting_APIlogEnabled, visitor_ip_address, loginapi_notoken, funUTCtoLocal, counteractive, checkuser
from base.views import auth_data
from django.http import JsonResponse
from django.shortcuts import redirect
from django.contrib import messages
from base.decorators import *
from django.db.models import Q

sort_direction = {}

# Create your views here.
def WelcomeView(request):
    content = {'user':request.user}
    return render(request, 'crm/welcome.html', content)

@unauth_user
def CustomerListView(request):
    return HttpResponse('CustomerListView')

@unauth_user
def QuotationView(request):
    return HttpResponse('QuotationView')

@unauth_user
def InvoiceView(request):
    return HttpResponse('InvoiceView')

@unauth_user
def ReceiptView(request):
    return HttpResponse('ReceiptView')

@unauth_user
def MemberListView(request):
    global sort_direction    

    q = request.GET.get('q') if request.GET.get('q') != None else ''
    q_active = request.GET.get('qactive') if request.GET.get('qactive') != None else 'all'
    q_verified = request.GET.get('qverified') if request.GET.get('qverified') != None else 'all'
    q_company = request.GET.get('qcompany') if request.GET.get('qcompany') != None else 'all'
    q_sort = request.GET.get('sort') if request.GET.get('sort') != None else ''
    
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
    auth_memberlist, \
    = auth_data(request.user)


    result_userlist = auth_memberlist
    # print(result_userlist.count())

    if q != '':
        result_userlist = result_userlist.filter(Q(username__icontains=q) 
                                             | Q(number__icontains=q) 
                                             | Q(nickname__icontains=q) 
                                             | Q(lastname__icontains=q) 
                                             | Q(firstname__icontains=q)
                                             | Q(mobilephone__icontains=q) 
                                             | Q(email__icontains=q) 
                                             )
    
    if q_active != '' and q_active != 'all':
        active_bool = True
        if q_active == 'inactive':
            active_bool = False
        result_userlist = result_userlist.filter(Q(enabled=active_bool))

    if q_verified != '' and q_verified != 'all':
        verified_bool = True
        if q_verified == 'unverified':
            verified_bool = False
        result_userlist = result_userlist.filter(Q(verified=verified_bool))

    if q_company == 'none':
        result_userlist = result_userlist.filter(Q(company=None))
    elif q_company != '' and q_company != 'all':
        result_userlist = result_userlist.filter(Q(company=q_company))


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
        result_userlist = result_userlist.order_by(direct + 'enabled')
    elif q_sort == 'verified':
        result_userlist = result_userlist.order_by(direct + 'verified')        
    elif q_sort == 'fname':
        result_userlist = result_userlist.order_by(direct + 'firstname')
    elif q_sort == 'lname':
        result_userlist = result_userlist.order_by(direct + 'lastname')
    elif q_sort == 'email':
        result_userlist = result_userlist.order_by(direct + 'email')
    elif q_sort == 'company':
        result_userlist = result_userlist.order_by(direct + 'company__name')
    elif q_sort == 'mobilephone':
        result_userlist = result_userlist.order_by(direct + 'mobilephone')
    elif q_sort == 'memberlevel':
        result_userlist = result_userlist.order_by(direct + 'memberlevel')
    elif q_sort == 'memberpoints':
        result_userlist = result_userlist.order_by(direct + 'memberpoints')



    context = {
        'app_name':APP_NAME,
        'aqs_version':aqs_version, 
        'en_queue':auth_en_queue, 'en_crm':auth_en_crm, 'en_booking':auth_en_booking,
        'users':auth_userlist, 
        'branchs':auth_branchs, 
        'ticketformats':auth_ticketformats, 
        'routes':auth_routes, 
        'timeslots':auth_timeslots, 
        'bookings':auth_bookings,
        'temps':auth_timeslottemplist,
        'members':auth_memberlist,
        }

    # context = {'users':auth_userlist, 
    #            'users_active':auth_userlist_active, 
    #            'profiles':auth_profilelist, 
    #            'auth_grouplist':auth_grouplist, 
    #            'branchs':auth_branchs, 
    #            'ticketformats':auth_ticketformats, 
    #            'routes':auth_routes, 
    #            'timeslots':auth_timeslots, 
    #            'bookings':auth_bookings, 
    #            'temp':auth_timeslottemplist,
    #     }
    context = context | {'q':q}
    context = context | {'qactive':q_active}
    context = context | {'qcompany':q_company}
    context = context | {'qverified':q_verified}
    context = context | {'result_members':result_userlist}
    

    return render(request, 'crm/memberlist.html', context)