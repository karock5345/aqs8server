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
from base.views import auth_data, funDomain, getcontext, getcontext_en, getcontext_mini
from django.http import JsonResponse
from django.contrib import messages
from base.decorators import *
from crm.models import CRMAdmin, Member, Company, Customer, CustomerGroup, CustomerSource, CustomerInformation, Quotation, Invoice, Receipt, BusinessType, BusinessSource, Supplier
from crm.forms import MemberUpdateForm, MemberNewForm, CustomerUpdateForm, CustomerGroupForm, CustomerSourceForm, CustomerInfoForm, CustomerNewForm, QuotationUpdateForm, InvoiceUpdateForm, ReceiptUpdateForm, BusinessTypeForm, BusinessSourceForm
from crm.forms import SupplierUpdateForm, SupplierNewForm
from crm.api import new_member
from django.db import transaction
import re
from booking.views import checkMphone
from base.api.views import funUTCtoLocal, funLocaltoUTC, funUTCtoLocaltime, funLocaltoUTCtime
import xml.etree.ElementTree as ET
from xhtml2pdf import pisa
from io import BytesIO
from django.template.loader import get_template

sort_direction = {}
sort_direction_cust = {}

# Create your views here.
def WelcomeView(request):
    content = {'user':request.user}
    return render(request, 'crm/welcome.html', content)
@unauth_user
def SupplierListView(request):
    global sort_direction_cust

    q = request.GET.get('q') if request.GET.get('q') != None else ''
    q_sort = request.GET.get('sort') if request.GET.get('sort') != None else ''
    
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
    context = getcontext(request, request.user)
    auth_suppliers = context['suppliers']

    result = auth_suppliers
    # print(result_userlist.count())

    userp = UserProfile.objects.filter(Q(user = request.user)).first()
    if userp != None:
        if userp.company == None:
            messages.error(request, 'Your are not assign Company' )            
            return redirect('home')

    if q != '':
        result = result.filter(Q(supplier_company__icontains=q) 
                                             | Q(contact__icontains=q) 
                                             | Q(website__icontains=q) 
                                             | Q(phone__icontains=q) 
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

    if q_sort == 'supplier_company':
        result = result.order_by(direct + 'supplier_company')
    elif q_sort == 'contact':
        result = result.order_by(direct + 'contact')
    elif q_sort == 'email':
        result = result.order_by(direct + 'email')        
    elif q_sort == 'phone':
        result = result.order_by(direct + 'phone')


    context = context | {'q':q}
    context = context | {'result':result}
    context = context | {'company':userp.company}

    return render(request, 'crm/supplierlist.html', context)

@unauth_user
def SupplierUpdateView(request, pk):
    utcnow = datetime.now(timezone.utc)
    supplier = Supplier.objects.get(id=pk)    
    company = supplier.company
    # get full path with domain name
    back_url = request.build_absolute_uri()
    
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

    if request.method == 'POST':
        action = request.POST.get('action')
        form = SupplierUpdateForm(request.POST, instance=supplier, prefix='supplierform', company=supplier.company)

        # go, link, context = subupdate(request, action, company, supplier, back_url)
        # if go == 'go':
        #     return render(request, link, context)

        if action == 'member':
            # return redirect('crmmember')
            pass
        elif action == 'update':
            error = ''
            # check the form
            error, newform = checksupplierform(form)
            
            if error == '' :         
                try :                
                    newform.save()

                    messages.success(request, 'Customer was successfully updated!')
                    
                    return redirect('crmsupplierlist')
                except:
                    error = 'An error occurcd during updating Customer'

            if error != '':
                messages.error(request, error )
                
    else:
        form = SupplierUpdateForm(instance=supplier, prefix='supplierform', company=supplier.company)
    context =  {'form':form, 'supplier':supplier, }
    context_en = getcontext_en(request)
    context = context_en | context
    return render(request, 'crm/supplier_update.html', context)

def checksupplierform(form):
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
            # Error Company is None
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


@unauth_user
def SupplierNewView(request, ccode):
    error = ''
    status = {}
    
    user=request.user
    #back_url = request.build_absolute_uri()
    # get previous url
    back_url = request.META.get('HTTP_REFERER')
    
    if error == '':
        try:
            company = Company.objects.get(ccode=ccode)
        except:
            error = 'Company not found'
    if error == '':
        try:
            form = SupplierNewForm(company=company)
        except:
            error = 'form error'

    if error == '':
        if request.method == 'POST':
            action = request.POST.get('action')
            
            utcnow = datetime.now(timezone.utc)
            form = SupplierNewForm(request.POST, company=company)

            if action == 'new':
                if form.is_valid() == True:                    
                    # create new customer record
                    supplier = Supplier.objects.create(
                        company=company,
                        supplier_company=form['supplier_company'].value(),
                        contact=form['contact'].value(),
                        address=form['address'].value(),
                        email=form['email'].value(),
                        phone=form['phone'].value(),
                        website=form['website'].value(),
                    )
                else:
                    error = 'Invalid form data: ' + str(form.errors)                    
            if error == '' :
                messages.success(request, 'Created new Supplier.')
                return redirect('crmsupplierlist')
    if error != '':
        messages.error(request, error)
        return redirect('crmsupplierlist')

    context = {'form':form}
    context_en = getcontext_en(request)
    context = context_en | context    
    context = {'title':'New Supplier', 'back_url':back_url, } | context 
    return render(request, 'base/new.html', context)

@unauth_user
def SupplierDelView(request, pk):
    utcnow = datetime.now(timezone.utc)
    supplier = Supplier.objects.get(id=pk) 
  
    if request.method =='POST':
        supplier.delete()       
        messages.success(request, 'Supplier was successfully deleted!') 
        return redirect('crmsupplierlist')
    context = {'obj':supplier, 'text':'Warning: This action will delete the Supplier.'}
    context_mini = getcontext_mini(request)
    context = context_mini | context
    return render(request, 'base/delete.html', context)


@unauth_user
def CustomerListView(request):
    global sort_direction_cust

    q = request.GET.get('q') if request.GET.get('q') != None else ''
    q_sort = request.GET.get('sort') if request.GET.get('sort') != None else ''
    
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
    context = getcontext(request, request.user)
    auth_customerlist = context['customers']

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
    back_url = request.build_absolute_uri()
    
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

    if request.method == 'POST':
        action = request.POST.get('action')
        form = CustomerUpdateForm(request.POST, instance=customer, prefix='customerform', company=customer.company)

        go, link, context = SubUpdate(request, action, company, customer, back_url)
        if go == 'go':
            return render(request, link, context)

        if action == 'member':
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
    context_en = getcontext_en(request)
    context = context_en | context
    return render(request, 'crm/customer_update.html', context)


@unauth_user
def CustomerDelView(request, pk):
    utcnow = datetime.now(timezone.utc)
    customer = Customer.objects.get(id=pk) 
  
    if request.method =='POST':
        customer.delete()       
        messages.success(request, 'Customer was successfully deleted!') 
        return redirect('crmcustomerlist')
    context = {'obj':customer, 'text':'Warning: This action will delete the Customer.'}
    context_mini = getcontext_mini(request)
    context = context_mini | context
    return render(request, 'base/delete.html', context)

@unauth_user
def CustomerNewView(request, ccode):
    error = ''
    status = {}

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
    
    user=request.user
    #back_url = request.build_absolute_uri()
    # get previous url
    back_url = request.META.get('HTTP_REFERER')

    try:
        company = Company.objects.get(ccode=ccode)
        form = CustomerNewForm(company=company, user=user)
    except:
        error = 'Company not found'

    if error == '':
        if request.method == 'POST':
            action = request.POST.get('action')
            
            go, link, context = SubUpdate(request, action, company, None, back_url)
            if go == 'go':
                return render(request, link, context)
            
            utcnow = datetime.now(timezone.utc)
            form = CustomerNewForm(request.POST, company=company, user=user)

            if action == 'member':
                return redirect('crmmember')

            if action == 'new':
                if form.is_valid() == True:
                    group = None
                    try:
                        group = CustomerGroup.objects.get(pk=form['group'].value())
                    except:
                        pass
                    source = None
                    try:
                        source = CustomerSource.objects.get(pk=form['source'].value())
                    except:
                        pass
                    information = None
                    try:
                        information = CustomerInformation.objects.get(pk=form['information'].value())
                    except:
                        pass
                    member = None
                    try:
                        member = Member.objects.get(pk=form['member'].value())
                    except:
                        pass
                    # create new customer record
                    customer = Customer.objects.create(
                        company=company,
                        companyname=form['companyname'].value(),
                        contact=form['contact'].value(),
                        address=form['address'].value(),
                        email=form['email'].value(),
                        phone=form['phone'].value(),
                        fax=form['fax'].value(),
                        referby=form['referby'].value(),
                        sales=request.user,
                        group=group,
                        source=source,
                        information=information,
                        member=member,
                        remark=form['remark'].value(),
                        createdby=request.user
                    )
                else:
                    error = 'Invalid form data: ' + str(form.errors)                    
            if error == '' :
                messages.success(request, 'Created new Customer.')
                return redirect('crmcustomerlist')
    if error != '':
        messages.error(request, error)

    # get the url of 'bookingtimeslot'
    context = {'form':form}
    context_en = getcontext_en(request)
    context = context_en | context    
    context = {'title':'New Customer', 'back_url':back_url, } | context 
    return render(request, 'base/new.html', context)

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

def SubUpdate(request, action, company, customer, full_path):
        context = {}
        context_mini = getcontext_mini(request)
        context = context_mini | context 
    # <---- business type for Quotation ----
        if action == 'businesstype':
            table = BusinessType.objects.filter(Q(company=company))
            form = BusinessTypeForm()
            context = context | {'table':table, 'form': form, 'company':company, 'customer':customer, 'back_url':full_path, 'title':'Manage Business Type', 'action':'businesstype'}
            # return render(request, 'crm/sub_update.html', context)
            return 'go', 'crm/sub_update.html', context
        elif action == 'update_businesstype':
            form = BusinessTypeForm(request.POST)
            if form.is_valid():
                # get the id of the customer group from the form
                pk = form['id'].value()
                obj = BusinessType.objects.get(pk=pk)

                obj.name = form['name'].value()
                obj.description = form['description'].value()
                obj.save()
                # form.save()
                messages.success(request, 'Update success' )
            table = BusinessType.objects.filter(Q(company=company))
            context = context | { 'table':table, 'form': form, 'company':company, 'back_url':full_path, 'title':'Manage Business Type', 'action':'businesstype'}
            # return render(request, 'crm/sub_update.html', context)
            return 'go', 'crm/sub_update.html', context
        elif action == 'new_businesstype':
            BusinessType.objects.create(company=company, name='', description='')
            form = BusinessTypeForm(request.POST)

            table = BusinessType.objects.filter(Q(company=company))
            context = context | { 'table':table, 'form': form, 'company':company, 'back_url':full_path, 'title':'Manage Business Type', 'action':'businesstype'}       
            # return render(request, 'crm/sub_update.html', context, )
            return 'go', 'crm/sub_update.html', context
        elif action == 'del_businesstype':
            form = BusinessTypeForm(request.POST)
            if form.is_valid():
                pk = form['id'].value()
                BusinessType.objects.get(pk=pk).delete()

            table = BusinessType.objects.filter(Q(company=company))
            context = context | { 'table':table, 'form': form, 'company':company, 'back_url':full_path, 'title':'Manage Business Type', 'action':'businesstype'}
            # return render(request, 'crm/sub_update.html', context, )  
            return 'go', 'crm/sub_update.html', context      
    # ---- business type for Quotation ---->

    # <---- business source for Quotation ----
        if action == 'businesssource':
            table = BusinessSource.objects.filter(Q(company=company))
            form = BusinessSourceForm()
            context = context | {'table':table, 'form': form, 'company':company, 'customer':customer, 'back_url':full_path, 'title':'Manage Business Source', 'action':'businesssource'}
            # return render(request, 'crm/sub_update.html', context)
            return 'go', 'crm/sub_update.html', context
        elif action == 'update_businesssource':
            form = BusinessSourceForm(request.POST)
            if form.is_valid():
                # get the id of the customer group from the form
                pk = form['id'].value()
                obj = BusinessSource.objects.get(pk=pk)

                obj.name = form['name'].value()
                obj.description = form['description'].value()
                obj.save()
                # form.save()
                messages.success(request, 'Update success' )
            table = BusinessSource.objects.filter(Q(company=company))
            context = context | { 'table':table, 'form': form, 'company':company, 'back_url':full_path, 'title':'Manage Business Source', 'action':'businesssource'}
            # return render(request, 'crm/sub_update.html', context)
            return 'go', 'crm/sub_update.html', context
        elif action == 'new_businesssource':
            BusinessSource.objects.create(company=company, name='', description='')
            form = BusinessSourceForm(request.POST)

            table = BusinessSource.objects.filter(Q(company=company))
            context = context | { 'table':table, 'form': form, 'company':company, 'back_url':full_path, 'title':'Manage Business Source', 'action':'businesssource'}       
            # return render(request, 'crm/sub_update.html', context, )
            return 'go', 'crm/sub_update.html', context
        elif action == 'del_businesssource':
            form = BusinessSourceForm(request.POST)
            if form.is_valid():
                pk = form['id'].value()
                BusinessSource.objects.get(pk=pk).delete()

            table = BusinessSource.objects.filter(Q(company=company))
            context = context | { 'table':table, 'form': form, 'company':company, 'back_url':full_path, 'title':'Manage Business Source', 'action':'businesssource'}
            # return render(request, 'crm/sub_update.html', context, )  
            return 'go', 'crm/sub_update.html', context      
    # ---- business source for Quotation ---->

    # <---- Customer Group ----
        if action == 'group':
            table = CustomerGroup.objects.filter(Q(company=company))
            cgform = CustomerGroupForm()
            context = context | {'table':table, 'form': cgform, 'company':company, 'customer':customer, 'back_url':full_path, 'title':'Manage Customer Group', 'action':'group'}
            # return render(request, 'crm/sub_update.html', context)
            return 'go', 'crm/sub_update.html', context
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
            context = context | { 'table':table, 'form': cgform, 'company':company, 'back_url':full_path, 'title':'Manage Customer Group', 'action':'group'}
            # return render(request, 'crm/sub_update.html', context)
            return 'go', 'crm/sub_update.html', context
        elif action == 'new_group':
            CustomerGroup.objects.create(company=company, name='', description='')
            cgform = CustomerGroupForm(request.POST)

            table = CustomerGroup.objects.filter(Q(company=company))
            context = context | { 'table':table, 'form': cgform, 'company':company, 'back_url':full_path, 'title':'Manage Customer Group', 'action':'group'}       
            # return render(request, 'crm/sub_update.html', context, )
            return 'go', 'crm/sub_update.html', context
        elif action == 'del_group':
            cgform = CustomerGroupForm(request.POST)
            if cgform.is_valid():
                pk = cgform['id'].value()
                CustomerGroup.objects.get(pk=pk).delete()

            table = CustomerGroup.objects.filter(Q(company=company))
            context = context | { 'table':table, 'form': cgform, 'company':company, 'back_url':full_path, 'title':'Manage Customer Group', 'action':'group'}
            # return render(request, 'crm/sub_update.html', context, )  
            return 'go', 'crm/sub_update.html', context      
    # ---- Customer Group ---->

    # <---- Customer Source ----
        elif action == 'source':
            table = CustomerSource.objects.filter(Q(company=company))
            csform = CustomerSourceForm()
            context = context | {'table':table, 'form': csform, 'company':company, 'customer':customer, 'back_url':full_path, 'title':'Manage Customer Source', 'action':'source'}
            # return render(request, 'crm/sub_update.html', context)
            return 'go', 'crm/sub_update.html', context
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
            context = context | { 'table':table, 'form': csform, 'company':company, 'back_url':full_path, 'title':'Manage Customer Source', 'action':'source'}
            # return render(request, 'crm/sub_update.html', context)
            return 'go', 'crm/sub_update.html', context
        elif action == 'new_source':
            CustomerSource.objects.create(company=company, name='', description='')
            csform = CustomerSourceForm(request.POST)

            table = CustomerSource.objects.filter(Q(company=company))
            context = context | { 'table':table, 'form': csform, 'company':company, 'back_url':full_path, 'title':'Manage Customer Source', 'action':'source'}       
            # return render(request, 'crm/sub_update.html', context, )
            return 'go', 'crm/sub_update.html', context
        elif action == 'del_source':
            csform = CustomerSourceForm(request.POST)
            if csform.is_valid():
                pk = csform['id'].value()
                CustomerSource.objects.get(pk=pk).delete()

            table = CustomerSource.objects.filter(Q(company=company))
            context = context | { 'table':table, 'form': csform, 'company':company, 'back_url':full_path, 'title':'Manage Customer Source', 'action':'source'}
            # return render(request, 'crm/sub_update.html', context, )        
            return 'go', 'crm/sub_update.html', context
    # ---- Customer Source ---->

    # <---- Customer Information ----
        elif action == 'information':
            table = CustomerInformation.objects.filter(Q(company=company))
            infoform = CustomerInfoForm()
            context = context | {'table':table, 'form': infoform, 'company':company, 'customer':customer, 'back_url':full_path, 'title':'Manage Customer Information', 'action':'information'}
            # return render(request, 'crm/sub_update.html', context)
            return 'go', 'crm/sub_update.html', context
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
            context = context | {'table':table, 'form': infoform, 'company':company, 'customer':customer, 'back_url':full_path, 'title':'Manage Customer Information', 'action':'information'}
            # return render(request, 'crm/sub_update.html', context)
            return 'go', 'crm/sub_update.html', context
        elif action == 'new_information':
            CustomerInformation.objects.create(company=company, name='', description='')
            infoform = CustomerInfoForm(request.POST)

            table = CustomerInformation.objects.filter(Q(company=company))
            context = context | {'table':table, 'form': infoform, 'company':company, 'customer':customer, 'back_url':full_path, 'title':'Manage Customer Information', 'action':'information'}
            # return render(request, 'crm/sub_update.html', context, )
            return 'go', 'crm/sub_update.html', context
        elif action == 'del_information':
            infoform = CustomerInfoForm(request.POST)
            if infoform.is_valid():
                pk = infoform['id'].value()
                CustomerInformation.objects.get(pk=pk).delete()

            table = CustomerInformation.objects.filter(Q(company=company))
            context = context | {'table':table, 'form': infoform, 'company':company, 'customer':customer, 'back_url':full_path, 'title':'Manage Customer Information', 'action':'information'}
            # return render(request, 'crm/sub_update.html', context, )
            return 'go', 'crm/sub_update.html', context
    # ---- Customer Information ---->



        return '', '', {}

@unauth_user
def QuotationView(request, pk=None):
    error = ''
    utcnow = datetime.now(timezone.utc)
    context = {}
    # company = customer.company
    # get full path with domain name
    full_path = request.build_absolute_uri()
    
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
    context = getcontext(request, request.user)
    auth_quotations = context['quotations']

    # get full path with domain name
    back_url = request.build_absolute_uri()
       
    if error == '':
        try:
            puser = UserProfile.objects.filter(user=request.user).first()
        except:
            error = 'User Profile not found'
    if error == '':
        company = puser.company
        if company == None:
            error = 'Company not found'

    quotation = None
    if pk != None:
        try:
            quotation = Quotation.objects.get(pk=pk)
        except:
            pass
    else:
        if auth_quotations.count() > 0:
            try:
                quotation = auth_quotations[puser.index_q]
            except:
                quotation = auth_quotations.first()     
                puser.index_q = 0
                puser.save()

    form = None
    if error == '':
        if quotation != None:
            form = QuotationUpdateForm(instance=quotation, prefix='quotationform', company=company)
             
    if error != '':
        messages.error(request, error )
        return redirect('home')
    

    
    if request.method == 'POST':
        action = request.POST.get('action')
        print ('action:', action)
        
        go, link, context = SubUpdate(request, action, company, quotation, back_url)
        print (go, link, context)
        if go == 'go':
            return render(request, link, context)

        if action == 'update':
            form = QuotationUpdateForm(request.POST, instance=quotation, prefix='quotationform', company=company)
            if form.is_valid() == True:
                form.save()
                messages.success(request, 'Quotation was successfully updated!')
                return redirect('crmquotation', pk=quotation.pk)
        if action == 'previous':
            puser.index_q = puser.index_q + 1
            if puser.index_q >= auth_quotations.count():
                puser.index_q = auth_quotations.count() - 1
            puser.save()
            quotation = auth_quotations[puser.index_q]
            return redirect('crmquotation', pk=quotation.pk)
        if action == 'next':
            puser.index_q = puser.index_q - 1
            if puser.index_q < 0:
                puser.index_q = 0
            puser.save()
            quotation = auth_quotations[puser.index_q]
            return redirect('crmquotation', pk=quotation.pk)
        if action == 'email':
            context = {'text1':'text1', 
                       'text2':'The quotation has been sent to the customer.',
                       'text3': 'Quotation No : ' + quotation.number,
                       'text4': 'Sent to : ' + quotation.customer_email,
                        }
            context_mini = getcontext_mini(request)
            context = context_mini | context 
            return render(request, 'crm/email_sent.html', context)
    
    context = context | {
                # 'aqs_version':aqs_version,
                # 'en_queue':auth_en_queue, 'en_crm':auth_en_crm, 'en_booking':auth_en_booking,
                'quotation':quotation, 
                'company':company,
                'form':form,
               }
    return render(request, 'crm/quotation.html', context)

@unauth_user
def QuotationNewView(request, ccode):
    error = ''
    status = {}
    nowutc = datetime.now(timezone.utc)

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
    auth_en_crm = context_temp['en_crm']
    
    user=request.user
    back_url = request.build_absolute_uri()

    if error == '':
        if auth_en_crm == False:
            error = 'CRM is not enabled'

    try:
        company = Company.objects.get(ccode=ccode)
        form = CustomerNewForm(company=company, user=user)
    except:
        error = 'Company not found'

    # generate new quotation number
    if error == '':
        error, number_str = gen_new_quotationno(company, nowutc)

    if error == '':
        # new quotation
        quotation = Quotation.objects.create(
            company=company,
            number=number_str,
            quotation_date=nowutc,
            quotation_status = 'draft',
            sales=user,
        )
        return redirect('crmquotation', pk=quotation.pk)

@unauth_user
def QuotationDelView(request, pk):
    utcnow = datetime.now(timezone.utc)
    obj = Quotation.objects.get(id=pk) 
  
    if request.method =='POST':
        for item in obj.items.all():
            item.delete()
        obj.delete()       
        messages.success(request, 'Quotation was successfully deleted!') 
        return redirect('crmquotation')
    context = {'obj':obj, 'text':'Warning: This action will delete the Quotation.'}
    context_mini = getcontext_mini(request)
    context = context_mini | context
    return render(request, 'base/delete.html', context)


@unauth_user
def QuotationPDFView(request, pk):
    quotation = Quotation.objects.get(pk=pk)
    # convert quotation.items.all() to list of dictionary then pass the q_dict : items_dist
    items_dist = []
    for item in quotation.items.all():
        items_dist.append({
            'name': item.name,
            'price': item.price,
            'qty': item.quantity,
            'sub_total': item.sub_total,
        })

    q_dict = { 
            'mycompany': quotation.company.name,
              'number': quotation.number, 
              'quotation_date': quotation.quotation_date,
              'customer_companyname': quotation.customer_companyname, 
              'customer_contact': quotation.customer_contact, 
              'sales': quotation.sales.first_name + ' ' + quotation.sales.last_name,
              'total': quotation.total,
              'items': items_dist,
              }
    
    pdf = render_to_pdf('crm/quotation_pdf.html', q_dict)
    return HttpResponse(pdf, content_type='application/pdf')
    
@transaction.atomic
def gen_new_quotationno(company:Company, datetime_now_utc:datetime):
    error = ''
    number_str = None

    if error == '':
        # genrate Quotation number
        try:
            crmadmin = CRMAdmin.objects.select_for_update().get(company=company)
        except:
            error = 'CRM Admin not found'   
    
    if error == '' :
        number = crmadmin.quotationnumber_next
        number_digit = crmadmin.quotationnumber_digit
        # check number reset
        # quotationnumber_reset is role for reset quotation number, e.g. role:<Y>2024</Y> now is 2023-12-31, when now is 2024-01-01, reset quotation number to 1 
        reset ='<DATA>' + crmadmin.quotationnumber_reset + '</DATA>'
        tree = ET.fromstring(reset)
        for elem in tree.iter():
            # print(elem.tag, elem.text)
            if elem.text == None and elem.tag != 'DATA':
                error = 'quotation number reset format error'
                break
            if elem.tag == 'Y':
                value = int(elem.text)
                now_y = datetime_now_utc.year
                if value != now_y:
                    number = 1

                    crmadmin.quotationnumber_reset = crmadmin.quotationnumber_reset.replace('<Y>' + str(value) + '</Y>', '<Y>' + str(now_y) + '</Y>')
                    crmadmin.save()
                    # save xml to db
            elif elem.tag == 'm':
                value = int(elem.text)
                now_m = datetime_now_utc.month
                if value != now_m:
                    number = 1
                    
                    crmadmin.quotationnumber_reset = crmadmin.quotationnumber_reset.replace('<m>' + str(value) + '</m>', '<m>' + str(now_m) + '</m>')
                    crmadmin.save()
            elif elem.tag == 'd':
                value = int(elem.text)
                now_d = datetime_now_utc.day
                if value != now_d:
                    number = 1

                    crmadmin.quotationnumber_reset = crmadmin.quotationnumber_reset.replace('<d>' + str(value) + '</d>', '<d>' + str(now_d) + '</d>')
                    crmadmin.save()
        
    if error == '':
    # process prefix
    # quotationnumber_prefix is role for quotation number, <TEXT>MEM</TEXT><Y></Y><m></m><d></d><no></no> is Year, Month, Day, Hour, Minute, Second, Number('%Y-%m-%d %H:%M:%S')
    # e.g. <TEXT>VIP</TEXT><Y></Y><no></no> is VIP2023001       
        number_str = ''
        prefix = crmadmin.quotationnumber_prefix
        if prefix == '' or prefix == None :
            number_str = str(number).zfill(number_digit)
        else:
            nonumber = True
            prefix ='<DATA>' + prefix + '</DATA>'
            tree = ET.fromstring(prefix)
            for elem in tree.iter():
                # print(elem.tag, elem.text)
                if elem.tag == 'Y':
                    number_str = number_str + str(datetime_now_utc.year)
                elif elem.tag == 'm':
                    number_str = number_str + str(datetime_now_utc.month)
                elif elem.tag == 'd':
                    number_str = number_str + str(datetime_now_utc.day)
                elif elem.tag == 'no':
                    number_str = number_str + str(number).zfill(number_digit)
                    nonumber = False
                elif elem.tag == 'TEXT' :
                    if elem.text != None :
                        number_str = number_str + elem.text
            if nonumber == True:
                number_str = number_str + str(number).zfill(number_digit)
        crmadmin.quotationnumber_next = crmadmin.quotationnumber_next + 1
        crmadmin.save()
        # print(number_str)

    return error, number_str

@unauth_user
def InvoiceView(request, pk=None):
    error = ''
    utcnow = datetime.now(timezone.utc)
    context = {}
    # company = customer.company
    # get full path with domain name
    full_path = request.build_absolute_uri()
    
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
    context = getcontext(request, request.user)
    auth_invoices = context['invoices']
       
    if error == '':
        try:
            puser = UserProfile.objects.filter(user=request.user).first()
        except:
            error = 'User Profile not found'
    if error == '':
        company = puser.company
        if company == None:
            error = 'Company not found'

    invoice = None
    if pk != None:
        try:
            invoice = Invoice.objects.get(pk=pk)
        except:
            pass
    else:
        if auth_invoices.count() > 0:
            try:
                invoice = auth_invoices[puser.index_q]
            except:
                invoice = auth_invoices.first()     
                puser.index_q = 0
                puser.save()

    form = None
    if error == '':
        if invoice != None:
            form = InvoiceUpdateForm(instance=invoice, prefix='invoiceform', company=company)
             
    if error != '':
        messages.error(request, error )
        return redirect('home')

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'update':
            form = InvoiceUpdateForm(request.POST, instance=invoice, prefix='invoiceform', company=company)
            if form.is_valid() == True:
                form.save()
                messages.success(request, 'Invoice was successfully updated!')
                return redirect('crminvoice', pk=invoice.pk)
        if action == 'previous':
            puser.index_i = puser.index_i + 1
            if puser.index_i >= auth_invoices.count():
                puser.index_i = auth_invoices.count() - 1
            puser.save()
            invoice = auth_invoices[puser.index_i]
            return redirect('crminvoice', pk=invoice.pk)
        if action == 'next':
            puser.index_i = puser.index_i - 1
            if puser.index_i < 0:
                puser.index_i = 0
            puser.save()
            invoice = auth_invoices[puser.index_i]
            return redirect('crminvoice', pk=invoice.pk)
        if action == 'email':
            context = {'text1':'text1', 
                       'text2':'The invoice has been sent to the customer.',
                        'text3': 'Invoice No : ' + invoice.number,
                        'text4': 'Sent to : ' + invoice.customer_email,
                        }
            context_mini = getcontext_mini(request)
            context = context_mini | context 
            return render(request, 'crm/email_sent.html', context)

    context = context | {
                'invoice':invoice, 
                'company':company,
                'form':form,
               }
    return render(request, 'crm/invoice.html', context)

@unauth_user
def InvoiceNewView(request, ccode):
    error = ''
    status = {}
    nowutc = datetime.now(timezone.utc)

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
    auth_en_crm = context_temp['en_crm']
    
    user=request.user
    back_url = request.build_absolute_uri()

    if error == '':
        if auth_en_crm == False:
            error = 'CRM is not enabled'

    try:
        company = Company.objects.get(ccode=ccode)
        form = CustomerNewForm(company=company, user=user)
    except:
        error = 'Company not found'

    # generate new invoice number
    if error == '':
        error, number_str = gen_new_invoiceno(company, nowutc)

    if error == '':
        # new invoice
        invoice = Invoice.objects.create(
            company=company,
            number=number_str,
            invoice_date=nowutc,
            invoice_status = 'draft',
            sales=user,
        )
        return redirect('crminvoice', pk=invoice.pk)

@unauth_user
def InvoiceDelView(request, pk):
    utcnow = datetime.now(timezone.utc)
    obj = Invoice.objects.get(id=pk) 
  
    if request.method =='POST':
        for item in obj.items.all():
            item.delete()
        obj.delete()       
        messages.success(request, 'Invoice was successfully deleted!') 
        return redirect('crminvoice')
    context = {'obj':obj, 'text':'Warning: This action will delete the Invoice.'}
    context_mini = getcontext_mini(request)
    context = context_mini | context
    return render(request, 'base/delete.html', context)


@unauth_user
def InvoicePDFView(request, pk):
    invoice = Invoice.objects.get(pk=pk)
    # convert invoice.items.all() to list of dictionary then pass the q_dict : items_dist
    items_dist = []
    for item in invoice.items.all():
        items_dist.append({
            'name': item.name,
            'price': item.price,
            'qty': item.quantity,
            'sub_total': item.sub_total,
        })

    q_dict = { 
            'mycompany': invoice.company.name,
              'number': invoice.number, 
              'invoice_date': invoice.invoice_date,
              'customer_companyname': invoice.customer_companyname, 
              'customer_contact': invoice.customer_contact, 
              'sales': invoice.sales.first_name + ' ' + invoice.sales.last_name,
              'total': invoice.total,
              'items': items_dist,
              }
    
    pdf = render_to_pdf('crm/invoice_pdf.html', q_dict)
    return HttpResponse(pdf, content_type='application/pdf')
    
@transaction.atomic
def gen_new_invoiceno(company:Company, datetime_now_utc:datetime):
    error = ''
    number_str = None

    if error == '':
        # genrate invoice number
        try:
            crmadmin = CRMAdmin.objects.select_for_update().get(company=company)
        except:
            error = 'CRM Admin not found'   
    
    if error == '' :
        number = crmadmin.invoicenumber_next
        number_digit = crmadmin.invoicenumber_digit
        # check number reset
        # invoicenumber_reset is role for reset invoice number, e.g. role:<Y>2024</Y> now is 2023-12-31, when now is 2024-01-01, reset quotation number to 1 
        reset ='<DATA>' + crmadmin.invoicenumber_reset + '</DATA>'
        tree = ET.fromstring(reset)
        for elem in tree.iter():
            # print(elem.tag, elem.text)
            if elem.text == None and elem.tag != 'DATA':
                error = 'invoice number reset format error'
                break
            if elem.tag == 'Y':
                value = int(elem.text)
                now_y = datetime_now_utc.year
                if value != now_y:
                    number = 1

                    crmadmin.invoicenumber_reset = crmadmin.invoicenumber_reset.replace('<Y>' + str(value) + '</Y>', '<Y>' + str(now_y) + '</Y>')
                    crmadmin.save()
                    # save xml to db
            elif elem.tag == 'm':
                value = int(elem.text)
                now_m = datetime_now_utc.month
                if value != now_m:
                    number = 1
                    
                    crmadmin.invoicenumber_reset = crmadmin.invoicenumber_reset.replace('<m>' + str(value) + '</m>', '<m>' + str(now_m) + '</m>')
                    crmadmin.save()
            elif elem.tag == 'd':
                value = int(elem.text)
                now_d = datetime_now_utc.day
                if value != now_d:
                    number = 1

                    crmadmin.invoicenumber_reset = crmadmin.invoicenumber_reset.replace('<d>' + str(value) + '</d>', '<d>' + str(now_d) + '</d>')
                    crmadmin.save()
        
    if error == '':
    # process prefix
    # invoicenumber_prefix is role for invoice number, <TEXT>MEM</TEXT><Y></Y><m></m><d></d><no></no> is Year, Month, Day, Hour, Minute, Second, Number('%Y-%m-%d %H:%M:%S')
    # e.g. <TEXT>VIP</TEXT><Y></Y><no></no> is VIP2023001       
        number_str = ''
        prefix = crmadmin.invoicenumber_prefix
        if prefix == '' or prefix == None :
            number_str = str(number).zfill(number_digit)
        else:
            nonumber = True
            prefix ='<DATA>' + prefix + '</DATA>'
            tree = ET.fromstring(prefix)
            for elem in tree.iter():
                # print(elem.tag, elem.text)
                if elem.tag == 'Y':
                    number_str = number_str + str(datetime_now_utc.year)
                elif elem.tag == 'm':
                    number_str = number_str + str(datetime_now_utc.month)
                elif elem.tag == 'd':
                    number_str = number_str + str(datetime_now_utc.day)
                elif elem.tag == 'no':
                    number_str = number_str + str(number).zfill(number_digit)
                    nonumber = False
                elif elem.tag == 'TEXT' :
                    if elem.text != None :
                        number_str = number_str + elem.text
            if nonumber == True:
                number_str = number_str + str(number).zfill(number_digit)
        crmadmin.invoicenumber_next = crmadmin.invoicenumber_next + 1
        crmadmin.save()
        # print(number_str)

    return error, number_str



@unauth_user
def ReceiptView(request, pk=None):
    error = ''
    utcnow = datetime.now(timezone.utc)
    context = {}
    # company = customer.company
    # get full path with domain name
    full_path = request.build_absolute_uri()
    
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
    context = getcontext(request, request.user)
    auth_receipts = context['receipts']
           
    if error == '':
        try:
            puser = UserProfile.objects.filter(user=request.user).first()
        except:
            error = 'User Profile not found'
    if error == '':
        company = puser.company
        if company == None:
            error = 'Company not found'

    receipt = None
    if pk != None:
        try:
            receipt = Receipt.objects.get(pk=pk)
        except:
            pass
    else:
        if auth_receipts.count() > 0:
            try:
                receipt = auth_receipts[puser.index_q]
            except:
                receipt = auth_receipts.first()     
                puser.index_q = 0
                puser.save()

    form = None
    if error == '':
        if receipt != None:
            form = ReceiptUpdateForm(instance=receipt, prefix='receiptform', company=company)
             
    if error != '':
        messages.error(request, error )
        return redirect('home')

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'update':
            form = ReceiptUpdateForm(request.POST, instance=receipt, prefix='receiptform', company=company)
            if form.is_valid() == True:
                form.save()
                messages.success(request, 'Receipt was successfully updated!')
                return redirect('crmreceipt', pk=receipt.pk)
        if action == 'previous':
            puser.index_r = puser.index_r + 1
            if puser.index_r >= auth_receipts.count():
                puser.index_r = auth_receipts.count() - 1
            puser.save()
            receipt = auth_receipts[puser.index_r]
            return redirect('crmreceipt', pk=receipt.pk)
        if action == 'next':
            puser.index_r = puser.index_r - 1
            if puser.index_r < 0:
                puser.index_r = 0
            puser.save()
            receipt = auth_receipts[puser.index_i]
            return redirect('crmreceipt', pk=receipt.pk)
        if action == 'email':
            context = {'text1':'text1', 
                       'text2':'The receipt has been sent to the customer.',
                        'text3': 'Receipt No : ' + receipt.number,
                        'text4': 'Sent to : ' + receipt.customer_email,
                        }
            context_mini = getcontext_mini(request)
            context = context_mini | context 
            return render(request, 'crm/email_sent.html', context)
    context = context | {
                # 'aqs_version':aqs_version,
                # 'en_queue':auth_en_queue, 'en_crm':auth_en_crm, 'en_booking':auth_en_booking,
                'receipt':receipt, 
                'company':company,
                'form':form,
               }  
    return render(request, 'crm/receipt.html', context)

@unauth_user
def ReceiptNewView(request, ccode):
    error = ''
    status = {}
    nowutc = datetime.now(timezone.utc)

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
    auth_en_crm = context_temp['en_crm']
    
    user=request.user
    back_url = request.build_absolute_uri()

    if error == '':
        if auth_en_crm == False:
            error = 'CRM is not enabled'

    try:
        company = Company.objects.get(ccode=ccode)
        form = CustomerNewForm(company=company, user=user)
    except:
        error = 'Company not found'

    # generate new receipt number
    if error == '':
        error, number_str = gen_new_receiptno(company, nowutc)

    if error == '':
        # new receipt
        receipt = Receipt.objects.create(
            company=company,
            number=number_str,
            receipt_date=nowutc,
            sales=user,
        )
        return redirect('crmreceipt', pk=receipt.pk)

@unauth_user
def ReceiptDelView(request, pk):
    utcnow = datetime.now(timezone.utc)
    obj = Receipt.objects.get(id=pk) 
  
    if request.method =='POST':
        for item in obj.items.all():
            item.delete()
        obj.delete()       
        messages.success(request, 'Receipt was successfully deleted!') 
        return redirect('crmreceipt')
    context = {'obj':obj, 'text':'Warning: This action will delete the Receipt.'}

    context_mini = getcontext_mini(request)
    context = context_mini | context
    return render(request, 'base/delete.html', context)


@unauth_user
def ReceiptPDFView(request, pk):
    receipt = Receipt.objects.get(pk=pk)
    # convert receipt.items.all() to list of dictionary then pass the q_dict : items_dist
    items_dist = []
    for item in receipt.items.all():
        items_dist.append({
            'name': item.name,
            'price': item.price,
            'qty': item.quantity,
            'sub_total': item.sub_total,
        })

    q_dict = { 
            'mycompany': receipt.company.name,
              'number': receipt.number, 
              'receipt_date': receipt.receipt_date,
              'customer_companyname': receipt.customer_companyname, 
              'customer_contact': receipt.customer_contact, 
              'sales': receipt.sales.first_name + ' ' + receipt.sales.last_name,
              'total': receipt.total,
              'items': items_dist,
              }
    
    pdf = render_to_pdf('crm/receipt_pdf.html', q_dict)
    return HttpResponse(pdf, content_type='application/pdf')
    
@transaction.atomic
def gen_new_receiptno(company:Company, datetime_now_utc:datetime):
    error = ''
    number_str = None

    if error == '':
        # genrate receipt number
        try:
            crmadmin = CRMAdmin.objects.select_for_update().get(company=company)
        except:
            error = 'CRM Admin not found'   
    
    if error == '' :
        number = crmadmin.receiptnumber_next
        number_digit = crmadmin.receiptnumber_digit
        # check number reset
        # receiptnumber_reset is role for reset receipt number, e.g. role:<Y>2024</Y> now is 2023-12-31, when now is 2024-01-01, reset quotation number to 1 
        reset ='<DATA>' + crmadmin.receiptnumber_reset + '</DATA>'
        tree = ET.fromstring(reset)
        for elem in tree.iter():
            # print(elem.tag, elem.text)
            if elem.text == None and elem.tag != 'DATA':
                error = 'Receipt number reset format error'
                break
            if elem.tag == 'Y':
                value = int(elem.text)
                now_y = datetime_now_utc.year
                if value != now_y:
                    number = 1

                    crmadmin.receiptnumber_reset = crmadmin.receiptnumber_reset.replace('<Y>' + str(value) + '</Y>', '<Y>' + str(now_y) + '</Y>')
                    crmadmin.save()
                    # save xml to db
            elif elem.tag == 'm':
                value = int(elem.text)
                now_m = datetime_now_utc.month
                if value != now_m:
                    number = 1
                    
                    crmadmin.receiptnumber_reset = crmadmin.receiptnumber_reset.replace('<m>' + str(value) + '</m>', '<m>' + str(now_m) + '</m>')
                    crmadmin.save()
            elif elem.tag == 'd':
                value = int(elem.text)
                now_d = datetime_now_utc.day
                if value != now_d:
                    number = 1

                    crmadmin.receiptnumber_reset = crmadmin.receiptnumber_reset.replace('<d>' + str(value) + '</d>', '<d>' + str(now_d) + '</d>')
                    crmadmin.save()
        
    if error == '':
    # process prefix
    # receiptnumber_prefix is role for receipt number, <TEXT>MEM</TEXT><Y></Y><m></m><d></d><no></no> is Year, Month, Day, Hour, Minute, Second, Number('%Y-%m-%d %H:%M:%S')
    # e.g. <TEXT>VIP</TEXT><Y></Y><no></no> is VIP2023001       
        number_str = ''
        prefix = crmadmin.receiptnumber_prefix
        if prefix == '' or prefix == None :
            number_str = str(number).zfill(number_digit)
        else:
            nonumber = True
            prefix ='<DATA>' + prefix + '</DATA>'
            tree = ET.fromstring(prefix)
            for elem in tree.iter():
                # print(elem.tag, elem.text)
                if elem.tag == 'Y':
                    number_str = number_str + str(datetime_now_utc.year)
                elif elem.tag == 'm':
                    number_str = number_str + str(datetime_now_utc.month)
                elif elem.tag == 'd':
                    number_str = number_str + str(datetime_now_utc.day)
                elif elem.tag == 'no':
                    number_str = number_str + str(number).zfill(number_digit)
                    nonumber = False
                elif elem.tag == 'TEXT' :
                    if elem.text != None :
                        number_str = number_str + elem.text
            if nonumber == True:
                number_str = number_str + str(number).zfill(number_digit)
        crmadmin.receiptnumber_next = crmadmin.receiptnumber_next + 1
        crmadmin.save()
        # print(number_str)

    return error, number_str


@unauth_user
def MemberListView(request):
    global sort_direction    

    q = request.GET.get('q') if request.GET.get('q') != None else ''
    q_active = request.GET.get('qactive') if request.GET.get('qactive') != None else 'all'
    q_verified = request.GET.get('qverified') if request.GET.get('qverified') != None else 'all'
    q_company = request.GET.get('qcompany') if request.GET.get('qcompany') != None else 'all'
    q_sort = request.GET.get('sort') if request.GET.get('sort') != None else ''
    
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
    context = getcontext(request, request.user)
    auth_memberlist = context['members']

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
    context_en = getcontext_en(request)
    context = context_en | context
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
    context_mini = getcontext_mini(request)
    context = context_mini | context
    return render(request, 'base/delete.html', context)


@unauth_user
def MemberNewView(request, ccode):
    error = ''
    status = {}

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
    context_en = getcontext_en(request)
    context = context_en | context
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




def render_to_pdf(template_src, quotation:Quotation):
    template = get_template(template_src)
    html = template.render(quotation)
    result = BytesIO()
    pdf = pisa.pisaDocument(BytesIO(html.encode("UTF-8")), result)
    if not pdf.err:
        return HttpResponse(result.getvalue(), content_type='application/pdf')
    return None

