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
                'ACW',
                'AUX',
                'ready',
                'login',
                'walking',               
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
    subscribe = models.BooleanField(default=False)
    substart = models.DateTimeField(default=datetime.datetime.strptime('2000-01-01 00:00:00', '%Y-%m-%d %H:%M:%S') )
    subend = models.DateTimeField(default=datetime.datetime.strptime('2000-01-01 00:00:00', '%Y-%m-%d %H:%M:%S') )
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
    queuemask =  models.CharField(default='A,B,C,D,E,F,G,H,I,J,K,L,M,N,O,P,Q,R,S,T,U,V,W,X,Y,Z,', max_length=200, null=False)
    websoftkey_show_waitinglist = models.BooleanField(default=True)

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
    # flash light
    flashlighttime = models.IntegerField(default=3)

    # voice settings
    voiceenabled  = models.BooleanField(default=True) 
    language1 = models.IntegerField(default=1)
    language2 = models.IntegerField(default=0)
    language3 = models.IntegerField(default=0)
    language4 = models.IntegerField(default=0)

    usersinglelogin = models.BooleanField(default=False)
    webtvcsslink = models.TextField(default='styles/styletv.css')
    webtvlogolink = models.TextField(default='images/logo_ts.png')

    # SMS settings
    SMSenabled = models.BooleanField(default=False)
    SMSmsg = models.TextField(max_length=70, null=True, blank=True)
    SMSQuota = models.IntegerField(default=500, help_text='Total no. of SMS per month', verbose_name="SMS Quota")
    SMSUsed = models.IntegerField(default=0, help_text='Total no. of SMS used', verbose_name="SMS used in month")
    SMSResetDay = models.IntegerField(default=1, help_text='SMS reset day of the month (1-28)', verbose_name="SMS Reset day")
    SMSResetLast = models.CharField(max_length=200, null=True, blank=True, help_text='Last reset date of SMS')

    # Booking settings
    bookingenabled = models.BooleanField(default=True)

    bookingPage1Text = models.TextField(null=True, 
                                            blank=True, 
                                            default= \
                                                    '多謝你預約我們的維修中心' + '\n' + \
                                                    '請帶發票在預約時間到維修中心' + '\n' + \
                                                    '地址: [[ADDR]]',
                                            help_text='Booking HTML page 1 text, [[ADDR]] is branch.address.')
    bookingPage1ScrollingText = models.TextField(null=True, blank=True, default='Scrolling text 1', help_text='Booking HTML page 1 Scrolling text, [[ADDR]] is branch address.')
    bookingPage2Text = models.TextField(null=True, 
                                            blank=True, 
                                            default= \
                                                    '請輸入 電郵 或 手機號碼(香港)' + '\n' + \
                                                    '我們發送確認信給你',
                                            help_text='Booking HTML page 2 text, [[ADDR]] is branch.address.')
    bookingPage2ScrollingText = models.TextField(null=True, blank=True, default='Scrolling text 2', help_text='Booking HTML page 2 Scrolling text, [[ADDR]] is branch.address.')
    bookingPage3Text = models.TextField(
                                            null=True,
                                            blank=True,
                                            default= \
                                                '你好 [[NAME]] :' + '\n' + '\n' + \
                                                '你的預約時間：' + '\n' + \
                                                '[[DATE]] [[WEEK]]' + '\n' + \
                                                '[[TIME]]' + '\n' + \
                                                '請帶發票在預約時間到維修中心' + '\n' + \
                                                '地址: [[ADDR]]' + '\n' + \
                                                '如需要更改時間/取消預約請盡早打電話給我們 12345678' + '\n' + \
                                                '' + '\n' + \
                                                '這個訊息會發送去你的電郵或者手機短訊。' + '\n' + \
                                                '' + '\n' + \
                                                'TSVD',
                                            help_text='Booking success text, [[ADDR]] is branch address, [[NAME]] is customer name, [[DATE]] is booking start date, [[TIME]] is booking start time. [[WEEK]] is week.',
                                            )
    # booking success email settings
    bookingSuccessEmailEnabled = models.BooleanField(default=True, verbose_name='Booking success email enabled')
    bookingSuccessEmailSubject = models.TextField(
                                                    null=True, 
                                                    blank=True, 
                                                    default= '你的預約已經確認 - TSVD',
                                                    help_text='Booking success email subject, [[ADDR]] is branch address, [[NAME]] is customer name, [[DATE]] is booking start date, [[TIME]] is booking start time. [[WEEK]] is week.'
                                                    )
    bookingSuccessEmailBody = models.TextField(
                                                null=True, 
                                                blank=True, 
                                                default= \
                                                            '你好 [[NAME]] :' + '\n' + '\n' + \
                                                            '你的預約時間：' + '\n' + \
                                                            '[[DATE]] [[WEEK]]' + '\n' + \
                                                            '[[TIME]]' + '\n' + \
                                                            '請帶發票在預約時間到維修中心' + '\n' + \
                                                            '地址: [[ADDR]]' + '\n' + \
                                                            '如需要更改時間/取消預約請盡早打電話給我們 12345678' + '\n' + \
                                                            '' + '\n' + \
                                                            'TSVD',
                                                help_text='Booking success email text, [[ADDR]] is branch address, [[NAME]] is customer name, [[DATE]] is booking start date, [[TIME]] is booking start time. [[WEEK]] is week.',
                                                )
    bookingSMSSuccessEnabled = models.BooleanField(default=True)
    bookingSMSSuccess = models.TextField(
                                        null=True,
                                        blank=True, 
                                        default= \
                                            '你的預約已經確認 - TSVD' + '\n' + \
                                            '預約時間：' + '\n' + \
                                            '[[DATE]]' + '\n' + \
                                            '[[TIME]]' + '\n' + \
                                            '如需要更改/取消預約請盡早致電 12345678' ,  
                                        verbose_name='Booking success SMS',
                                        help_text='SMS text body for booking success, [[DATE]] is booking start date, [[TIME]] is booking start time. 160 characters / 70 characters (Unicode) per one SMS',
                                        )
    # branch status
    updated = models.DateTimeField(auto_now=True)
    created = models.DateTimeField(auto_now_add=True) # auto_now_add just auto add once (the first created)


    # some time add a new field for foreign key, migrate will fail,
    # we need to add a default value
    # branch = models.ForeignKey(Branch, on_delete=models.CASCADE, default=Branch.get_default_pk)
    @classmethod
    def get_default_pk(cls):
        kb = cls.objects.get_or_create(
            bcode='KB'
        )
        return kb[0].pk


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
    
    tickettype = models.CharField(default='', max_length=200, null=True, blank=True, help_text='Ticket type',)
    queuepriority = models.CharField(
       max_length=32,
       choices=PRIORITY,
       default=BYBRANCH,
       null=False,
       help_text='Queue Priority',
    )
    branchs = models.ManyToManyField(Branch, related_name='branchs_u',  blank=True, help_text='Branch access rights',)
    staffnumber = models.CharField(max_length=200, null=True, blank=True, default='', help_text='Staff number',)    
    #enabled = models.BooleanField(default=True)  
    # room = models.ForeignKey(Room, on_delete=models.CASCADE)
    # body = models.TextField()
    mobilephone = models.CharField(max_length=20, null=True, blank=True, help_text='Mobile phone', )
    updated = models.DateTimeField(auto_now=True,)
    created = models.DateTimeField(auto_now_add=True) # auto_now_add just auto add once (the first created)


    class Meta:
        ordering = ['-updated', '-created']


class TicketFormat(models.Model):
    tformat_default = '''<CEN>
<LOGO>1
<TEXT>歡迎光臨，請稍候<LINE>
<TEXT>Welcome, please wait to be served<LINE>
<LINE>
<B_FONT>
<TEXT>票 號<LINE>
<TEXT>Ticket number<LINE>
<D_FONT><TICKET><LINE>
<N_FONT>
<DATETIME><LINE>
<QR>http://192.168.1.22:8000<MYTICKET><LINE>
<TEXT>掃描QR查看您的網上飛仔<LINE>
<TEXT>Scan QR code for your e-ticket<LINE>
<CUT>'''

    enabled = models.BooleanField(default=True) 
    ttype = models.CharField(max_length=10, null=False, blank=False) 
    branch = models.ForeignKey(Branch, on_delete=models.SET_NULL, blank=True, null=True)
    
    # description1 = models.TextField()
    # description2 = models.TextField()
    # description3 = models.TextField()
    tformat = models.TextField(null=False, blank=False, default=tformat_default) 
    ticketnext = models.IntegerField(default=1)  # only for Branch.ticketrepeatnumber is True
    touchkey_lang1 = models.CharField(max_length=100, null=True, blank=True, default='') 
    touchkey_lang2 = models.CharField(max_length=100, null=True, blank=True, default='') 
    touchkey_lang3 = models.CharField(max_length=100, null=True, blank=True, default='') 
    touchkey_lang4 = models.CharField(max_length=100, null=True, blank=True, default='') 
    
    
    updated = models.DateTimeField(auto_now=True)
    created = models.DateTimeField(auto_now_add=True) # auto_now_add just auto add once (the first created)
    # class Meta:
    #     ordering = ['branch', 'ttype']
    class Meta:
        unique_together = ('ttype', 'branch',)  
    def __str__(self):
        return self.branch.bcode + '-' + self.ttype


class CounterType(models.Model):
    enabled = models.BooleanField(default=True)
    branch = models.ForeignKey(Branch, on_delete=models.SET_NULL, blank=True, null=True)
    name = models.CharField(max_length=200, null=False)
    lang1 = models.CharField(max_length=200, null=True, blank=True, default='')
    lang2 = models.CharField(max_length=200, null=True, blank=True, default='')
    lang3 = models.CharField(max_length=200, null=True, blank=True, default='')    
    lang4 = models.CharField(max_length=200, null=True, blank=True, default='')    
    displayscrollingtext = models.TextField(null=True, blank=True, default='Testing 123...')
    countermode = models.CharField(max_length=200, null=False, blank=False, default='normal', verbose_name='Counter Mode', help_text='Normal mode=normal, Call Centre mode=cc, Restaurant mode=res') # normal, callcentre
    nextcounter = models.IntegerField(default=0)  # only for CallCentre mode system auto assign ticket to counter 
                                                  # this is NOT counter number, system will generate a list of counterstatus. 
                                                  # This number is the index of the list

    updated = models.DateTimeField(auto_now=True)
    created = models.DateTimeField(auto_now_add=True) # auto_now_add just auto add once (the first created)

    def __str__(self):
        return  self.branch.bcode + '-' + self.name
    class Meta:
        ordering = ['branch']
        unique_together = ('branch', 'name',)

class TicketRoute(models.Model):
    enabled = models.BooleanField(default=True) 
    branch = models.ForeignKey(Branch, on_delete=models.SET_NULL, blank=True, null=True)
    tickettype = models.CharField(max_length=200)
    step = models.IntegerField(default=1)
    countertype = models.ForeignKey(CounterType, on_delete=models.SET_NULL, blank=True, null=True)
    displasttickettype = models.CharField(max_length=200, default='-')
    displastticketnumber = models.CharField(max_length=200, default='-')
    displastcounter = models.CharField(max_length=200, default='-')
    waiting = models.IntegerField(default=0)
    def __str__(self):
        return self.branch.bcode + '-' + self.tickettype + '[' + str(self.step) + ']'
    class Meta:
        ordering = ['branch','tickettype', 'step']
        unique_together = ('branch', 'tickettype', 'step')
 
class Ticket(models.Model):
    tickettype = models.CharField(max_length=200)
    ticketnumber = models.CharField(max_length=200)
    branch = models.ForeignKey(Branch, on_delete=models.SET_NULL, blank=True, null=True)
    step = models.IntegerField(default=1)
    countertype = models.ForeignKey(CounterType, on_delete=models.SET_NULL, blank=True, null=True)
    ticketroute= models.ForeignKey(TicketRoute, on_delete=models.SET_NULL, blank=True, null=True)
    ticketformat= models.ForeignKey(TicketFormat, on_delete=models.SET_NULL, blank=True, null=True)
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

    createdby = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True, default=None, related_name='createdby')

    def __str__(self):
        return self.tickettype + self.ticketnumber

class TicketTemp(models.Model):
    tickettype = models.CharField(max_length=200)
    ticketnumber = models.CharField(max_length=200)
    branch = models.ForeignKey(Branch, on_delete=models.SET_NULL, blank=True, null=True)
    step = models.IntegerField(default=1)
    countertype = models.ForeignKey(CounterType, on_delete=models.SET_NULL, blank=True, null=True)
    ticketroute= models.ForeignKey(TicketRoute, on_delete=models.SET_NULL, blank=True, null=True)
    ticketformat= models.ForeignKey(TicketFormat, on_delete=models.SET_NULL, blank=True, null=True)
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

    securitycode = models.CharField(max_length=10, default='', blank=True, null=True)

    myticketlink = models.CharField(max_length=1000, default='', blank=True, null=True)
    
    createdby = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True, default=None, related_name='createdbytemp')
    
    ticket = models.ForeignKey(Ticket, on_delete=models.SET_NULL, blank=True, null=True)
    def __str__(self):
        return self.tickettype + self.ticketnumber
        


   
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
    # if name='global' is for all branchs
    name = models.CharField(max_length=200, unique=True, null=False)
    # if name='global' branch should be null
    branch = models.ForeignKey(Branch, on_delete=models.SET_NULL, blank=True, null=True)  
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
    flashid = models.IntegerField(null=True, blank=True, default=1)

class CounterLoginLog(models.Model) :
    countertype = models.ForeignKey(CounterType, on_delete=models.SET_NULL, blank=True, null=True) 
    counternumber = models.CharField(max_length=200, null=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True)
    logintime = models.DateTimeField(null=True, blank=True)
    logouttime = models.DateTimeField(null=True, blank=True)

class UserStatusLog(models.Model) :
    user = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True)
    status = models.TextField(default=lcounterstatus[0])
    starttime = models.DateTimeField(null=True, blank=True)
    endtime = models.DateTimeField(null=True, blank=True)
    ticket = models.ForeignKey(Ticket, on_delete=models.SET_NULL, blank=True, null=True)
    
    updated = models.DateTimeField(auto_now=True,)
    created = models.DateTimeField(auto_now_add=True) # auto_now_add just auto add once (the first created)
    
class PrinterStatus(models.Model):       
    branch = models.ForeignKey(Branch, on_delete=models.SET_NULL, blank=True, null=True)  # if name='global' branch should be null
    printernumber = models.TextField(null=True, blank=True)
    status = models.TextField(null=True, blank=True) # 1
    statustext = models.TextField(null=True, blank=True)
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
    flashtime = models.IntegerField(null=True, blank=True, default=3)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True)
    displaytime = models.DateTimeField(null=True, blank=True)     
    
    class Meta:
            ordering = ['displaytime']

class WebTouch(models.Model):
    name = models.CharField(max_length=200, null=True)
    branch = models.ForeignKey(Branch, on_delete=models.SET_NULL, blank=True, null=True)
    enabled = models.BooleanField(default=True)
    touchkey = models.ManyToManyField(TicketFormat)


    updated = models.DateTimeField(auto_now=True)
    created = models.DateTimeField(auto_now_add=True) # auto_now_add just auto add once (the first created)
    class Meta:
        unique_together = ('name', 'branch',)


class SubscribeOrder(models.Model):
    branch = models.ForeignKey(Branch, on_delete=models.SET_NULL, blank=True, null=True)
    days = models.IntegerField(blank=False, null=False)
    startdate = models.DateTimeField(blank=False, null=False)
    enddate = models.DateTimeField(blank=False, null=False)
    amount = models.FloatField()
    invoice = models.CharField(max_length=200, null=True)
    remark  = models.CharField(max_length=1000, null=True)

    createdby = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True)
    updated = models.DateTimeField(auto_now=True)
    created = models.DateTimeField(auto_now_add=True) # auto_now_add just auto add once (the first created)


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