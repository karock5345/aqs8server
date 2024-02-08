# from ast import Mod
#from dataclasses import field
from collections.abc import Mapping
from typing import Any
from django.core.files.base import File
from django.db.models.base import Model
from django.forms import ModelForm
from django import forms
from django.contrib.auth.models import User, Group
from django.db.models import Q
from django.forms.utils import ErrorList
from base.models import TicketFormat, TicketRoute, UserProfile, Branch, CounterType
from .models import TimeSlot
from captcha.fields import ReCaptchaField
from captcha.widgets import ReCaptchaV2Checkbox
from base.api.views import funUTCtoLocal, funLocaltoUTC, funUTCtoLocaltime, funLocaltoUTCtime
import pytz
from django.utils.timezone import localtime, get_current_timezone
from datetime import datetime, timedelta

class DetailsForm(forms.Form):
    name = forms.CharField(label='稱呼', max_length=100)
    mphone = forms.CharField(label='手提電話', max_length=100)
    email = forms.EmailField(label='電郵地址')

class TimeSlotForm(ModelForm):
    def __init__(self, *args,**kwargs):
        self.auth_branchs = kwargs.pop('auth_branchs')

        super().__init__(*args,**kwargs)        

        ts = self.instance
        timezone = ts.branch.timezone
        self.initial['start_date'] = funUTCtoLocal(ts.start_date, timezone)
        self.initial['end_date'] = funUTCtoLocal(ts.end_date, timezone)

        self.initial['show_date'] = funUTCtoLocal(ts.show_date, timezone)
        self.initial['show_end_date'] = funUTCtoLocal(ts.show_end_date, timezone)
       
        self.fields['branch'].queryset = Branch.objects.filter(id__in=self.auth_branchs)
        self.fields['user'].widget.attrs['disabled'] = 'disabled'
        self.fields['created_by_temp'].widget.attrs['disabled'] = 'disabled'
        self.fields['show_date'].widget=forms.widgets.DateTimeInput( format='%Y-%m-%d %H:%M', )
        self.fields['show_end_date'].widget=forms.widgets.DateTimeInput( format='%Y-%m-%d %H:%M', )
        self.fields['start_date'].widget=forms.widgets.DateTimeInput( format='%Y-%m-%d %H:%M', )
        self.fields['end_date'].widget=forms.widgets.DateTimeInput( format='%Y-%m-%d %H:%M', )
        
    class Meta:        
        model = TimeSlot
        fields = ['enabled', 'branch', 'start_date', 'end_date', 'show_date', 'show_end_date','slot_using', 'slot_available', 'slot_total',  'user', 'created_by_temp']

class TimeSlotNewForm(ModelForm):
    def __init__(self, *args,**kwargs):
        self.auth_branchs = kwargs.pop('auth_branchs')

        super().__init__(*args,**kwargs)        
        # For new form initial value of Branch is null
        datetime_now = datetime.now()

        # |show_date---show_end_date|---start_date---| 
        # show_date should be < show_end_date < start_date    
        start_date_default = datetime_now + timedelta(days=7)
        # start_date_default change seconds to '00'
        start_date_default = start_date_default.replace(second=0, microsecond=0)
        # start_date_default = funUTCtoLocal(start_date_default, timezone)
        self.initial['start_date'] = start_date_default
        end_date_default = start_date_default + timedelta(minutes=30)
        self.initial['end_date'] = end_date_default

        show_date_default = start_date_default - timedelta(days=7)
        self.initial['show_date'] = show_date_default
        show_date_end_default = start_date_default - timedelta(minutes=60)
        self.initial['show_end_date'] = show_date_end_default

        self.fields['branch'].queryset = Branch.objects.filter(id__in=self.auth_branchs)
        self.fields['user'].widget.attrs['disabled'] = 'disabled'
        self.fields['created_by_temp'].widget.attrs['disabled'] = 'disabled'
        self.fields['show_date'].widget=forms.widgets.DateTimeInput( format='%Y-%m-%d %H:%M', )
        self.fields['show_end_date'].widget=forms.widgets.DateTimeInput( format='%Y-%m-%d %H:%M', )
        self.fields['start_date'].widget=forms.widgets.DateTimeInput( format='%Y-%m-%d %H:%M', )
        self.fields['end_date'].widget=forms.widgets.DateTimeInput( format='%Y-%m-%d %H:%M', )
    class Meta:        
        model = TimeSlot
        fields = ['enabled', 'branch', 'start_date', 'end_date', 'show_date', 'show_end_date', 'slot_total',  'user', 'created_by_temp']

