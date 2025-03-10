from django.forms import ModelForm
from django import forms
from django.contrib.auth.models import User, Group
from django.db.models import Q
from django.forms.utils import ErrorList
from base.models import TicketFormat, TicketRoute, UserProfile, Branch, CounterType
from .models import Member, Customer, CustomerGroup, CustomerSource, CustomerInformation, Quotation, Invoice, Receipt, BusinessType, BusinessSource, Supplier
from .models import Product, Product_Type, Category
from captcha.fields import ReCaptchaField
from captcha.widgets import ReCaptchaV2Checkbox
from base.api.views import funUTCtoLocal, funLocaltoUTC, funUTCtoLocaltime, funLocaltoUTCtime
import pytz
# from django.utils.timezone import localtime, get_current_timezone
from datetime import datetime, timedelta

class DateInput(forms.DateInput):
    input_type = 'date'
class DateTimeInput(forms.DateTimeInput):
    input_type = 'datetime'

class CategoryForm(forms.ModelForm):
    id = forms.fields.IntegerField()
    def __init__(self, *args,**kwargs):
        super().__init__(*args,**kwargs)
        self.initial['id'] = self.instance.pk
    class Meta:
        model = Category
        fields = ['id', 'name', 'description']
class ProductTypeForm(forms.ModelForm):
    id = forms.fields.IntegerField()
    def __init__(self, *args,**kwargs):
        super().__init__(*args,**kwargs)
        self.initial['id'] = self.instance.pk
    class Meta:
        model = Product_Type
        fields = ['id', 'name', 'description']        
class ProductUpdateForm(ModelForm):
    def __init__(self, *args,**kwargs):
        self.company = kwargs.pop('company')
        super().__init__(*args,**kwargs)        
        self.fields['product_type'].queryset = Product_Type.objects.filter(company=self.company)
        self.fields['category'].queryset = Category.objects.filter(company=self.company)
        self.fields['supplier'].queryset = Supplier.objects.filter(company=self.company)
    
    class Meta:        
        model = Product
        fields = ['name', 'description','product_type', 'category', 'supplier', 'status', 'price', 'cost', 'duration', 'barcode' , 'weight', 'dimensions', 'manufacturing_date', 'expiration_date', 'is_available']


class MemberUpdateForm(ModelForm):
    def __init__(self, *args,**kwargs):
        # self.company = kwargs.pop('company')
        # self.auth_userlist = kwargs.pop('auth_userlist')

        super().__init__(*args,**kwargs)        

        mem = self.instance
        timezone = mem.company.timezone
        self.initial['birthday'] = funUTCtoLocal(mem.birthday, timezone)
        self.initial['verifycode_date'] = funUTCtoLocal(mem.verifycode_date, timezone)

        # readonly
        self.fields['username'].widget.attrs['readonly'] = 'readonly'
        self.fields['number'].widget.attrs['readonly'] = 'readonly'
        # hidden
        # self.fields['user'].widget.attrs['disabled'] = 'disabled'

    class Meta:        
        model = Member
        fields = ['username', 'password', 'number', 'firstname', 'lastname', 'nickname', 'enabled', 'verified', 'verifycode', 'verifycode_date', 'birthday', 'gender', 'memberpoints',  'memberpointtotal', 'memberlevel', 'mobilephone_country', 'mobilephone', 'email', 'remark']
        widgets = {
            'birthday': DateInput(),
            # 'verifycode_date': DateTimeInput(),
        }

class MemberNewForm(ModelForm):
    def __init__(self, *args,**kwargs):
        self.company = kwargs.pop('company')

        super().__init__(*args,**kwargs)        
        # For new form initial value of Branch is null
        datetime_now = datetime.now()
        timezone = self.company.timezone
        # Initial value:
        # self.initial['birthday'] = '1990-01-01'
        # self.fields['birthday'].widget=forms.widgets.DateTimeInput( format='%Y-%m-%d', )

    class Meta:        
        model = Member
        fields = ['username', 'password', 'firstname', 'lastname', 'nickname', 'enabled', 'birthday', 'gender', 'memberpoints', 'memberpointtotal', 'memberlevel', 'mobilephone', 'email', 'remark']
        widgets = {
            'birthday': DateInput(),
            # 'verifycode_date': DateTimeInput(),
        }

class SupplierUpdateForm(ModelForm):
    def __init__(self, *args,**kwargs):
        self.company = kwargs.pop('company')
        super().__init__(*args,**kwargs)        
    class Meta:        
        model = Supplier
        fields = ['supplier_company', 'contact', 'phone', 'address', 'website', 'email']

class SupplierNewForm(ModelForm):
    def __init__(self, *args,**kwargs):
        self.company = kwargs.pop('company')
        super().__init__(*args,**kwargs)        
    class Meta:        
        model = Supplier
        fields = ['supplier_company', 'contact', 'phone', 'address', 'website', 'email']

class CustomerUpdateForm(ModelForm):
    def __init__(self, *args,**kwargs):
        self.company = kwargs.pop('company')
        super().__init__(*args,**kwargs)        
        self.fields['group'].queryset = CustomerGroup.objects.filter(company=self.company)
        self.fields['source'].queryset = CustomerSource.objects.filter(company=self.company)
        self.fields['information'].queryset = CustomerInformation.objects.filter(company=self.company)
    class Meta:        
        model = Customer
        fields = ['companyname',  'address','contact', 'phone', 'email', 'fax', 'referby', 'group', 'source', 'information' , 'member', 'remark']

class CustomerNewForm(ModelForm):
    Sales = forms.fields.CharField()
    def __init__(self, *args,**kwargs):
        self.company = kwargs.pop('company')
        self.user = kwargs.pop('user')
        super().__init__(*args,**kwargs)        
        self.fields['group'].queryset = CustomerGroup.objects.filter(company=self.company)
        self.fields['source'].queryset = CustomerSource.objects.filter(company=self.company)
        self.fields['information'].queryset = CustomerInformation.objects.filter(company=self.company)
        # readonly
        # set fields is text fields
        self.fields['Sales'].widget=forms.widgets.TextInput()
        self.fields['Sales'].widget.attrs['readonly'] = 'readonly'
        self.initial['Sales'] = self.user.first_name + ' ' + self.user.last_name + ' (' + self.user.username + ')'
    class Meta:        
        model = Customer
        fields = ['companyname', 'contact', 'phone', 'email', 'fax', 'address', 'referby', 'group', 'source', 'information' , 'member', 'remark', 'Sales']

class CustomerGroupForm(forms.ModelForm): 
    id = forms.fields.IntegerField()
    def __init__(self, *args,**kwargs):
        super().__init__(*args,**kwargs)        
        self.initial['id'] = self.instance.pk
    class Meta:
        model = CustomerGroup
        fields = ['id', 'name', 'description']

class CustomerSourceForm(forms.ModelForm): 
    id = forms.fields.IntegerField()
    def __init__(self, *args,**kwargs):
        super().__init__(*args,**kwargs)        
        self.initial['id'] = self.instance.pk
    class Meta:
        model = CustomerSource
        fields = ['id', 'name', 'description']

class CustomerInfoForm(forms.ModelForm): 
    id = forms.fields.IntegerField()
    def __init__(self, *args,**kwargs):
        super().__init__(*args,**kwargs)        
        self.initial['id'] = self.instance.pk
    class Meta:
        model = CustomerInformation
        fields = ['id', 'name', 'description']

class QuotationUpdateForm(ModelForm):
    def __init__(self, *args,**kwargs):
        self.company = kwargs.pop('company')
        super().__init__(*args,**kwargs)
        # self.fields['group'].queryset = CustomerGroup.objects.filter(company=self.company)
        # self.fields['source'].queryset = CustomerSource.objects.filter(company=self.company)
        # self.fields['information'].queryset = CustomerInformation.objects.filter(company=self.company)
        self.fields['businesstype'].queryset = BusinessType.objects.filter(company=self.company)
        self.fields['businesssource'].queryset = BusinessSource.objects.filter(company=self.company)
    class Meta:
        model = Quotation
        fields = ['quotation_status', 'customer', 'customer_companyname', 'customer_contact', 'customer_phone', 'customer_email', 'businesstype', 'businesssource', 'sales', 'confirm_by', 'confirm_date', 'remark', 'terms' , 'total',]

class BusinessTypeForm(forms.ModelForm):
    id = forms.fields.IntegerField()
    def __init__(self, *args,**kwargs):
        super().__init__(*args,**kwargs)
        self.initial['id'] = self.instance.pk
    class Meta:
        model = BusinessType
        fields = ['id', 'name', 'description']

class BusinessSourceForm(forms.ModelForm):
    id = forms.fields.IntegerField()
    def __init__(self, *args,**kwargs):
        super().__init__(*args,**kwargs)
        self.initial['id'] = self.instance.pk
    class Meta:
        model = BusinessSource
        fields = ['id', 'name', 'description']

class InvoiceUpdateForm(ModelForm):
    def __init__(self, *args,**kwargs):
        self.company = kwargs.pop('company')
        super().__init__(*args,**kwargs)        
        # self.fields['group'].queryset = CustomerGroup.objects.filter(company=self.company)
        # self.fields['source'].queryset = CustomerSource.objects.filter(company=self.company)
        # self.fields['information'].queryset = CustomerInformation.objects.filter(company=self.company)
        
    class Meta:        
        model = Invoice
        fields = ['invoice_type', 'invoice_status', 'customer', 'customer_companyname', 'customer_contact', 'customer_phone', 'customer_email', 'sales', 'confirm_by', 'confirm_date', 'remark', 'terms', 'payment_method' , 'total']        

class ReceiptUpdateForm(ModelForm):
    def __init__(self, *args,**kwargs):
        self.company = kwargs.pop('company')
        super().__init__(*args,**kwargs)        
        # self.fields['group'].queryset = CustomerGroup.objects.filter(company=self.company)
        # self.fields['source'].queryset = CustomerSource.objects.filter(company=self.company)
        # self.fields['information'].queryset = CustomerInformation.objects.filter(company=self.company)
        
    class Meta:        
        model = Receipt
        fields = ['payment', 'customer', 'customer_companyname', 'customer_contact', 'customer_phone', 'customer_email', 'sales', 'confirm_by', 'confirm_date', 'remark', 'total',]
         