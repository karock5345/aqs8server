from django.contrib import admin
from django.db import models
from django import forms
from .models import TicketTemp, testingModel, Branch, CounterLoginLog, CounterStatus, DisplayAndVoice,  TicketFormat
from .models import UserProfile, CounterType, Ticket, TicketLog, TicketRoute, TicketData, APILog, Setting, PrinterStatus, SystemLog
# Register your models here.

class testingView(admin.ModelAdmin):
    model = testingModel
    list_display =('name', 'des')

class UserProfileView(admin.ModelAdmin):
    list_display =('user', 'tickettype')
    ordering = ('-updated', '-created')
        

class BranchProfileView(admin.ModelAdmin):
    list_display =(  'bcode', 'name', 'address', 'enabled', )
    ordering = ('-updated', '-created')

class TicketFormatView(admin.ModelAdmin):
    list_display =( 'branch', 'ttype' ,'enabled')
    ordering=('branch', 'ttype')



class CounterTypeView(admin.ModelAdmin):
    list_display =( 'branch', 'name', 'lang1', 'lang2', 'enabled',)



class TicketView(admin.ModelAdmin):

    # formfield_overrides = {
    #     models.DateTimeField: {'widget': forms.DateTimeInput(format='%Y-%m-%d %H:%M:%S.%f')},
    #     # models.DateTimeField(attrs={'supports_microseconds' : True} ),
    # }
    list_display =('branch', 'countertype', 'tickettype', 'ticketnumber', 'step', 'tickettime' , 'status', 'locked')
    ordering = ['branch', '-tickettime',]


class TicketTempView(admin.ModelAdmin):

    # formfield_overrides = {
    #     models.DateTimeField: {'widget': forms.DateTimeInput(format='%Y-%m-%d %H:%M:%S.%f')},
    #     # models.DateTimeField(attrs={'supports_microseconds' : True} ),
    # }
    list_display =('branch', 'countertype', 'tickettype', 'ticketnumber', 'step', 'tickettime' , 'status', 'locked')
    ordering = ['branch', '-tickettime',]
      

class TicketRouteView(admin.ModelAdmin):
    list_display =('branch', 'tickettype', 'step', 'countertype' )
    ordering = ('branch', 'tickettype', 'step')


class TicketLogView(admin.ModelAdmin):
    list_display =('ticket', 'logtime','logtext', 'user' )
    ordering =('ticket', '-logtime')


class TicketDataView(admin.ModelAdmin):
    ordering = ('branch', 'countertype','ticket',   )
    list_display =('branch', 'countertype','ticket',   )



class APILogView(admin.ModelAdmin):
    model = APILog
    ordering = ('-logtime',)
    list_display =('logtime', 'ip', 'requeststr',  'app')

class SystemLogView(admin.ModelAdmin):
    model = SystemLog
    ordering = ('-logtime',)
    list_display =('logtime', 'logtext')       

class SettingsView(admin.ModelAdmin):
    model = Setting
    list_display =('name', 'branch', 'API_Log_Enabled' )

class CounterStatusView(admin.ModelAdmin):
    model = CounterStatus
    ordering = ('countertype', 'counternumber', )
    list_display =('countertype', 'counternumber', 'enabled', 'user', 'tickettemp',  )



class CounterLoginLogView(admin.ModelAdmin):

    model = CounterLoginLog
    ordering = ('countertype', 'counternumber')
    list_display =('countertype', 'counternumber', 'user', 'logintime', 'logouttime',  )

  
class PrinterStatusView(admin.ModelAdmin):

    model = PrinterStatus
    ordering = ('-updated', )
    list_display =('branch', 'printernumber', 'status', 'updated', )

class DispView(admin.ModelAdmin):

    model = DisplayAndVoice
    ordering = ('-displaytime', )
    list_display = ('branch', 'countertype', 'tickettemp', 'displaytime')

admin.site.register(testingModel, testingView)
admin.site.register(UserProfile, UserProfileView)
admin.site.register(TicketFormat, TicketFormatView)
admin.site.register(Branch, BranchProfileView)
admin.site.register(CounterType, CounterTypeView)
admin.site.register(Ticket, TicketView)
admin.site.register(TicketTemp, TicketTempView)
admin.site.register(TicketRoute, TicketRouteView)
admin.site.register(TicketLog, TicketLogView)
admin.site.register(TicketData, TicketDataView)
admin.site.register(APILog, APILogView)
admin.site.register(Setting, SettingsView)
admin.site.register(CounterStatus, CounterStatusView)
admin.site.register(CounterLoginLog, CounterLoginLogView)
admin.site.register(PrinterStatus, PrinterStatusView)
admin.site.register(DisplayAndVoice, DispView)
admin.site.register(SystemLog, SystemLogView)