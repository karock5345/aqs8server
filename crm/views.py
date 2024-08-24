from aqs.settings import APP_NAME, aqs_version
from django.shortcuts import render, redirect, HttpResponse
from django.urls import reverse
from django.db.models import Q
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from base.decorators import allowed_users
from base.models import Branch, APILog, UserProfile
from datetime import datetime, timedelta, timezone
from base.api.views import setting_APIlogEnabled, visitor_ip_address, loginapi_notoken, funUTCtoLocal, counteractive, checkuser
from base.views import auth_data
from django.http import JsonResponse
from django.contrib import messages
from base.decorators import *
from crm.models import Member, Company, Customer, CustomerGroup, CustomerSource, CustomerInformation
from crm.forms import MemberUpdateForm, MemberNewForm, CustomerUpdateForm, CustomerGroupForm, CustomerSourceForm, CustomerInfoForm
from crm.api import new_member

import re
from booking.views import checkMphone
from base.api.views import funUTCtoLocal, funLocaltoUTC, funUTCtoLocaltime, funLocaltoUTCtime

sort_direction = {}
sort_direction_cust = {}

# Create your views here.
def WelcomeView(request):
    content = {'user':request.user}
    return render(request, 'crm/welcome.html', content)

@unauth_user
def CustomerListView(request):
    global sort_direction_cust

    q = request.GET.get('q') if request.GET.get('q') != None else ''
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
    auth_customerlist, \
    auth_quotations, \
    = auth_data(request.user)


    result = auth_customerlist
    # print(result_userlist.count())

    userp = UserProfile.objects.filter(Q(user = request.user)).first()
    if userp != None:
        if userp.company == None:
            messages.error(request, 'Your are not assign Company' )            
            return redirect('home')

    if q != '':
        result = result.filter(Q(companyname__icontains=q) 
                                             | Q(contact__icontains=q) 
                                             | Q(address__icontains=q) 
                                             | Q(phone__icontains=q) 
                                             | Q(remark__icontains=q)
                                             | Q(email__icontains=q) 
                                             )
    
    direct = ''
    if q_sort != '':
        # find out the sort_list
        try:
            direct = sort_direction_cust[q_sort]
        except:
            direct = ''
            sort_direction_cust[q_sort] = ''
        if direct == '':
            sort_direction_cust[q_sort] = '-'
        elif direct == '-':
            sort_direction_cust[q_sort] = ''

    if q_sort == 'customer':
        result = result.order_by(direct + 'companyname')
    elif q_sort == 'contact':
        result = result.order_by(direct + 'contact')
    elif q_sort == 'email':
        result = result.order_by(direct + 'email')        
    elif q_sort == 'tel':
        result = result.order_by(direct + 'phone')
    elif q_sort == 'sales':
        result = result.order_by(direct + 'sales')

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
        'customers':auth_customerlist,
        'quotations':auth_quotations,
        } 
    context = context | {'q':q}
    context = context | {'result':result}
    context = context | {'company':userp.company}

    return render(request, 'crm/customerlist.html', context)


@unauth_user
def CustomerUpdateView(request, pk):
    utcnow = datetime.now(timezone.utc)
    customer = Customer.objects.get(id=pk)    
    company = customer.company
    # get full path with domain name
    full_path = request.build_absolute_uri()
    
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
    auth_customerlist, \
    auth_quotations, \
    = auth_data(request.user)

    if request.method == 'POST':
        action = request.POST.get('action')
        form = CustomerUpdateForm(request.POST, instance=customer, prefix='customerform', company=customer.company)

    # <---- Customer Group ----
        if action == 'group':
            table = CustomerGroup.objects.filter(Q(company=company))
            cgform = CustomerGroupForm()
            context = {'aqs_version':aqs_version,'table':table, 'form': cgform, 'company':company, 'customer':customer, 'back_url':full_path, 'title':'Manage Customer Group', 'action':'group'}
            return render(request, 'crm/sub_update.html', context)
        elif action == 'update_group':
            cgform = CustomerGroupForm(request.POST)
            if cgform.is_valid():
                # get the id of the customer group from the form
                pk = cgform['id'].value()
                cg = CustomerGroup.objects.get(pk=pk)

                cg.name = cgform['name'].value()
                cg.description = cgform['description'].value()
                cg.save()
                # cgform.save()
                messages.success(request, 'Update success' )
            table = CustomerGroup.objects.filter(Q(company=company))
            context = {'aqs_version':aqs_version, 'table':table, 'form': cgform, 'company':company, 'back_url':full_path, 'title':'Manage Customer Group', 'action':'group'}
            return render(request, 'crm/sub_update.html', context)
        elif action == 'new_group':
            CustomerGroup.objects.create(company=company, name='', description='')
            cgform = CustomerGroupForm(request.POST)

            table = CustomerGroup.objects.filter(Q(company=company))
            context = {'aqs_version':aqs_version, 'table':table, 'form': cgform, 'company':company, 'back_url':full_path, 'title':'Manage Customer Group', 'action':'group'}       
            return render(request, 'crm/sub_update.html', context, )
        elif action == 'del_group':
            cgform = CustomerGroupForm(request.POST)
            if cgform.is_valid():
                pk = cgform['id'].value()
                CustomerGroup.objects.get(pk=pk).delete()

            table = CustomerGroup.objects.filter(Q(company=company))
            context = {'aqs_version':aqs_version, 'table':table, 'form': cgform, 'company':company, 'back_url':full_path, 'title':'Manage Customer Group', 'action':'group'}
            return render(request, 'crm/sub_update.html', context, )        
    # ---- Customer Group ---->


    # <---- Customer Source ----
        elif action == 'source':
            table = CustomerSource.objects.filter(Q(company=company))
            csform = CustomerSourceForm()
            context = {'aqs_version':aqs_version,'table':table, 'form': csform, 'company':company, 'customer':customer, 'back_url':full_path, 'title':'Manage Customer Source', 'action':'source'}
            return render(request, 'crm/sub_update.html', context)
        elif action == 'update_source':
            csform = CustomerSourceForm(request.POST)
            if csform.is_valid():
                # get the id of the customer group from the form
                pk = csform['id'].value()
                source = CustomerSource.objects.get(pk=pk)

                source.name = csform['name'].value()
                source.description = csform['description'].value()
                source.save()
                messages.success(request, 'Update success' )
            table = CustomerSource.objects.filter(Q(company=company))
            context = {'aqs_version':aqs_version, 'table':table, 'form': csform, 'company':company, 'back_url':full_path, 'title':'Manage Customer Source', 'action':'source'}
            return render(request, 'crm/sub_update.html', context)
        elif action == 'new_source':
            CustomerSource.objects.create(company=company, name='', description='')
            csform = CustomerSourceForm(request.POST)

            table = CustomerSource.objects.filter(Q(company=company))
            context = {'aqs_version':aqs_version, 'table':table, 'form': csform, 'company':company, 'back_url':full_path, 'title':'Manage Customer Source', 'action':'source'}       
            return render(request, 'crm/sub_update.html', context, )
        elif action == 'del_source':
            csform = CustomerSourceForm(request.POST)
            if csform.is_valid():
                pk = csform['id'].value()
                CustomerSource.objects.get(pk=pk).delete()

            table = CustomerSource.objects.filter(Q(company=company))
            context = {'aqs_version':aqs_version, 'table':table, 'form': csform, 'company':company, 'back_url':full_path, 'title':'Manage Customer Source', 'action':'source'}
            return render(request, 'crm/sub_update.html', context, )        
    # ---- Customer Source ---->

    # <---- Customer Information ----
        elif action == 'information':
            table = CustomerInformation.objects.filter(Q(company=company))
            infoform = CustomerInfoForm()
            context = {'aqs_version':aqs_version,'table':table, 'form': infoform, 'company':company, 'customer':customer, 'back_url':full_path, 'title':'Manage Customer Information', 'action':'information'}
            return render(request, 'crm/sub_update.html', context)
        elif action == 'update_information':
            infoform = CustomerInfoForm(request.POST)
            if infoform.is_valid():
                # get the id of the customer group from the form
                pk = infoform['id'].value()
                info = CustomerInformation.objects.get(pk=pk)

                info.name = infoform['name'].value()
                info.description = infoform['description'].value()
                info.save()
                messages.success(request, 'Update success' )
            table = CustomerInformation.objects.filter(Q(company=company))
            context = {'aqs_version':aqs_version,'table':table, 'form': infoform, 'company':company, 'customer':customer, 'back_url':full_path, 'title':'Manage Customer Information', 'action':'information'}
            return render(request, 'crm/sub_update.html', context)
        elif action == 'new_information':
            CustomerInformation.objects.create(company=company, name='', description='')
            infoform = CustomerInfoForm(request.POST)

            table = CustomerInformation.objects.filter(Q(company=company))
            context = {'aqs_version':aqs_version,'table':table, 'form': infoform, 'company':company, 'customer':customer, 'back_url':full_path, 'title':'Manage Customer Information', 'action':'information'}
            return render(request, 'crm/sub_update.html', context, )
        elif action == 'del_information':
            infoform = CustomerInfoForm(request.POST)
            if infoform.is_valid():
                pk = infoform['id'].value()
                CustomerInformation.objects.get(pk=pk).delete()

            table = CustomerInformation.objects.filter(Q(company=company))
            context = {'aqs_version':aqs_version,'table':table, 'form': infoform, 'company':company, 'customer':customer, 'back_url':full_path, 'title':'Manage Customer Information', 'action':'information'}
            return render(request, 'crm/sub_update.html', context, )        
    # ---- Customer Information ---->

        elif action == 'member':
            return redirect('crmmember')

        elif action == 'update':
            # form = CustomerUpdateForm(request.POST, instance=customer, prefix='customerform')
            error = ''
            # check the form
            error, newform = checkcustomerform(form)
            
            if error == '' :         
                try :                
                    newform.save()

                    messages.success(request, 'Customer was successfully updated!')
                    
                    return redirect('crmcustomerlist')
                except:
                    error = 'An error occurcd during updating Customer'

            if error != '':
                messages.error(request, error )
                
    else:
        form = CustomerUpdateForm(instance=customer, prefix='customerform', company=customer.company)
    context =  {'form':form, 'customer':customer, }
    context = {
                'aqs_version':aqs_version,
                'en_queue':auth_en_queue, 'en_crm':auth_en_crm, 'en_booking':auth_en_booking,
               } | context 
    return render(request, 'crm/customer_update.html', context)


@unauth_user
def QuotationView(request):
    utcnow = datetime.now(timezone.utc)
    context = {}
    # company = customer.company
    # get full path with domain name
    full_path = request.build_absolute_uri()
    
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
    auth_customerlist, \
    auth_quotations, \
    = auth_data(request.user)

    quotation = None
    if auth_quotations.count() > 0:
        quotation = auth_quotations.first()
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
        'customers':auth_customerlist,
        'quotations':auth_quotations,
        }    
    context = {
                'aqs_version':aqs_version,
                'en_queue':auth_en_queue, 'en_crm':auth_en_crm, 'en_booking':auth_en_booking,
                'quotation':quotation, 
               } | context 
    return render(request, 'crm/quotation.html', context)

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
    auth_customerlist, \
    auth_quotations, \
    = auth_data(request.user)


    result_userlist = auth_memberlist
    # print(result_userlist.count())

    userp = UserProfile.objects.filter(Q(user = request.user)).first()
    if userp != None:
        if userp.company == None:
            messages.error(request, 'Your are not assign Company' )            
            return redirect('home')

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
        'customers':auth_customerlist,
        'quotations':auth_quotations,
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
    context = context | {'company':userp.company}

    return render(request, 'crm/memberlist.html', context)

@unauth_user
def MemberUpdateView(request, pk):
    utcnow = datetime.now(timezone.utc)
    member = Member.objects.get(id=pk)    

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
    auth_customerlist, \
    auth_quotations, \
    = auth_data(request.user)

    if request.method == 'POST':
        form = MemberUpdateForm(request.POST, instance=member, prefix='memberform')
        error = ''
        # check the form
        error, newform = checkmemberform(form)
        
        if error == '' :         
            try :                
                newform.save()
                # get the member just saved
                # member = Member.objects.get(id=pk)
                # member.user = request.user
                # member.save()
     
                messages.success(request, 'Member was successfully updated!')
                # funBookingLog(utcnow, booking.timeslot, booking, TimeSlot.ACTION.NULL, Booking.STATUS.CHANGED, request.user, None)
                
                return redirect('crmmember')
            except:
                error = 'An error occurcd during updating Member'

        if error != '':
            messages.error(request, error )
                
    else:
        form = MemberUpdateForm(instance=member, prefix='memberform')
    context =  {'form':form, 'member':member, }
    context = {
                'aqs_version':aqs_version,
                'en_queue':auth_en_queue, 'en_crm':auth_en_crm, 'en_booking':auth_en_booking,
               } | context 
    return render(request, 'crm/member_update.html', context)

@unauth_user
def MemberDelView(request, pk):
    utcnow = datetime.now(timezone.utc)
    member = Member.objects.get(id=pk) 
  
    if request.method =='POST':
        member.delete()       
        messages.success(request, 'Member was successfully deleted!') 
        return redirect('crmmember')
    context = {'obj':member, 'text':'Warning: This action will delete the Member.'}
    context = {'aqs_version':aqs_version} | context 
    return render(request, 'base/delete.html', context)


@unauth_user
def MemberNewView(request, ccode):
    error = ''
    status = {}

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
    auth_customerlist, \
    auth_quotations, \
    = auth_data(request.user)
    
    try:
        company = Company.objects.get(ccode=ccode)
        form = MemberNewForm(company=company)
    except:
        error = 'Company not found'
    
    if error == '':
        if request.method == 'POST':
            utcnow = datetime.now(timezone.utc)
            form = MemberNewForm(request.POST, company=company)
            # check birthday is 'YYYY-MM-DD' or 'YYYY-MM-DD HH:MM:SS'
            birthday = form['birthday'].value()
            # str_time = str(dob) + ' 00:00:00'
            # dob = datetime.strptime(str_time, "%Y-%m-%d %H:%M:%S")
            # rx_dob = funLocaltoUTC(dob, company.timezone)
            try:
                birthday = datetime.strptime(birthday, "%Y-%m-%d %H:%M:%S")
            except:
                str_time = str(birthday) + ' 00:00:00'
                birthday = datetime.strptime(str_time, "%Y-%m-%d %H:%M:%S")

            if form.is_valid() == True:
                status, error = new_member(
                            request, utcnow, 
                            company, form['username'].value(), form['password'].value(), True,
                            False, utcnow,
                            form['firstname'].value(), form['lastname'].value(), form['gender'].value(), form['email'].value(), '852', form['mobilephone'].value(),  form['nickname'].value(),
                            birthday, 
                            form['memberlevel'].value(), form['memberpoints'].value(), form['memberpointtotal'].value(),                       
                           )

            if error == '' :
                messages.success(request, 'Created new Member.')
                return redirect('crmmember')
    if error != '':
        messages.error(request, error)

    # get the url of 'bookingtimeslot'
    back_url = reverse('crmmember')
    context = {'form':form}
    context = {
                'aqs_version':aqs_version,
                'en_queue':auth_en_queue, 'en_crm':auth_en_crm, 'en_booking':auth_en_booking,
               } | context     
    context = {'title':'New Member', 'back_url':back_url, } | context 
    return render(request, 'base/new.html', context)



def checkmemberform(form):
    error = ''
    errorTC = ''
    newform = None

    if form.is_valid() == False:
        # error_string = ' '.join([' '.join(x for x in l) for l in list(form.errors.values())])
        error_string = ''
        for l in list(form.errors):
            errx = ''
            for x in form.errors[l]:
                errx = errx + ',' +  x
                # print(l , x)
            error_string = error_string + ' [' + l + '] ' + errx + '\n'
        error = 'An error occurcd during registration: ' + error_string
        

    if error == '' :
        newform = form.save(commit=False)

    if error == '' :
        if newform.company == None :
            # Error branch is None
            error = 'Error Company is blank'
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
        else:
            newform.email = ''

    if error == '':
        try:
            newform.birthday = funLocaltoUTC(newform.birthday, newform.company.timezone)
        except:
            error = 'An error occurcd : Birthday is not correct'

    if error == '':
        try:
            newform.verifycode_date = funLocaltoUTC(newform.verifycode_date, newform.company.timezone)
        except:
            error = 'An error occurcd : Verifycode_date is not correct'

    return error, newform

def checkcustomerform(form):
    error = ''
    errorTC = ''
    newform = None

    if form.is_valid() == False:
        # error_string = ' '.join([' '.join(x for x in l) for l in list(form.errors.values())])
        error_string = ''
        for l in list(form.errors):
            errx = ''
            for x in form.errors[l]:
                errx = errx + ',' +  x
                # print(l , x)
            error_string = error_string + ' [' + l + '] ' + errx + '\n'
        error = 'An error occurcd during registration: ' + error_string
        

    if error == '' :
        newform = form.save(commit=False)

    if error == '' :
        if newform.company == None :
            # Error branch is None
            error = 'Error Company is blank'

    if error == '' :
        if newform.phone == '':
            pass
        else:
            if newform.phone != None :
                if len(newform.phone) != 8:
                    error = 'Phone number must be 8 digits'

    if error == '':
        if not(newform.email == '' or newform.email == None) :
        # check email format
            regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b'
            if(re.fullmatch(regex, newform.email)):
                pass       
            else:
                error = 'Email format is incorrect'
                error_TC = '電郵地址格式不正確'
        else:
            newform.email = ''

    return error, newform