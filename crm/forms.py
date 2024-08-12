from django.forms import ModelForm
from django import forms
from django.contrib.auth.models import User, Group
from django.db.models import Q
from django.forms.utils import ErrorList
from base.models import TicketFormat, TicketRoute, UserProfile, Branch, CounterType
from .models import Member
from captcha.fields import ReCaptchaField
from captcha.widgets import ReCaptchaV2Checkbox
from base.api.views import funUTCtoLocal, funLocaltoUTC, funUTCtoLocaltime, funLocaltoUTCtime
import pytz
from django.utils.timezone import localtime, get_current_timezone
from datetime import datetime, timedelta

class MemberUpdateForm(ModelForm):
    birthday = forms.DateTimeField(label='Birthday', input_formats=['%Y-%m-%d'], widget=forms.widgets.DateInput( format='%Y-%m-%d', ))
    verifycode_date = forms.DateTimeField(label='Verifycode Date', input_formats=['%Y-%m-%d %H:%M'], widget=forms.widgets.DateInput( format='%Y-%m-%d %H:%M', ))

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


class MemberNewForm(ModelForm):
    birthday = forms.DateTimeField(label='Birthday', input_formats=['%Y-%m-%d'], widget=forms.widgets.DateInput( format='%Y-%m-%d', ))
    verifycode_date = forms.DateTimeField(label='Verifycode Date', input_formats=['%Y-%m-%d %H:%M'], widget=forms.widgets.DateInput( format='%Y-%m-%d %H:%M', ))

    def __init__(self, *args,**kwargs):
        self.company = kwargs.pop('company')

        super().__init__(*args,**kwargs)        
        # For new form initial value of Branch is null
        datetime_now = datetime.now()
        timezone = self.company.timezone
        # Initial value:
        self.initial['birthday'] = '1990-01-01'

    class Meta:        
        model = Member
        fields = ['username', 'password', 'firstname', 'lastname', 'nickname', 'enabled', 'birthday', 'gender', 'memberpoints', 'memberpointtotal', 'memberlevel', 'mobilephone', 'email', 'company', 'remark']
