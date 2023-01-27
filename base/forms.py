# from ast import Mod
#from dataclasses import field
from django.forms import ModelForm, forms
from django.contrib.auth.models import User, Group
from django.db.models import Q
from base.models import TicketFormat, TicketRoute, UserProfile
from captcha.fields import ReCaptchaField
from captcha.widgets import ReCaptchaV2Checkbox

class CaptchaForm(forms.Form):
    captcha = ReCaptchaField(
    widget = ReCaptchaV2Checkbox(
        attrs={
            'data-theme': 'dark',
        }
    )
    )

    # captcha = ReCaptchaField()


class UserForm(ModelForm):
    class Meta:
        model = User 
        fields = ['is_active', 'first_name', 'last_name', 'email', 'groups']
    def __init__(self, *args,**kwargs):
        super (UserForm,self ).__init__(*args,**kwargs)
        self.fields['groups'].queryset = Group.objects.filter(~Q(name='api'), ~Q(name='web'))   # Q(groups__name='api')

class UserFormAdmin(ModelForm):
# admin can not change himself group and cannot set is_active
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']
        
class UserProfileForm(ModelForm):
    class Meta:
        model = UserProfile
        fields = ['tickettype', 'queuepriority', 'branchs', 'staffnumber']

class TicketFormatForm(ModelForm):
    class Meta:
        model = TicketFormat
        fields = ['enabled', 'ttype', 'branch', 'tformat']

class trForm(ModelForm):
    class Meta:
        model = TicketRoute 
        fields = ['enabled', 'branch', 'tickettype', 'step', 'countertype']
    