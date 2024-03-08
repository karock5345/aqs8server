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
from captcha.fields import ReCaptchaField
from captcha.widgets import ReCaptchaV2Checkbox
from .api.views import funUTCtoLocal, funLocaltoUTC, funUTCtoLocaltime, funLocaltoUTCtime
import pytz
from django.utils.timezone import localtime, get_current_timezone
from datetime import datetime

class CaptchaForm(forms.Form):
    captcha = ReCaptchaField(
    widget = ReCaptchaV2Checkbox(
        attrs={
            'data-theme': 'dark',
        }
    )
    )

    # captcha = ReCaptchaField()

class BranchSettingsForm_Admin(ModelForm):
    
    # enabled = forms.fields.BooleanField(label='Enable Branch', required=False)
    # subscribe = forms.fields.BooleanField(label='Enable Subscribe', required=False)
    # substart = forms.fields.DateTimeField(label='Subscribe start date (local time)' , widget=forms.widgets.DateTimeInput( attrs={'type':'datetime-local', 'step':'1'}))
    # subend = forms.fields.DateTimeField(label='Subscribe end date (local time)', widget=forms.widgets.DateTimeInput( attrs={'type':'datetime-local', 'step':'1'}))

    # name = forms.fields.CharField(label='Branch Name')
    # address = forms.fields.CharField(label='Branch Address')
    # gps = forms.fields.CharField(label='GPS', required=False)
    # officehourstart = forms.fields.TimeField(label='Office Hour open time (local time)', widget=forms.widgets.TimeInput( attrs={'type':'time', 'step':'1'}))
    # officehourend = forms.fields.TimeField(label='Office Hour close time (local time)', widget=forms.widgets.TimeInput( attrs={'type':'time', 'step':'1'}))
    # tickettimestart = forms.fields.TimeField(label='Ticket start time (local time)', widget=forms.widgets.TimeInput( attrs={'type':'time', 'step':'1'}))
    # tickettimeend = forms.fields.TimeField(label='Ticket end time (local time)', widget=forms.widgets.TimeInput( attrs={'type':'time', 'step':'1'}))

    # queuepriority = forms.fields.ChoiceField(label='Queue Priority', choices=Branch.PRIORITY)
    # queuemask = forms.fields.CharField(label='Queue Mask')
    # ticketmax = forms.fields.IntegerField(label='Ticket max number')
    # ticketnext = forms.fields.IntegerField(label='Ticket next number')
    # ticketnoformat = forms.fields.CharField(label='Ticket number format ("000" means: A001, B049)')
    # ticketrepeatnumber = forms.fields.BooleanField(label='Ticket repeat number (False: A001 -> B002 -> A003)', required=False)
    
    
    # displayenabled = forms.fields.BooleanField(label='Enable display', required=False)
    # displayflashtime = forms.fields.IntegerField(label='Display flash time (0-50)')

    # voiceenabled = forms.fields.BooleanField(label='Enable Voice announcement', required=False)
    # language1 = forms.fields.CharField(label='First Language (0-4), 0 is not used')
    # language2 = forms.fields.CharField(label='Second Language (0-4), 0 is not used')
    # language3 = forms.fields.CharField(label='3rd Language (0-4), 0 is not used')
    # language4 = forms.fields.CharField(label='4th Language (0-4), 0 is not used')
    # usersinglelogin = forms.fields.BooleanField(label='User single login', required=False)
    # SMSenabled = forms.fields.BooleanField(label='Enable SMS', required=False)
    # SMSmsg = forms.fields.CharField(label='SMS Message', required=False)
    # websoftkey_show_waitinglist = forms.fields.BooleanField(label='Web-Softkey show waiting list', required=False)
    
    # # Booking settings
    # bookingenabled = forms.fields.BooleanField(label='Enable Booking Function', required=False)
    # bookingPage1Text = forms.fields.CharField(label='Booking HTML page 1 Text', help_text='Booking HTML page 1 Text, [[ADDR]] is branch.address.', required=False, widget=forms.Textarea())
    # bookingPage1ScrollingText = forms.fields.CharField(label='Booking HTML page 1 Scrolling Text', help_text='Booking HTML page 1 Scrolling Text, [[ADDR]] is branch.address.', required=False, widget=forms.Textarea())
    # bookingPage2Text = forms.fields.CharField(label='Booking HTML page 2 Text', help_text='Booking HTML page 1 Text, [[ADDR]] is branch.address.', required=False, widget=forms.Textarea())
    # bookingPage2ScrollingText = forms.fields.CharField(label='Booking HTML page 1 Scrolling Text', help_text='Booking HTML page 2 Scrolling Text, [[ADDR]] is branch.address.', required=False, widget=forms.Textarea())
    # bookingPage3Text = forms.fields.CharField(label='Booking HTML Success Text', help_text='Booking success text, [[ADDR]] is branch address, [[NAME]] is customer name, [[DATE]] is booking start date, [[TIME]] is booking start time. [[WEEK]] is week.', required=False, widget=forms.Textarea())
    # # bookingSuccessEmailSubject = forms.fields.CharField(label='Booking Email Success Subject' , required=False)
    
    # bookingSuccessEmailBody = forms.fields.CharField(label='Booking Email Success Body' , required=False, widget=forms.Textarea())
    # bookingSMS = forms.fields.BooleanField(label='Enable send SMS after booking success', required=False)
    # bookingSMSSuccess = forms.fields.CharField(label='Booking SMS Text', required=False, widget=forms.Textarea())



    def __init__(self, *args, **kwargs):
        super(BranchSettingsForm_Admin, self).__init__(*args, **kwargs)
        # change time from DB utc to local time
        timezone = self.initial['timezone']
        self.initial['officehourstart'] = funUTCtoLocaltime(self.initial['officehourstart'], timezone)
        self.initial['officehourend'] = funUTCtoLocaltime(self.initial['officehourend'], timezone)
        self.initial['tickettimestart'] = funUTCtoLocaltime(self.initial['tickettimestart'], timezone)
        self.initial['tickettimeend'] = funUTCtoLocaltime(self.initial['tickettimeend'], timezone)
        self.initial['substart'] = funUTCtoLocal(self.initial['substart'], timezone)
        self.initial['subend'] = funUTCtoLocal(self.initial['subend'], timezone)
        # enabled = forms.fields.BooleanField(label='Enable Branch', required=False)
        self.fields['enabled'] = forms.fields.BooleanField(label='Enable Branch', required=False, help_text=self.fields['enabled'].help_text)
        self.fields['subscribe'] = forms.fields.BooleanField(label='Enable Subscribe', required=False, help_text=self.fields['subscribe'].help_text)
        self.fields['substart'] = forms.fields.DateTimeField(label='Subscribe start date (local time)' , widget=forms.widgets.DateTimeInput( attrs={'type':'datetime-local', 'step':'1'}), help_text=self.fields['substart'].help_text)
        self.fields['subend'] = forms.fields.DateTimeField(label='Subscribe end date (local time)', widget=forms.widgets.DateTimeInput( attrs={'type':'datetime-local', 'step':'1'}), help_text=self.fields['subend'].help_text)
        self.fields['name'] = forms.fields.CharField(label='Branch Name', help_text=self.fields['name'].help_text, widget=forms.widgets.TextInput())
        self.fields['address'] = forms.fields.CharField(label='Branch Address', help_text=self.fields['address'].help_text)
        self.fields['gps'] = forms.fields.CharField(label='GPS of the Branch', required=False, help_text=self.fields['gps'].help_text)
        self.fields['timezone'] = forms.fields.ChoiceField(label='Timezone', choices=[(x, x) for x in pytz.all_timezones], help_text=self.fields['timezone'].help_text)
        self.fields['officehourstart'] = forms.fields.TimeField(label='Office Hour open time (local time)', widget=forms.widgets.TimeInput( attrs={'type':'time', 'step':'1'}), help_text=self.fields['officehourstart'].help_text)
        self.fields['officehourend'] = forms.fields.TimeField(label='Office Hour close time (local time)', widget=forms.widgets.TimeInput( attrs={'type':'time', 'step':'1'}), help_text=self.fields['officehourend'].help_text)
        self.fields['tickettimestart'] = forms.fields.TimeField(label='Ticket start time (local time)', widget=forms.widgets.TimeInput( attrs={'type':'time', 'step':'1'}), help_text=self.fields['tickettimestart'].help_text)
        self.fields['tickettimeend'] = forms.fields.TimeField(label='Ticket end time (local time)', widget=forms.widgets.TimeInput( attrs={'type':'time', 'step':'1'}), help_text=self.fields['tickettimeend'].help_text)
        self.fields['queuepriority'] = forms.fields.ChoiceField(label='Queue Priority', choices=Branch.PRIORITY, help_text=self.fields['queuepriority'].help_text)
        self.fields['queuemask'] = forms.fields.CharField(label='Queue Mask', help_text=self.fields['queuemask'].help_text)
        self.fields['ticketmax'] = forms.fields.IntegerField(label='Ticket max number', help_text=self.fields['ticketmax'].help_text)
        self.fields['ticketnext'] = forms.fields.IntegerField(label='Ticket next number', help_text=self.fields['ticketnext'].help_text)
        self.fields['ticketnoformat'] = forms.fields.CharField(label='Ticket number format ("000" means: A001, B049)', help_text=self.fields['ticketnoformat'].help_text)
        self.fields['ticketrepeatnumber'] = forms.fields.BooleanField(label='Ticket repeat number (False: A001 -> B002 -> A003)', required=False, help_text=self.fields['ticketrepeatnumber'].help_text)
        self.fields['displayenabled'] = forms.fields.BooleanField(label='Enable display', required=False, help_text=self.fields['displayenabled'].help_text)
        self.fields['displayflashtime'] = forms.fields.IntegerField(label='Display flash time (0-50)', help_text=self.fields['displayflashtime'].help_text)
        self.fields['voiceenabled'] = forms.fields.BooleanField(label='Enable Voice announcement', required=False, help_text=self.fields['voiceenabled'].help_text)
        self.fields['language1'] = forms.fields.CharField(label='First Language (0-4), 0 is not used', help_text=self.fields['language1'].help_text)
        self.fields['language2'] = forms.fields.CharField(label='Second Language (0-4), 0 is not used', help_text=self.fields['language2'].help_text)
        self.fields['language3'] = forms.fields.CharField(label='3rd Language (0-4), 0 is not used', help_text=self.fields['language3'].help_text)
        self.fields['language4'] = forms.fields.CharField(label='4th Language (0-4), 0 is not used', help_text=self.fields['language4'].help_text)
        self.fields['usersinglelogin'] = forms.fields.BooleanField(label='User single login', required=False, help_text=self.fields['usersinglelogin'].help_text)
        self.fields['SMSenabled'] = forms.fields.BooleanField(label='Enable SMS', required=False, help_text=self.fields['SMSenabled'].help_text)
        self.fields['SMSmsg'] = forms.fields.CharField(label='SMS Message', required=False, help_text=self.fields['SMSmsg'].help_text)
        self.fields['websoftkey_show_waitinglist'] = forms.fields.BooleanField(label='Web-Softkey show waiting list', required=False, help_text=self.fields['websoftkey_show_waitinglist'].help_text)
        self.fields['bookingenabled'] = forms.fields.BooleanField(label='Enable Booking Function', required=False, help_text=self.fields['bookingenabled'].help_text)
        self.fields['bookingPage1Text'] = forms.fields.CharField(label='Booking HTML page 1 Text', help_text=self.fields['bookingPage1Text'].help_text, required=False, widget=forms.Textarea(),)
        self.fields['bookingPage1ScrollingText'] = forms.fields.CharField(label='Booking HTML page 1 Scrolling Text', help_text=self.fields['bookingPage1ScrollingText'].help_text, required=False, widget=forms.Textarea())
        self.fields['bookingPage2Text'] = forms.fields.CharField(label='Booking HTML page 2 Text', help_text=self.fields['bookingPage2Text'].help_text, required=False, widget=forms.Textarea())
        self.fields['bookingPage2ScrollingText'] = forms.fields.CharField(label='Booking HTML page 1 Scrolling Text', help_text=self.fields['bookingPage2ScrollingText'].help_text, required=False, widget=forms.Textarea())
        self.fields['bookingPage3Text'] = forms.fields.CharField(label='Booking HTML Success Text', help_text=self.fields['bookingPage3Text'].help_text, required=False, widget=forms.Textarea())
        self.fields['bookingSuccessEmailSubject'] = forms.fields.CharField(label='Booking Email Success Subject' , required=False, widget=forms.TextInput(), help_text=self.fields['bookingSuccessEmailSubject'].help_text)
        self.fields['bookingSuccessEmailBody'] = forms.fields.CharField(label='Booking Email Success Body' , required=False, widget=forms.Textarea(), help_text=self.fields['bookingSuccessEmailBody'].help_text)
        self.fields['bookingSMSSuccessEnabled'] = forms.fields.BooleanField(label='Enable send SMS after booking success', required=False, help_text=self.fields['bookingSMSSuccessEnabled'].help_text)
        # self.fields['bookingSMSSuccess'] = forms.fields.CharField(label='Booking SMS Text', required=False, widget=forms.Textarea(), help_text=self.fields['bookingSMSSuccess'].help_text)
        self.fields['bookingNewEmailSubject'] = forms.fields.CharField(required=False, widget=forms.TextInput(), help_text=self.fields['bookingNewEmailSubject'].help_text)
        # self.fields['bookingNewEmailUser'] = forms.fields.MultipleChoiceField( widget=forms.CheckboxSelectMultiple(), choices=User.objects.all().values_list('id', 'username'), help_text=self.fields['bookingNewEmailUser'].help_text)
        # self.initial['bookingNewEmailUser'] = self.instance.bookingNewEmailUser.all().values_list('id', flat=True)
    class Meta:
        model = Branch
        fields = ['enabled', 'subscribe', 'substart', 'subend',
                  'name', 'address', 'gps', 
                  'timezone', 'officehourstart', 'officehourend', 'tickettimestart', 'tickettimeend', 
                  'queueenabled',
                  'queuepriority', 'queuemask', 'ticketmax', 'ticketnext', 'ticketnoformat', 'ticketrepeatnumber',
                  'displayenabled', 'displayflashtime', 
                  'voiceenabled', 'language1', 'language2', 'language3', 'language4', 
                  'usersinglelogin', 'websoftkey_show_waitinglist', 
                  'SMSenabled', 'SMSmsg', 'SMSQuota', 'SMSUsed', 'SMSResetDay',
                  'bookingenabled', 'bookingPage1ScrollingText', 'bookingPage1Text', 'bookingPage2ScrollingText', 'bookingPage2Text', 'bookingPage3Text',
                  'bookingSuccessEmailEnabled', 'bookingSuccessEmailSubject', 'bookingSuccessEmailBody', 'bookingSMSSuccessEnabled', 'bookingSMSSuccess',
                  'bookingNewEmailEnabled', 'bookingNewEmailUser', 'bookingNewEmailSubject', 'bookingNewEmailBody',
                  ]        
        
        
class BranchSettingsForm_Adv(ModelForm):
    # enabled = forms.fields.BooleanField(label='Enable Branch', required=False)
    # subscribe = forms.fields.BooleanField(label='Enable Subscribe', required=False)
    # substart = forms.fields.DateTimeField(label='Subscribe start date (local time)' , widget=forms.widgets.DateTimeInput( attrs={'type':'datetime-local', 'step':'1'}))
    # subend = forms.fields.DateTimeField(label='Subscribe end date (local time)', widget=forms.widgets.DateTimeInput( attrs={'type':'datetime-local', 'step':'1'}))

    name = forms.fields.CharField(label='Branch Name')
    address = forms.fields.CharField(label='Branch Address')
    gps = forms.fields.CharField(label='GPS', required=False)
    officehourstart = forms.fields.TimeField(label='Office Hour open time (local time)', widget=forms.widgets.TimeInput( attrs={'type':'time', 'step':'1'}))
    officehourend = forms.fields.TimeField(label='Office Hour close time (local time)', widget=forms.widgets.TimeInput( attrs={'type':'time', 'step':'1'}))
    tickettimestart = forms.fields.TimeField(label='Ticket start time (local time)', widget=forms.widgets.TimeInput( attrs={'type':'time', 'step':'1'}))
    tickettimeend = forms.fields.TimeField(label='Ticket end time (local time)', widget=forms.widgets.TimeInput( attrs={'type':'time', 'step':'1'}))

    queuepriority = forms.fields.ChoiceField(label='Queue Priority', choices=Branch.PRIORITY)
    queuemask = forms.fields.CharField(label='Queue Mask')
    ticketmax = forms.fields.IntegerField(label='Ticket max number')
    ticketnext = forms.fields.IntegerField(label='Ticket next number')
    ticketnoformat = forms.fields.CharField(label='Ticket number format ("000" means: A001, B049)')
    ticketrepeatnumber = forms.fields.BooleanField(label='Ticket repeat number (False: A001 -> B002 -> A003)', required=False)
    
    
    displayenabled = forms.fields.BooleanField(label='Enable display', required=False)
    displayflashtime = forms.fields.IntegerField(label='Display flash time (0-50)')

    voiceenabled = forms.fields.BooleanField(label='Enable Voice announcement', required=False)
    language1 = forms.fields.CharField(label='First Language (0-4), 0 is not used')
    language2 = forms.fields.CharField(label='Second Language (0-4), 0 is not used')
    language3 = forms.fields.CharField(label='3rd Language (0-4), 0 is not used')
    language4 = forms.fields.CharField(label='4th Language (0-4), 0 is not used')
    usersinglelogin = forms.fields.BooleanField(label='User single login', required=False)
    # SMSenabled = forms.fields.BooleanField(label='Enable SMS', required=False)
    # SMSmsg = forms.fields.CharField(label='SMS Message', required=False)
    websoftkey_show_waitinglist = forms.fields.BooleanField(label='Web-Softkey show waiting list', required=False)

    class Meta:
        model = Branch
        # fields = ['enabled', 'subscribe', 'substart', 'subend',
        #           'name', 'address', 'gps', 
        #           'timezone', 'officehourstart', 'officehourend', 'tickettimestart', 'tickettimeend', 
        #           'queuepriority', 'queuemask', 'ticketmax', 'ticketnext', 'ticketnoformat', 'ticketrepeatnumber',
        #           'displayenabled', 'displayflashtime', 
        #           'voiceenabled', 'language1', 'language2', 'language3', 'language4', 
        #           'usersinglelogin', 'SMSenabled', 'SMSmsg']
        fields = [
                  'name', 'address', 'gps', 
                  'timezone', 'officehourstart', 'officehourend', 'tickettimestart', 'tickettimeend', 
                  'queuepriority', 'queuemask', 'ticketmax', 'ticketnext', 'ticketnoformat', 'ticketrepeatnumber',
                  'displayenabled', 'displayflashtime', 
                  'voiceenabled', 'language1', 'language2', 'language3', 'language4', 
                  'usersinglelogin', 'websoftkey_show_waitinglist']
    def __init__(self, *args, **kwargs):
        super(BranchSettingsForm_Adv, self).__init__(*args, **kwargs)
        # change time from DB utc to local time
        branch = self.instance
        timezone = branch.timezone
        self.initial['officehourstart'] = funUTCtoLocaltime(self.initial['officehourstart'], timezone)
        self.initial['officehourend'] = funUTCtoLocaltime(self.initial['officehourend'], timezone)
        self.initial['tickettimestart'] = funUTCtoLocaltime(self.initial['tickettimestart'], timezone)
        self.initial['tickettimeend'] = funUTCtoLocaltime(self.initial['tickettimeend'], timezone)


class BranchSettingsForm_Basic(ModelForm):
    # enabled = forms.fields.BooleanField(label='Enable Branch', required=False)
    # subscribe = forms.fields.BooleanField(label='Enable Subscribe', required=False)
    # substart = forms.fields.DateTimeField(label='Subscribe start date (local time)' , widget=forms.widgets.DateTimeInput( attrs={'type':'datetime-local', 'step':'1'}))
    # subend = forms.fields.DateTimeField(label='Subscribe end date (local time)', widget=forms.widgets.DateTimeInput( attrs={'type':'datetime-local', 'step':'1'}))

    name = forms.fields.CharField(label='Branch Name')
    address = forms.fields.CharField(label='Branch Address')
    gps = forms.fields.CharField(label='GPS', required=False)
    officehourstart = forms.fields.TimeField(label='Office Hour open time (local time)', widget=forms.widgets.TimeInput( attrs={'type':'time', 'step':'1'}))
    officehourend = forms.fields.TimeField(label='Office Hour close time (local time)', widget=forms.widgets.TimeInput( attrs={'type':'time', 'step':'1'}))
    tickettimestart = forms.fields.TimeField(label='Ticket start time (local time)', widget=forms.widgets.TimeInput( attrs={'type':'time', 'step':'1'}))
    tickettimeend = forms.fields.TimeField(label='Ticket end time (local time)', widget=forms.widgets.TimeInput( attrs={'type':'time', 'step':'1'}))

    # queuepriority = forms.fields.ChoiceField(label='Queue Priority', choices=Branch.PRIORITY)
    # queuemask = forms.fields.CharField(label='Queue Mask')
    # ticketmax = forms.fields.IntegerField(label='Ticket max number')
    # ticketnext = forms.fields.IntegerField(label='Ticket next number')
    # ticketnoformat = forms.fields.CharField(label='Ticket number format ("000" means: A001, B049)')
    # ticketrepeatnumber = forms.fields.BooleanField(label='Ticket repeat number (False: A001 -> B002 -> A003)', required=False)
    
    
    # displayenabled = forms.fields.BooleanField(label='Enable display', required=False)
    # displayflashtime = forms.fields.IntegerField(label='Display flash time (0-50)')

    # voiceenabled = forms.fields.BooleanField(label='Enable Voice announcement', required=False)
    # language1 = forms.fields.CharField(label='First Language (0-4), 0 is not used')
    # language2 = forms.fields.CharField(label='Second Language (0-4), 0 is not used')
    # language3 = forms.fields.CharField(label='3rd Language (0-4), 0 is not used')
    # language4 = forms.fields.CharField(label='4th Language (0-4), 0 is not used')
    # usersinglelogin = forms.fields.BooleanField(label='User single login', required=False)
    # SMSenabled = forms.fields.BooleanField(label='Enable SMS', required=False)
    # SMSmsg = forms.fields.CharField(label='SMS Message', required=False)

    class Meta:
        model = Branch
        # fields = ['enabled', 'subscribe', 'substart', 'subend',
        #           'name', 'address', 'gps', 
        #           'timezone', 'officehourstart', 'officehourend', 'tickettimestart', 'tickettimeend', 
        #           'queuepriority', 'queuemask', 'ticketmax', 'ticketnext', 'ticketnoformat', 'ticketrepeatnumber',
        #           'displayenabled', 'displayflashtime', 
        #           'voiceenabled', 'language1', 'language2', 'language3', 'language4', 
        #           'usersinglelogin', 'SMSenabled', 'SMSmsg']
        fields = ['name', 'address', 'gps', 
                  'officehourstart', 'officehourend', 'tickettimestart', 'tickettimeend',                   
                  ]

    def __init__(self, *args, **kwargs):
        super(BranchSettingsForm_Basic, self).__init__(*args, **kwargs)
        # change time from DB utc to local time
        # get branch
        branch = self.instance
        timezone = branch.timezone
        self.initial['officehourstart'] = funUTCtoLocaltime(self.initial['officehourstart'], timezone)
        self.initial['officehourend'] = funUTCtoLocaltime(self.initial['officehourend'], timezone)
        self.initial['tickettimestart'] = funUTCtoLocaltime(self.initial['tickettimestart'], timezone)
        self.initial['tickettimeend'] = funUTCtoLocaltime(self.initial['tickettimeend'], timezone)
        # self.initial['substart'] = funUTCtoLocal(self.initial['substart'], timezone)
        # self.initial['subend'] = funUTCtoLocal(self.initial['subend'], timezone)


# for PCCW manager Group only include frontline and manager
class UserFormManager(ModelForm):
    class Meta:
        model = User 
        fields = ['is_active', 'first_name', 'last_name', 'email', 'groups']
    def __init__(self, *args,**kwargs):
        super (UserFormManager,self ).__init__(*args,**kwargs)
        self.fields['groups'].queryset = Group.objects.filter(Q(name='manager') | Q(name='frontline'))   # Q(groups__name='api')

        

# for PCCW manager Group only include frontline and manager and support
class UserFormSupport(ModelForm):
    class Meta:
        model = User 
        fields = ['is_active', 'first_name', 'last_name', 'email', 'groups']
    def __init__(self, *args,**kwargs):
        super (UserFormSupport,self ).__init__(*args,**kwargs)
        self.fields['groups'].queryset = Group.objects.filter(Q(name='manager')| Q(name='frontline')| Q(name='support'))   # Q(groups__name='api')


# for PCCW manager Group only include frontline and manager and support and admin
class UserFormAdmin(ModelForm):
    class Meta:
        model = User 
        fields = ['is_active', 'first_name', 'last_name', 'email', 'groups']
    def __init__(self, *args,**kwargs):
        super (UserFormAdmin,self ).__init__(*args,**kwargs)
        self.fields['groups'].queryset = Group.objects.filter(Q(name='manager')| Q(name='frontline')| Q(name='support')| Q(name='admin'))   # Q(groups__name='api')

class UserForm(ModelForm):
    class Meta:
        model = User 
        fields = ['is_active', 'first_name', 'last_name', 'email', 'groups']
    def __init__(self, *args,**kwargs):
        auth_grouplist = kwargs.pop('auth_grouplist')
        super ().__init__(*args,**kwargs)
        self.fields['groups'].queryset = Group.objects.filter(id__in=auth_grouplist)   
        # self.fields['groups'].queryset = Group.objects.filter()   # Q(groups__name='api')
        # here we can filter the groups by user branchs
        
class UserFormAdminSelf(ModelForm):
# admin can not change himself group and cannot set is_active
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']


class UserFormSuper(ModelForm):
    class Meta:
        model = User 
        fields = ['is_active', 'is_active', 'first_name', 'last_name', 'email', 'groups']
    def __init__(self, *args,**kwargs):
        super (UserFormSuper,self ).__init__(*args,**kwargs)
        self.fields['groups'].queryset = Group.objects.filter(~Q(name='web'))  

        
class UserProfileForm(ModelForm):
    class Meta:
        model = UserProfile

        fields = ['tickettype', 'queuepriority', 'branchs', 'staffnumber', 'mobilephone']
    def __init__(self, *args,**kwargs):
        self.auth_branchs = kwargs.pop('auth_branchs')
        super().__init__(*args,**kwargs)
        self.fields['branchs'].queryset = Branch.objects.filter(id__in=self.auth_branchs)   # Q(groups__name='api')
        
class newTicketTypeForm(forms.Form):
    new_tickettype = forms.CharField(label='New Ticket Type', max_length=100)

class TicketFormatForm(ModelForm):
    def __init__(self, *args,**kwargs):
        self.auth_branchs = kwargs.pop('auth_branchs')
        super().__init__(*args,**kwargs)
        self.fields['branch'].queryset = Branch.objects.filter(id__in=self.auth_branchs) 
    class Meta:
        model = TicketFormat
        fields = ['enabled', 'ttype', 'branch', 'tformat', 'touchkey_lang1', 'touchkey_lang2', 'touchkey_lang3', 'touchkey_lang4']

class trForm(ModelForm):
    def __init__(self, *args,**kwargs):
        self.auth_branchs = kwargs.pop('auth_branchs')
        super().__init__(*args,**kwargs)
        self.fields['branch'].queryset = Branch.objects.filter(id__in=self.auth_branchs)
        self.fields['countertype'].queryset = CounterType.objects.filter(branch__in=self.auth_branchs)
    class Meta:
        model = TicketRoute 
        fields = ['enabled', 'branch', 'tickettype', 'step', 'countertype']

class getForm(forms.Form):
    ticketnumber = forms.CharField(label='Ticket Number', max_length=100)

class voidForm(forms.Form):
    tickettype = forms.CharField(label='Ticket Type', max_length=100)
    ticketnumber = forms.CharField(label='Ticket Number', max_length=100)
    tickettime = forms.DateField(label='Ticket Time')

class resetForm(forms.Form):
    new_password1 = forms.CharField(label='New password', max_length=100)