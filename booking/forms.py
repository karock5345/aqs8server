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
from datetime import datetime


class TimeSlotForm(ModelForm):
    def __init__(self, *args,**kwargs):
        self.auth_branchs = kwargs.pop('auth_branchs')
        super().__init__(*args,**kwargs)
        self.fields['branch'].queryset = Branch.objects.filter(id__in=self.auth_branchs)
        self.fields['user'].widget.attrs['disabled'] = 'disabled'
        self.fields['created_by_temp'].widget.attrs['disabled'] = 'disabled'
    
        try:            
            ts = self.instance
            timezone = ts.branch.timezone
            self.initial['show_date'] = funUTCtoLocal(ts.show_date, timezone)
            self.initial['show_end_date'] = funUTCtoLocal(ts.show_end_date, timezone)
            self.initial['booking_date'] = funUTCtoLocal(ts.booking_date, timezone)
        except:
            # For new form initial value of Branch is null
            pass
        self.fields['show_date'].widget=forms.widgets.DateTimeInput( format='%Y-%m-%d %H:%M', )
        self.fields['show_end_date'].widget=forms.widgets.DateTimeInput( format='%Y-%m-%d %H:%M', )
        self.fields['booking_date'].widget=forms.widgets.DateTimeInput( format='%Y-%m-%d %H:%M', )

    class Meta:
        model = TimeSlot
        fields = ['enabled', 'branch', 'booking_date','show_date', 'show_end_date',  'status', 'slot_total', 'slot_available',  'user', 'created_by_temp']

