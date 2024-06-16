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
    price = models.IntegerField(default=0)
class testingModel2(models.Model):
    total = models.IntegerField(default=0)

class Branch(models.Model):
    BYTIME = 'time'
    BYTICKETTIME = 'tickettime'
    BYUSER = 'user'
    BYMASK = 'mask'
    PRIORITY = [
       (BYTIME, ('Booking ticket first then by ticket time')),
       (BYTICKETTIME, ('By Ticket time')),
       (BYUSER, ('By User priority')),
       (BYMASK, ('By Mask priority')),
    ]

    # General settings
    bcode = models.CharField(max_length=200,unique=True, null=False, blank=False) # branch code
    enabled = models.BooleanField(default=True)
    queueenabled = models.BooleanField(default=True, verbose_name='Enabled Queuing System')
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
    #  volume range 0-100 (0 is mute)
    voice_volume = models.IntegerField(default=50, help_text='Volume range 0-100 (0 is mute)')
    language1 = models.IntegerField(default=1, help_text='English')
    O_Replace_Zero = models.BooleanField(default=True, help_text='Replace voice to [Oh] from [Zero]')
    language2 = models.IntegerField(default=0, help_text='Cantonese')
    language3 = models.IntegerField(default=0, help_text='Manadrin')
    language4 = models.IntegerField(default=0, help_text='Portuguese')
    before_enabled = models.BooleanField(default=False, help_text='Play effect sound Before calling ticket')
    before_sound = models.CharField(max_length=100, default='[SUCCESS]')
    after_enabled = models.BooleanField(default=False, help_text='Play effect sound After calling ticket')
    after_sound = models.CharField(max_length=100, default='[NOTIFY]')

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
    bookingenabled = models.BooleanField(default=True, verbose_name='Enabled Booking system')

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
    # Booking Success SMS settings
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
    # New booking email notification to admin settings
    bookingNewEmailEnabled = models.BooleanField(default=True, verbose_name='Enabled New Booking email notification')
    bookingNewEmailUser = models.ManyToManyField(User,  blank=True, 
                                                 verbose_name='New Booking email list',
                                                 )
    bookingNewEmailSubject = models.TextField(
                                                    null=True, 
                                                    blank=True, 
                                                    default= '你有新預約 - TSVD',
                                                    verbose_name='Email subject for New Booking',
                                                    help_text='[[ADDR]] is branch address, [[NAME]] is customer name, [[DATE]] is booking start date, [[TIME]] is booking start time, [[WEEK]] is week, [[PHONE]] is customer phone, [[EMAIL]] is customer email, [[BNAME]] is branch name, [[BCODE]] is branch code, [[USER]] is user first name.',
                                                    )
    bookingNewEmailBody = models.TextField(
                                                null=True, 
                                                blank=True, 
                                                default= \
                                                            '恭喜，你有新預約' + '\n' + '\n' + \
                                                            '客人名稱：[[NAME]]' + '\n' + \
                                                            '預約時間：' + '\n' + \
                                                            '[[DATE]] [[WEEK]]' + '\n' + \
                                                            '[[TIME]]' + '\n' + \
                                                            '地址: [[ADDR]]' + '\n' + \
                                                            '客人電話：[[PHONE]]' + '\n' + \
                                                            '客人電郵：[[EMAIL]]' + '\n' + \
                                                            '' + '\n' + \
                                                            'TSVD',
                                                verbose_name='Email body for New Booking',
                                                help_text='[[ADDR]] is branch address, [[NAME]] is customer name, [[DATE]] is booking start date, [[TIME]] is booking start time, [[WEEK]] is week, [[PHONE]] is customer phone, [[EMAIL]] is customer email, [[BNAME]] is branch name, [[BCODE]] is branch code, [[USER]] is user first name.',
                                                )    

    # Booking to queue settings
    bookingToQueueEnabled = models.BooleanField(default=True, verbose_name='Booking to Queue enabled')
    # printer number for booking to queue ticket
    bookingPrinterNumber = models.CharField(max_length=200, null=True, blank=True, default='P1', help_text='Printer number can be multiple printer, e.g. P1,P2,P3,... And BLANK is no print.')
    # booking ticket number digit, e.g. =3 means A001, B049 =2 means A01, B49
    bookingTicketDigit = models.IntegerField(default=3, verbose_name='Booking ticket digit (1 to 4 digits)', help_text='Ticket number digit, e.g. =3 means A001, B049 =2 means A01, B49')
    # booking ticket format 0=Ticket Type + Ticket Nubmber + Sub Ticket Type + sub Ticket number, 
    #                       1=Ticket Type + Sub Ticket Type + sub Ticket number, 
    #                       2=Sub Ticket Type + sub Ticket number, 
    bookingTicketFormat = models.IntegerField(default=0, verbose_name='Booking ticket format', help_text='0=Full format (e.g. B003A02), 1=Short1 (e.g. BA02), 2=Short2 (e.g. A02)')
    # Function for Booking was late / early force Booking to On time to Start Service or queue
    bookingForceOnTime = models.BooleanField(default=True, verbose_name='Booking force on time', help_text='If booking is late or early, force to on time to start service or queue')
    # On time range, e.g. =10 means late within 10 minutes of booking time is on time, booking_tickettype = 'A'
    bookingToQueueOnTimeRangeLate = models.IntegerField(default=10, verbose_name='Booking to Queue on time range late (1 to 15 minutes)')
    # On time range, e.g. =-15 means early within 15 minutes of booking time is on time, booking_tickettype = 'A'
    # Arrival time = Ticket Time (6:20) - Booking Time (06:30) = -10 minutes, so   10 (RangeLate) >= -10 >= -15 (RangeEarly)  => on time
    bookingToQueueOnTimeRangeEarly = models.IntegerField(default=15, verbose_name='Booking to Queue on time range early (1 to 30 minutes)')
    # Late unit, e.g. =5 means 10+1(11) to 10+5(15) minute late is going to booking_tickettype = 'B'
    # late 10+5+1(16) to 10+5+5(20) is going to booking_tickettype = 'C'  ...
    # Early case, e.g. early -15-1(-16) to -15-5(-20) is going to booking_tickettype = 'B'
    # Early case, e.g. early -15-5-1(-21) to -15-5-5(-25) is going to booking_tickettype = 'C'
    bookingToQueueLateUnit = models.IntegerField(default=5, verbose_name='Booking to Queue late unit (1 to 15 minutes)')
    bookingToQueueRatioNormal = models.IntegerField(default=3, verbose_name='Booking to Queue direction ratio [normal] (1 to 10)', help_text='Normal ratio for booking to queue, Default 3:1')
    bookingToQueueRatioRev = models.IntegerField(default=1, verbose_name='Booking to Queue direction ratio [Reverse] (1 to 10)', help_text='Reverse ratio for booking to queue, Default 3:1')

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
    BYTICKETTIME = 'tickettime'
    BYUSER = 'user'
    BYMASK = 'mask'
    PRIORITY = [
        (BYBRANCH, ('By Branch')),
        (BYTIME, ('Booking ticket first then by ticket time')),
        (BYTICKETTIME, ('By Ticket time')),
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
    
    enabled_queue = models.BooleanField(default=False, verbose_name='Queue enabled')
    enabled_crm = models.BooleanField(default=False, verbose_name='CRM enabled')
    enabled_booking = models.BooleanField(default=False, verbose_name='Booking enabled')

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
<QR><MYTICKET><LINE>
<TEXT>掃描QR查看您的網上飛仔<LINE>
<TEXT>Scan QR code for your e-ticket<LINE>
<CUT>'''

    enabled = models.BooleanField(default=True) 
    ttype = models.CharField(max_length=10, null=False, blank=False)
    for_booking = models.BooleanField(default=False)
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

class SubTicket(models.Model):
    branch = models.ForeignKey(Branch, on_delete=models.SET_NULL, blank=True, null=True)
    booking_tickettype = models.CharField(max_length=20)
    ticketnext = models.IntegerField(default=1)
    
    def __str__(self):
        return self.branch.bcode + '-' + self.booking_tickettype
    class Meta:
        ordering = ['branch','booking_tickettype']
        unique_together = ('branch', 'booking_tickettype')


class CounterType(models.Model):
    enabled = models.BooleanField(default=True)
    branch = models.ForeignKey(Branch, on_delete=models.SET_NULL, blank=True, null=True)
    name = models.CharField(max_length=200, null=False)
    lang1 = models.CharField(max_length=200, null=True, blank=True, default='')
    lang2 = models.CharField(max_length=200, null=True, blank=True, default='')
    lang3 = models.CharField(max_length=200, null=True, blank=True, default='')    
    lang4 = models.CharField(max_length=200, null=True, blank=True, default='')    
    displayscrollingtext = models.TextField(null=True, blank=True, default='Testing 123...')
    vert_showcounter = models.BooleanField(default=True)
    vert_showlatest = models.BooleanField(default=True)
    vert_latestpagehold = models.IntegerField(default=10)
    showcounter = models.BooleanField(default=True)
    showlatest = models.BooleanField(default=True)
    latestpagehold = models.IntegerField(default=6)
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
    
    # for display ticket type and ticket number, it is combined with booking_tickettype and booking_ticketnumber
    tickettype_disp = models.CharField(max_length=200)
    ticketnumber_disp = models.CharField(max_length=200)

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

    booking_tickettype = models.CharField(max_length=200, null=True, blank=True, default='')
    booking_ticketnumber = models.CharField(max_length=200, null=True, blank=True, default='')
    booking_time = models.DateTimeField(null=True, blank=True, default=None)
    # arrival time is ticket time
    # booking_arrival = models.DateTimeField(null=True, blank=True) 
    booking_name = models.CharField(max_length=200, null=True, blank=True, default='')
    booking_user = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True, default=None, related_name='booking_user')
    booking_id = models.IntegerField(null=True, blank=True, default=None)

    def __str__(self):
        return self.tickettype + self.ticketnumber

class TicketTemp(models.Model):
    tickettype = models.CharField(max_length=200)
    ticketnumber = models.CharField(max_length=200)

    # for display ticket type and ticket number, it is combined with booking_tickettype and booking_ticketnumber
    tickettype_disp = models.CharField(max_length=200)
    ticketnumber_disp = models.CharField(max_length=200)

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
    
    booking_tickettype = models.CharField(max_length=200, null=True, blank=True, default='')
    booking_ticketnumber = models.CharField(max_length=200, null=True, blank=True, default='')
    booking_time = models.DateTimeField(null=True, blank=True, default=None)
    # arrival time is ticket time
    # booking_arrival = models.DateTimeField(null=True, blank=True) 
    booking_name = models.CharField(max_length=200, null=True, blank=True, default='')
    booking_user = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True, default=None, related_name='booking_user_temp')
    booking_id = models.IntegerField(null=True, blank=True, default=None)

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
    voice = models.CharField(max_length=50, null=True, blank=True, default='[SC]', help_text='[SC] = Service Counter, [C1] = Counter one, [CASHIER] = Cashier, Blank = No voice')
    enabled = models.BooleanField(default=True) 
    status = models.TextField(default=lcounterstatus[0])
    tickettemp = models.ForeignKey(TicketTemp, on_delete=models.SET_NULL, blank=True, null=True)
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


class Device(models.Model):
    VOICECOMP = 'VC'
    DISPPANEL = 'D'
    PRINTERCONTROL = 'PRT'
    DEVICETYPE = [
       (VOICECOMP, ('Voice Component')),
       (DISPPANEL, ('Display Panel')),
       (PRINTERCONTROL, ('Printer Control')),
    ]


    device_id_end = models.CharField(max_length=200, null=False) # device ID end created by the device
    device_id_given = models.CharField(max_length=200, null=False) # device ID given by the server
    # device type : VoiceComp, Display, PrinterControl ...
    device_type = models.CharField(
       max_length=32,
       choices=DEVICETYPE,
       null=False,
    )
    device_ip = models.CharField(max_length=20, null=True, blank=True)
    device_ip_int = models.CharField(max_length=20, null=True, blank=True)
    version = models.CharField(max_length=20, null=True, blank=True)
    branch = models.ForeignKey(Branch, on_delete=models.SET_NULL, blank=True, null=True)
    countertype = models.ForeignKey(CounterType, on_delete=models.SET_NULL, blank=True, null=True)
    lastactive = models.DateTimeField(null=True, blank=True, default=None) # last active time
    settings = models.TextField(null=True, blank=True, default='') # settings for the device

    updated = models.DateTimeField(auto_now=True)
    created = models.DateTimeField(auto_now_add=True) # auto_now_add just auto add once (the first created)

    class Meta:
        unique_together = ('device_id_end', 'device_id_given',)

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