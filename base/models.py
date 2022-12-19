import datetime
from django.db import models
from django.contrib.auth.models import User


# Create your models here.

lcounterstatus = [
                'waiting',
                'calling',
                'processing',
                'done',
                'miss',
                'void',
                ]

class testingModel(models.Model):
    name = models.TextField(null=True, blank=True)
    des = models.TextField(null=True, blank=True)



class Branch(models.Model):
    BYTIME = 'time'
    BYUSER = 'user'
    BYMASK = 'mask'
    PRIORITY = [
       (BYTIME, ('By Ticket time')),
       (BYUSER, ('By User priority')),
       (BYMASK, ('By Mask priority')),
    ]

    # General settings
    bcode = models.CharField(max_length=200,unique=True, null=False, blank=False) # branch code
    enabled = models.BooleanField(default=True)    
    name = models.TextField() 
    address = models.TextField(null=True, blank=True) 
    gps = models.TextField(null=True, blank=True) 
    timezone = models.CharField(max_length=32, null=False, default='Asia/Hong_Kong')
    officehourstart = models.TimeField(default=datetime.time(9, 0, 0))
    officehourend = models.TimeField(default=datetime.time(18, 0, 0))
    queuepriority = models.CharField(
       max_length=32,
       choices=PRIORITY,
       default=BYTIME,
       null=False,
    )
    queuemask =  models.CharField(default='ABCDEFGHIJKLMNOPQRSTUVWXYZ', max_length=200, null=False)

    # ticket settings
    tickettimestart = models.TimeField(default=datetime.time(8, 0, 0))
    tickettimeend = models.TimeField(default=datetime.time(17, 0, 0))
    ticketmax = models.IntegerField(default=999) 
    ticketnext = models.IntegerField(default=1) # only for ticketrepeatnumber is True
    ticketnoformat = models.TextField(default='000')  # if '000' means: A001, B049
    ticketrepeatnumber = models.BooleanField(default=True)  # if False: A001 -> B002 -> A003

    # display settings
    displayenabled  = models.BooleanField(default=True) 
    displayflashtime = models.IntegerField(default=3)

    # voice settings
    voiceenabled  = models.BooleanField(default=True) 
    language1 = models.IntegerField(default=1)
    language2 = models.IntegerField(default=0)
    language3 = models.IntegerField(default=0)
    language4 = models.IntegerField(default=0)

    usersinglelogin = models.BooleanField(default=False)    

    # branch status
    updated = models.DateTimeField(auto_now=True)
    created = models.DateTimeField(auto_now_add=True) # auto_now_add just auto add once (the first created)
    def __str__(self):
        return self.bcode
 
class UserProfile(models.Model):  
    BYBRANCH = 'branch'    
    BYTIME = 'time'
    BYUSER = 'user'
    BYMASK = 'mask'
    PRIORITY = [
        (BYBRANCH, ('By Branch')),
        (BYTIME, ('By Ticket time')),
        (BYUSER, ('By User priority')),
        (BYMASK, ('By Branch mask priority')),
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE,unique=True)
    
    tickettype = models.CharField(default='ABCDEFGHIJKLMNOPQRSTUVWXYZ', max_length=200, null=True, blank=True, )
    queuepriority = models.CharField(
       max_length=32,
       choices=PRIORITY,
       default=BYBRANCH,
       null=False,
    )
    branchs = models.ManyToManyField(Branch, related_name='branchs_u',  blank=True)
    staffnumber = models.CharField(max_length=200, null=True, blank=True, default='')    
    #enabled = models.BooleanField(default=True)  
    # room = models.ForeignKey(Room, on_delete=models.CASCADE)
    # body = models.TextField()
    updated = models.DateTimeField(auto_now=True)
    created = models.DateTimeField(auto_now_add=True) # auto_now_add just auto add once (the first created)


    class Meta:
        ordering = ['-updated', '-created']


class TicketFormat(models.Model):
    tformat_default = '''<CEN>
<LOGO>
<TEXT>歡迎光臨，請稍候<LINE>
<TEXT>Welcome, please wait to be served<LINE>
<LINE>
<B_FONT>
<TEXT>票 號<LINE>
<TEXT>Ticket number<LINE>
<D_FONT><TICKET><LINE>
<N_FONT>
<DATETIME>
<CUT>'''

    enabled = models.BooleanField(default=True) 
    ttype = models.CharField(max_length=10, null=False, blank=False) 
    branch = models.ForeignKey(Branch, on_delete=models.SET_NULL, blank=True, null=True)
    
    # description1 = models.TextField()
    # description2 = models.TextField()
    # description3 = models.TextField()
    tformat = models.TextField(null=False, blank=False, default=tformat_default) 
    ticketnext = models.IntegerField(default=1)  # only for Branch.ticketrepeatnumber is True

    
    updated = models.DateTimeField(auto_now=True)
    created = models.DateTimeField(auto_now_add=True) # auto_now_add just auto add once (the first created)
    # class Meta:
    #     ordering = ['branch', 'ttype']
    class Meta:
        unique_together = ('ttype', 'branch',)  


class CounterType(models.Model):
    enabled = models.BooleanField(default=True)
    branch = models.ForeignKey(Branch, on_delete=models.SET_NULL, blank=True, null=True)
    name = models.CharField(max_length=200, null=False)    
    displayscrollingtext = models.TextField(null=False, blank=False, default='Testing 123...') 

    updated = models.DateTimeField(auto_now=True)
    created = models.DateTimeField(auto_now_add=True) # auto_now_add just auto add once (the first created)

    def __str__(self):
        return  self.branch.bcode + '-' + self.name
    class Meta:
        ordering = ['branch']
        unique_together = ('branch', 'name',)

class Ticket(models.Model):
    tickettype = models.CharField(max_length=200)
    ticketnumber = models.CharField(max_length=200)
    branch = models.ForeignKey(Branch, on_delete=models.SET_NULL, blank=True, null=True)
    step = models.IntegerField(default=1)
    countertype = models.ForeignKey(CounterType, on_delete=models.SET_NULL, blank=True, null=True)
    status = models.TextField(default=lcounterstatus[0])
    locked = models.BooleanField(default=False)

    tickettime = models.DateTimeField()
    # calltime = models.DateTimeField()
    # walktime = models.DateTimeField()
    # donetime = models.DateTimeField()

    tickettext = models.TextField(default='', blank=True, null=True)
    printernumber = models.TextField(default='', blank=True, null=True)  # format printer 1 and 2 print: <NO>1</NO><NO>2</NO> 
    printedtimes = models.IntegerField(default=0)

    user = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True)

    remark = models.TextField(default='', blank=True, null=True)
    def __str__(self):
        return self.tickettype + self.ticketnumber

class TicketTemp(models.Model):
    tickettype = models.CharField(max_length=200)
    ticketnumber = models.CharField(max_length=200)
    branch = models.ForeignKey(Branch, on_delete=models.SET_NULL, blank=True, null=True)
    step = models.IntegerField(default=1)
    countertype = models.ForeignKey(CounterType, on_delete=models.SET_NULL, blank=True, null=True)
    status = models.TextField(default=lcounterstatus[0])
    locked = models.BooleanField(default=False)

    tickettime = models.DateTimeField()
    # calltime = models.DateTimeField()
    # walktime = models.DateTimeField()
    # donetime = models.DateTimeField()

    tickettext = models.TextField(default='', blank=True, null=True)
    printernumber = models.TextField(default='', blank=True, null=True)  # format printer 1 and 2 print: <NO>1</NO><NO>2</NO> 
    printedtimes = models.IntegerField(default=0)

    user = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True)

    remark = models.TextField(default='', blank=True, null=True)

    ticket = models.ForeignKey(Ticket, on_delete=models.SET_NULL, blank=True, null=True)
    def __str__(self):
        return self.tickettype + self.ticketnumber
        


class TicketRoute(models.Model):
    enabled = models.BooleanField(default=True) 
    branch = models.ForeignKey(Branch, on_delete=models.SET_NULL, blank=True, null=True)
    tickettype = models.CharField(max_length=200)
    step = models.IntegerField(default=1)
    countertype = models.ForeignKey(CounterType, on_delete=models.SET_NULL, blank=True, null=True)
    displasttickettype = models.CharField(max_length=200, default=' ')
    displastticketnumber = models.CharField(max_length=200, default=' ')
    displastcounter = models.CharField(max_length=200, default=' ')
    waiting = models.IntegerField(default=0)
    
class TicketLog(models.Model):
    ticket = models.ForeignKey(Ticket, on_delete=models.SET_NULL, blank=True, null=True)
    tickettemp = models.ForeignKey(TicketTemp, on_delete=models.SET_NULL, blank=True, null=True)
    # tickettype = models.CharField(max_length=200)
    # ticketnumber = models.CharField(max_length=200)
    # branch = models.ForeignKey(Branch, on_delete=models.SET_NULL, blank=True, null=True)
    # tickettime = models.DateTimeField(null=True)

    # countertype = models.ForeignKey(CounterType, on_delete=models.SET_NULL, null=True)
    app = models.TextField(null=True, blank=True)
    version = models.TextField(null=True, blank=True)
    logtime = models.DateTimeField()
    logtext = models.TextField(null=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True)

class APILog(models.Model):
    logtime = models.DateTimeField(null=True, blank=True)
    requeststr = models.TextField(null=True, blank=True)
    ip = models.TextField(null=True, blank=True)
    app = models.TextField(null=True, blank=True)
    version = models.TextField(null=True, blank=True)
    logtext = models.TextField(null=True, blank=True)


class SystemLog(models.Model):
    logtime = models.DateTimeField(null=True, blank=True)
    logtext = models.TextField(null=True, blank=True)
    
class TicketData(models.Model):
    ticket = models.ForeignKey(Ticket, on_delete=models.SET_NULL, blank=True, null=True)
    tickettemp = models.ForeignKey(TicketTemp, on_delete=models.SET_NULL, blank=True, null=True)

    branch = models.ForeignKey(Branch, on_delete=models.SET_NULL, blank=True, null=True)
    countertype = models.ForeignKey(CounterType, on_delete=models.SET_NULL, blank=True, null=True)
    step = models.IntegerField(default=1)

    starttime = models.DateTimeField(null=True, blank=True)
    startuser = models.ForeignKey(User, related_name='startuser', on_delete=models.SET_NULL, blank=True, null=True)
    calltime =  models.DateTimeField(null=True, blank=True)
    calluser = models.ForeignKey(User, related_name='calluser', on_delete=models.SET_NULL, blank=True, null=True)
    processtime = models.DateTimeField(null=True, blank=True)
    processuser = models.ForeignKey(User, related_name='processuser', on_delete=models.SET_NULL, blank=True, null=True)
    donetime = models.DateTimeField(null=True, blank=True)
    doneuser = models.ForeignKey(User, related_name='doneuser', on_delete=models.SET_NULL, blank=True, null=True)
    misstime = models.DateTimeField(null=True, blank=True)
    missuser = models.ForeignKey(User, related_name='missuser', on_delete=models.SET_NULL, blank=True, null=True)
    voidtime = models.DateTimeField(null=True, blank=True)
    voiduser = models.ForeignKey(User, related_name='voiduser', on_delete=models.SET_NULL, blank=True, null=True)

    waitingperiod = models.IntegerField(null=True, blank=True) # calltime - starttime / misstime - starttime
    walkingperiod = models.IntegerField(null=True, blank=True)
    processingperiod = models.IntegerField(null=True, blank=True)

    totalperiod = models.IntegerField(null=True, blank=True)

class Setting(models.Model):
    name = models.CharField(max_length=200, unique=True, null=False) # if name='global' is for all branchs
    branch = models.ForeignKey(Branch, on_delete=models.SET_NULL, blank=True, null=True)  # if name='global' branch should be null
    API_Log_Enabled = models.BooleanField(default=True) 


class CounterStatus(models.Model):
    countertype = models.ForeignKey(CounterType, on_delete=models.SET_NULL, blank=True, null=True) 
    counternumber = models.CharField(max_length=200, null=True)
    enabled = models.BooleanField(default=True) 
    tickettemp = models.ForeignKey(TicketTemp, on_delete=models.SET_NULL, blank=True, null=True)
    status = models.TextField(default=lcounterstatus[0])
    user = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True)
    loged = models.BooleanField(default=False)
    logintime = models.DateTimeField(null=True, blank=True)
    lastactive = models.DateTimeField(null=True, blank=True)

class CounterLoginLog(models.Model) :
    countertype = models.ForeignKey(CounterType, on_delete=models.SET_NULL, blank=True, null=True) 
    counternumber = models.CharField(max_length=200, null=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True)
    logintime = models.DateTimeField(null=True, blank=True)
    logouttime = models.DateTimeField(null=True, blank=True)

class PrinterStatus(models.Model):       
    branch = models.ForeignKey(Branch, on_delete=models.SET_NULL, blank=True, null=True)  # if name='global' branch should be null
    printernumber = models.TextField(null=True, blank=True)
    status = models.TextField(null=True, blank=True)    
    updated = models.DateTimeField(auto_now=True)
    created = models.DateTimeField(auto_now_add=True) # auto_now_add just auto add once (the first created)

    class Meta:
        unique_together = ('branch', 'printernumber',)
        ordering = ['-updated', '-created']
                

class DisplayAndVoice(models.Model):
    branch = models.ForeignKey(Branch, on_delete=models.SET_NULL, blank=True, null=True)
    countertype = models.ForeignKey(CounterType, on_delete=models.SET_NULL, blank=True, null=True) 
    counternumber = models.CharField(max_length=200, null=True)
    tickettemp = models.ForeignKey(TicketTemp, on_delete=models.SET_NULL, blank=True, null=True)    
    wait = models.CharField(max_length=200, null=True) 
    flashtime = models.CharField(max_length=200, null=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True)
    displaytime = models.DateTimeField(null=True, blank=True)     
    
    class Meta:
            ordering = ['displaytime']


# class Room(models.Model):
#     host =models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
#     topic =  models.ForeignKey(Topic, on_delete=models.SET_NULL, null=True)
#     name = models.CharField(max_length=200)
#     description = models.TextField(null=True, blank=True)
#     participants = models.ManyToManyField(User, related_name='participants', blank=True)
#     updated = models.DateTimeField(auto_now=True)
#     created = models.DateTimeField(auto_now_add=True) # auto_now_add just auto add once (the first created)

#     class Meta:
#         ordering = ['-updated', '-created']
#     def __str__(self):
#         return self.name        