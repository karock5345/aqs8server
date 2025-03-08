# from django.contrib.auth.models import User
from django.db.models import Q
from .views import counteractive
from .v_display import newdisplayvoice
from base.models import CounterStatus, CounterType, TicketTemp, TicketRoute, TicketData, TicketLog, CounterLoginLog, UserProfile, lcounterstatus, UserStatusLog
# from base.models import testingModel
from base.ws import *
import logging
from django.db import transaction
import time
# from base.api.serializers import waitinglistSerivalizer
from booking.models import Booking, TimeSlot
from celery import shared_task


logger = logging.getLogger(__name__)
softkey_version = '8.4.0.0'

QueueDirection = {}

# if call = False, just get the next ticket for update the softkey
def funCallTicketwithDirection(branch:Branch, call:bool, user, counterstatus:CounterStatus, l_mask:list):
    global QueueDirection

    ticket = None
    
    # check the waiting queue have any ticket from booking?

    # booking ticket normal direction
    ticketlist_b = TicketTemp.objects.filter(~Q(booking_id=None) & (Q(booking_user=user) | Q(booking_user=None)) & Q(branch=branch) & Q(countertype=counterstatus.countertype) & Q(status=lcounterstatus[0]) 
                                             & Q(locked=False)).order_by('booking_tickettype', 'tickettime')

    # non-booking ticket
    ticketlist = TicketTemp.objects.filter(Q(booking_id=None) & Q(branch=branch) & Q(countertype=counterstatus.countertype) & Q(status=lcounterstatus[0]) & Q(locked=False)).order_by('tickettime')

    # get the direct from QueueDirection
    direction = None
    try:
        direction = QueueDirection[branch.bcode]
    except:
        pass
    if direction == None:
        direction = 1
        QueueDirection = QueueDirection | {branch.bcode: direction}

    # print('QueueDirection:', QueueDirection)
    # print('Direction:', direction)
    # get the booking ticket first
    if ticketlist_b.count() > 0:
        if direction <= branch.bookingToQueueRatioNormal:
            # Direction is normal
            for t in ticketlist_b:
                if t.tickettype in l_mask:
                    # call this ticket
                    ticket = t
                    break
            pass
        else:
            # Direction is reverse
            ticketlist_b = TicketTemp.objects.filter(~Q(booking_id=None) & (Q(booking_user=user) | Q(booking_user=None)) & Q(branch=branch) & Q(countertype=counterstatus.countertype) & Q(status=lcounterstatus[0]) 
                                                    & Q(locked=False)).order_by('-booking_tickettype', 'tickettime')
            for t in ticketlist_b:
                if t.tickettype in l_mask:
                    # check the late ticket waiting time
                    booking = Booking.objects.get(id=t.booking_id)
                    late_min = booking.late_min
                    # print('late_min:', late_min)
                    waiting_min = int((datetime.now(timezone.utc) - t.tickettime).total_seconds() / 60)
                    # print('waiting_min:', waiting_min)

                    offset = waiting_min - late_min
                    if late_min < 0:
                        offset = waiting_min + late_min
                    if offset >= 0:
                        # call this ticket
                        ticket = t
                        break
            pass
        
        if call == True and ticket != None:
            # next direction index
            direction += 1
            if direction > branch.bookingToQueueRatioNormal + branch.bookingToQueueRatioRev:
                direction = 1
            QueueDirection = QueueDirection | {branch.bcode: direction}
    if ticket == None:
        # get the non-booking ticket
        # found the waiting ticket by time
        for t in ticketlist:
            if t.tickettype in l_mask:
                # call this ticket
                ticket = t
                break
    return ticket

# version 8.4.0 Prevent WS data lost. Send data to "Display Ticket" "Voice" "Print Ticket" repact 3 times
# version 8.3.0 add transaction select_for_update for prevent 'double bookings' problem
@transaction.atomic
def funCounterCall_v840(user, branch:Branch, countertype, counterstatus, logtext, rx_app, rx_version, datetime_now):
    status = dict({})
    msg = dict({})
    context = dict({})

    # check call priority
    # if priority = 'time' / 'umask' user mask / 'bmask' branch mask
    priority = ''
    mask = ''
    if status == dict({}) :
        userp = None
        obj_userp = UserProfile.objects.filter(user__exact=user)
        if obj_userp.count() == 1 :
            userp = obj_userp[0]            
        if userp == None:
            status = dict({'status': 'Error'})
            msg =  dict({'msg':'User profile not found'})  
    if status == dict({}) :
        qp = userp.queuepriority
        if qp == 'time':
            mask = userp.tickettype
            priority = 'time'
        elif qp == 'tickettime':
            mask = userp.tickettype
            priority = 'tickettime'            
        elif qp == 'user':            
            mask = userp.tickettype
            priority = 'umask'
        elif qp == 'mask':
            # branch mask               
            mask = branch.queuemask
            priority = 'bmask'
        elif qp == 'branch':
            qp = branch.queuepriority
            if qp == 'time':
                priority = 'time'
                mask = userp.tickettype
            elif qp == 'tickettime':
                priority = 'tickettime'
                mask = userp.tickettype                
            elif qp == 'mask':
                priority = 'bmask'
                mask = branch.queuemask 
            elif qp == 'user':
                priority = 'umask'
                mask = userp.tickettype
        if mask == None :
            mask = ''
        if mask == '' :
            status = dict({'status': 'Error'})
            msg =  dict({'msg':'User no ticket type selected'})
        if priority == '' :
            status = dict({'status': 'Error'})
            msg =  dict({'msg':'Queue priority not found qp->[' + qp + '] priority->[' + priority +']'})
        if mask != '' and priority == 'bmask' :
            l_mask = mask.split(',')
            new_mask=''
            l_new_mask = []
            mask_b = mask
            # remove all space in mask_b
            mask_b = mask_b.replace(' ', '')
            u_tt = userp.tickettype
            u_tt = u_tt.replace(' ', '')
            l_mask_b = mask_b.split(',')
            l_u_tt = u_tt.split(',')

            # check user ticket type in branch mask
            for tt in l_mask_b:
                if tt in l_u_tt:
                    new_mask = new_mask + tt + ','
                    l_new_mask.append(tt)

           
            mask = new_mask
            l_mask = l_new_mask
        if priority == 'bmask' or priority == 'umask' :
            priority = 'mask'
    if status == dict({}) :
        # get the Counter type
        ctypeobj = CounterType.objects.filter( Q(branch=branch) & Q(name=countertype.name) )
        if not(ctypeobj.count() > 0) :
            status = dict({'status': 'Error'})
            msg =  dict({'msg':'Counter Type not found'})  
    if status == dict({}) :
        countertype = ctypeobj[0]
        cstatusobj = CounterStatus.objects.filter( Q(countertype=countertype) & Q(counternumber=counterstatus.counternumber) & Q(user=user))
        if not(cstatusobj.count() > 0) :
            status = dict({'status': 'Error'})
            msg =  dict({'msg':'Counter not found / User did not login'})  
    if status == dict({}) :
        counterstatus = cstatusobj[0]
        counterstatus.lastactive = datetime_now
        counterstatus.save()

        # check counter status
        if not(counterstatus.status == 'waiting' or counterstatus.status == 'ready') :
            status = dict({'status': 'Error'})
            msg =  dict({'msg':'Counter status is not WAITING/READY'})  
        elif counterstatus.tickettemp != None :
            status = dict({'status': 'Error'})
            msg =  dict({'msg':'Counter still processing ticket:' + counterstatus.tickettemp.tickettype + counterstatus.tickettemp.ticketnumber})  


    # Get the ticket from queue
    if status == dict({}) :
        mask = mask.replace(' ', '')
        l_mask = mask.split(',')
        ticket = None

        if priority == 'time':
            # priority = 'time' , call booking ticket first
            ticket = funCallTicketwithDirection(branch, True, user, counterstatus, l_mask)

            # testing
            # print ('Calling ticket:', ticket.tickettype + ticket.ticketnumber)
            # ticket = None
            if ticket != None:
                context = {'priority': priority, 'mask': mask, 'tickettype': ticket.tickettype, 'ticketnumber': ticket.ticketnumber , 'tickettime': ticket.tickettime}
        elif priority == 'tickettime':
            # found the waiting ticket by time
            ticketlist = TicketTemp.objects.filter(Q(branch=branch) & Q(countertype=countertype) & Q(status=lcounterstatus[0]) & Q(locked=False)).order_by('tickettime')            
            for ticket in ticketlist:
                tt =  ticket.tickettype 
                if ticket.tickettype in l_mask:
                    # call this ticket
                    context = {'priority': priority, 'mask': mask, 'tickettype': ticket.tickettype, 'ticketnumber': ticket.ticketnumber , 'tickettime': ticket.tickettime}
                    break
        elif priority == 'mask':
            ticketlist = TicketTemp.objects.filter( Q(branch=branch) & Q(countertype=countertype) & Q(status=lcounterstatus[0]) & Q(locked=False)).order_by('tickettime')

            for tt in l_mask:
                for ticket in ticketlist:
                    if tt == ticket.tickettype:
                        # call this ticket
                        context = {'priority': priority, 'mask': mask, 'tickettype': ticket.tickettype, 'ticketnumber': ticket.ticketnumber , 'tickettime': ticket.tickettime}
                        break
                if context != dict({}):
                    break
        
        if context != dict({}) and ticket != None :
            try:
                # lock the ticket
                ticket = TicketTemp.objects.select_for_update(nowait=True).get(id=ticket.id)
                # for testing
                # time.sleep(3)
            except Exception as e:
                from base.a_global import str_db_locked
                status = dict({'status': 'Error'})
                msg =  dict({'msg':str_db_locked})
    if status == dict({}) :
        if ticket == None:
            # no ticket to call
            status = dict({'status': 'OK'})
            context = dict({'data':{}})
    if status == dict({}) :
        # update ticketdata db
        td = None
        obj_td = TicketData.objects.filter(
            tickettemp=ticket,
            countertype=countertype,
            step=ticket.step,
            branch=branch,
        )
        if obj_td.count() == 1 :
            td = obj_td[0]
        else:
            status = dict({'status': 'Error'})
            msg =  dict({'msg':'TicketData is multi ' })  
        if td == None :
            status = dict({'status': 'Error'})
            msg =  dict({'msg':'TicketData not found ' }) 

    if status == dict({}) :
        td.calltime = datetime_now
        td.calluser = user
        time_diff = datetime_now - td.starttime
        tsecs = int(time_diff.total_seconds())
        td.waitingperiod = tsecs
        td.save()

        # update counterstatus db 
        counterstatus.tickettemp = ticket
        counterstatus.status = lcounterstatus[1]
        counterstatus.save()

        # update ticket 
        ticket.user = user
        ticket.status = lcounterstatus[1]
        ticket.ticketroute.waiting = ticket.ticketroute.waiting - 1
        ticket.ticketroute.save()
        ticket.save()

        # add ticketlog
        localdate_now = funUTCtoLocal(datetime_now, branch.timezone)
        TicketLog.objects.create(
            tickettemp=ticket,
            logtime=datetime_now,
            app = rx_app,
            version = rx_version,
            logtext= logtext + branch.bcode + '_' + ticket.tickettype + '_'+ ticket.ticketnumber + '_' + localdate_now.strftime('%Y-%m-%d_%H:%M:%S') ,
            user=user,
        )

        # do display and voice temp db
        newdisplayvoice(branch, countertype, counterstatus.counternumber, ticket, datetime_now, user)

    # # WS send data :
    #     # websocket to web tv
    #     wssendwebtv(branch, countertype)
    #     # websocket to Display Panel display ticket
    #     wssenddispcall840(branch,counterstatus, countertype, ticket)
    #     # websocket to softkey (update Queue List)
    #     wssendql(branch, countertype, ticket, 'del')
    #     # websocket to web my ticket
    #     wsSendTicketStatus(branch, ticket, counterstatus)        
    #     # websocket to voice com and flash light
    #     wssendvoice840(branch, countertype, counterstatus, ticket, 'asdf1234')
    #     wssendflashlight(branch, countertype, counterstatus, 'flash')
    #     # websocket to web softkey for update counter status
    #     wscounterstatus(counterstatus)

        redis_online = check_redis_connection()
        # pass the sub to celery parallel run
        if redis_online:
            try:
                t_ws_call = t_WS_Call.apply_async (args=[branch.id, counterstatus.id, countertype.id, ticket.id, True], countdown=0)
                logging.info('Start task : t_ws_call (wssendwebtv, wssenddispcall_v840, wssendql, wssendvoice_v840, wssendflashlight, wscounterstatus) : ' + str(t_ws_call))
            except Exception as e:
                logging.error('Error t_ws_call : ' + str(e))
                pass
        else:
            logging.error('Redis is offline. Cannot run t_ws_call')

        context = dict({'data':context})
        status = dict({'status': 'OK'})

    return status, msg, context

@shared_task
def t_WS_Call(branch_id, counterstatus_id, countertype_id, ticket_id, delsl:bool):
    from celery import current_task

    branch = Branch.objects.get(id=branch_id)
    counterstatus = CounterStatus.objects.get(id=counterstatus_id)
    countertype = CounterType.objects.get(id=countertype_id)
    ticket = TicketTemp.objects.get(id=ticket_id)

    # Get my task ID
    my_id = current_task.request.id
    logger.info(f'Call/Get WS data out (wssendwebtv, wssenddispcall_v840, wssendql, wssendvoice_v840, wssendflashlight, wscounterstatus): {my_id}')

    current_task.status = 'PROGRESS'

    # websocket to web tv
    try:
        wssendwebtv(branch, countertype)
    except Exception as e:
        current_task.status = 'ERROR'
        return current_task.status

    # websocket to Display Panel display ticket
    try:
        wssenddispcall_v840(branch, counterstatus, countertype, ticket)
    except Exception as e:
        current_task.status = 'ERROR'
        return current_task.status

    # websocket to softkey (update Queue List)
    if delsl:
        try:
            wssendql(branch,countertype, ticket, 'del')
        except Exception as e:
            current_task.status = 'ERROR'
            return current_task.status

    # websocket to voice com
    msgid_h = 'voice_Call/Get_' + datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S%f')
    try:
        wssendvoice_v840(branch, countertype, counterstatus, ticket, msgid_h)
    except Exception as e:
        current_task.status = 'ERROR'
        return current_task.status

    # websocket to flash light
    try:
        wssendflashlight(branch, countertype, counterstatus, 'flash')    
    except Exception as e:
        current_task.status = 'ERROR'
        return current_task.status

    # websocket to web softkey for update counter status
    wscounterstatus(counterstatus)
    try:
        wscounterstatus(counterstatus) 
    except Exception as e:
        current_task.status = 'ERROR'
        return current_task.status

    current_task.status = 'SUCCESS'
    return current_task.status

# def funCounterCall_old(user, branch, countertype, counterstatus, logtext, rx_app, rx_version, datetime_now):
#     status = dict({})
#     msg = dict({})
#     context = dict({})

#     # check call priority
#     # if priority = 'time' / 'umask' user mask / 'bmask' branch mask
#     priority = ''
#     mask = ''
#     if status == dict({}) :
#         userp = None
#         obj_userp = UserProfile.objects.filter(user__exact=user)
#         if obj_userp.count() == 1 :
#             userp = obj_userp[0]            
#         if userp == None:
#             status = dict({'status': 'Error'})
#             msg =  dict({'msg':'User profile not found'})  
#     if status == dict({}) :
#         qp = userp.queuepriority
#         if qp == 'time':
#             mask = userp.tickettype
#             priority = 'time'
#         if qp == 'user':            
#             mask = userp.tickettype
#             priority = 'umask'
#         if qp == 'mask':
#             # branch mask               
#             mask = branch.queuemask
#             priority = 'bmask'
#         if qp == 'branch':
#             qp = branch.queuepriority
#             if qp == 'time':
#                 priority = 'time'
#                 mask = userp.tickettype
#             if qp == 'mask':
#                 priority = 'bmask'
#                 mask = branch.queuemask 
#             if qp == 'user':
#                 priority = 'umask'
#                 mask = userp.tickettype
#         if mask == '' or priority == '' :
#             status = dict({'status': 'Error'})
#             msg =  dict({'msg':'Queue priority not found (qp:' + qp + ') '+ mask + '<-mask , priority->' + priority})   
#         if mask != '' and priority == 'bmask' :
#             l_mask = mask.split(',')
#             new_mask=''
#             l_new_mask = []
#             mask_b = mask
#             # remove all space in mask_b
#             mask_b = mask_b.replace(' ', '')
#             u_tt = userp.tickettype
#             u_tt = u_tt.replace(' ', '')
#             l_mask_b = mask_b.split(',')
#             l_u_tt = u_tt.split(',')

#             # check user ticket type in branch mask
#             for tt in l_mask_b:
#                 if tt in l_u_tt:
#                     new_mask = new_mask + tt + ','
#                     l_new_mask.append(tt)

#             # istart = 0
#             # # get text inside mask_b string format '{x}{y}{z}' -> x,y,z
#             # for i in range(len(mask_b)):
#             #     if mask_b[i] == '{':
#             #         for j in range(i+1, len(mask_b)):
#             #             if mask_b[j] == '}':
#             #                 tt = mask_b[i:j+1]
#             #                 istart = j + 1
#             #                 if u_tt.find(tt) != -1 :
#             #                     new_mask  = new_mask + tt
#             #                 break                   
#             mask = new_mask
#             l_mask = l_new_mask
#         if priority == 'bmask' or priority == 'umask' :
#             priority = 'mask'
#     if status == dict({}) :
#         # get the Counter type
#         ctypeobj = CounterType.objects.filter( Q(branch=branch) & Q(name=countertype.name) )
#         if not(ctypeobj.count() > 0) :
#             status = dict({'status': 'Error'})
#             msg =  dict({'msg':'Counter Type not found'})  
#     if status == dict({}) :
#         countertype = ctypeobj[0]
#         cstatusobj = CounterStatus.objects.filter( Q(countertype=countertype) & Q(counternumber=counterstatus.counternumber) & Q(user=user))
#         if not(cstatusobj.count() > 0) :
#             status = dict({'status': 'Error'})
#             msg =  dict({'msg':'Counter not found / User did not login'})  
#     if status == dict({}) :
#         counterstatus = cstatusobj[0]
#         counterstatus.lastactive = datetime_now
#         counterstatus.save()

#         # check counter status
#         if not(counterstatus.status == 'waiting' or counterstatus.status == 'ready') :
#             status = dict({'status': 'Error'})
#             msg =  dict({'msg':'Counter status is not WAITING/READY'})  
#         elif counterstatus.tickettemp != None :
#             status = dict({'status': 'Error'})
#             msg =  dict({'msg':'Counter still processing ticket:' + counterstatus.tickettemp.tickettype + counterstatus.tickettemp.ticketnumber})  



#     if status == dict({}) :
#         mask = mask.replace(' ', '')
#         l_mask = mask.split(',')
#         ticket = None

#         if priority== 'time':
#             # found the waiting ticket by time
#             ticketlist = TicketTemp.objects.filter( Q(branch=branch) & Q(countertype=countertype) & Q(status=lcounterstatus[0]) & Q(locked=False)).order_by('tickettime')            
#             for ticket in ticketlist:
#                 tt =  ticket.tickettype 
#                 if ticket.tickettype in l_mask:
#                     # call this ticket
#                     context = {'priority': priority, 'mask': mask, 'tickettype': ticket.tickettype, 'ticketnumber': ticket.ticketnumber , 'tickettime': ticket.tickettime}
#                     break
#         elif priority == 'mask':
#             ticketlist = TicketTemp.objects.filter( Q(branch=branch) & Q(countertype=countertype) & Q(status=lcounterstatus[0]) & Q(locked=False)).order_by('tickettime')

#             for tt in l_mask:
#                 for ticket in ticketlist:
#                     if tt == ticket.tickettype:
#                         # call this ticket
#                         context = {'priority': priority, 'mask': mask, 'tickettype': ticket.tickettype, 'ticketnumber': ticket.ticketnumber , 'tickettime': ticket.tickettime}
#                         break
#                 if context != dict({}):
#                     break
         
#         if context != dict({}) and ticket != None :
#             # update ticketdata db
#             td = None
#             if status == dict({}) :
#                 obj_td = TicketData.objects.filter(
#                     tickettemp=ticket,
#                     countertype=countertype,
#                     step=ticket.step,
#                     branch=branch,
#                 )
#                 if obj_td.count() == 1 :
#                     td = obj_td[0]
#                 else:
#                     status = dict({'status': 'Error'})
#                     msg =  dict({'msg':'TicketData is multi ' })  
#                 if td == None :
#                     status = dict({'status': 'Error'})
#                     msg =  dict({'msg':'TicketData not found ' }) 

#             if status == dict({}) :
#                 td.calltime = datetime_now
#                 td.calluser = user
#                 time_diff = datetime_now - td.starttime
#                 tsecs = int(time_diff.total_seconds())
#                 td.waitingperiod = tsecs
#                 td.save()

#                 # update counterstatus db 
#                 counterstatus.tickettemp = ticket
#                 counterstatus.status = lcounterstatus[1]
#                 counterstatus.save()

#                 # update ticket 
#                 ticket.user = user
#                 ticket.status = lcounterstatus[1]
#                 ticket.ticketroute.waiting = ticket.ticketroute.waiting - 1
#                 ticket.ticketroute.save()
#                 ticket.save()

#                 # add ticketlog
#                 localdate_now = funUTCtoLocal(datetime_now, branch.timezone)
#                 TicketLog.objects.create(
#                     tickettemp=ticket,
#                     logtime=datetime_now,
#                     app = rx_app,
#                     version = rx_version,
#                     logtext= logtext + branch.bcode + '_' + ticket.tickettype + '_'+ ticket.ticketnumber + '_' + localdate_now.strftime('%Y-%m-%d_%H:%M:%S') ,
#                     user=user,
#                 )

#                 # do display and voice temp db
#                 newdisplayvoice(branch, countertype, counterstatus.counternumber, ticket, datetime_now, user)

#                 # websocket to web tv
#                 wssendwebtv(branch, countertype)
#                 # websocket to Display Panel display ticket
#                 wssenddispcall(branch,counterstatus, countertype, ticket)
#                 # websocket to softkey (update Queue List)
#                 wssendql(branch, countertype, ticket, 'del')
#                 # websocket to web my ticket
#                 wsSendTicketStatus(branch, ticket, counterstatus)    
#                 # websocket to voice com and flash light
#                 wssendvoice(branch.bcode, countertype.name, ticket.tickettype, ticket.ticketnumber, counterstatus.counternumber)
#                 wssendvoice830(branch.bcode, countertype.name, counterstatus.id, ticket.tickettype_disp, ticket.ticketnumber_disp, counterstatus.counternumber)
#                 wssendvoice840(branch, countertype, counterstatus, ticket, 'asdf1234')
#                 wssendflashlight(branch, countertype, counterstatus, 'flash')

#                 # websocket to web softkey for update counter status
#                 wscounterstatus(counterstatus)

#         context = dict({'data':context})
#         status = dict({'status': 'OK'})
#         # msg =  dict({'msg':'Everything will be OK.'})        

#     return status, msg, context

def funCounterProcess(user, branch, countertype, counterstatus, logtext, rx_app, rx_version, datetime_now):
    status = dict({})
    msg = dict({})

    if status == dict({}) :
        ticket = counterstatus.tickettemp
        if ticket == None :
            status = dict({'status': 'Error'})
            msg =  dict({'msg':'Ticket not found ' })
    if status == dict({}) :
        # update ticketdata db
        td = None
        obj_td = TicketData.objects.filter(
            tickettemp=ticket,            
            countertype=countertype,
            step=ticket.step,
            branch=branch,
        )
        if obj_td.count() == 1 :
            td = obj_td[0]
        else:
            status = dict({'status': 'Error'})
            msg =  dict({'msg':'TicketData is multi ' })  

        if td == None :
            status = dict({'status': 'Error'})
            msg =  dict({'msg':'TicketData not found ' })            
        elif td.calltime == None:
            status = dict({'status': 'Error'})
            msg =  dict({'msg':'TicketData: calltime not found'})  
    if status == dict({}) :            
        td.processtime = datetime_now
        td.processuser = user
        time_diff = datetime_now - td.calltime
        tsecs = int(time_diff.total_seconds())
        td.walkingperiod = tsecs
        td.save()

        # update counterstatus db 
        counterstatus.tickettemp = ticket
        counterstatus.status = lcounterstatus[2]
        counterstatus.save()

        # update ticket 
        ticket.user = user
        ticket.status = lcounterstatus[2]
        ticket.save()
        
        # booking ticket
        if ticket.booking_id != None:
            from booking.views import funBookingLog

            booking = Booking.objects.get(id=ticket.booking_id)
            booking.status = Booking.STATUS.STARTED
            booking.save()
            # get the new timeslot and create a log
            funBookingLog(datetime_now, booking.timeslot, booking, TimeSlot.ACTION.NULL, Booking.STATUS.STARTED, user, None)

        # add ticketlog
        localdate_now = funUTCtoLocal(datetime_now, branch.timezone)
        TicketLog.objects.create(
            tickettemp=ticket,
            logtime=datetime_now,
            app = rx_app,
            version = rx_version,
            logtext= logtext + branch.bcode + '_' + ticket.tickettype + '_'+ ticket.ticketnumber + '_' + localdate_now.strftime('%Y-%m-%d_%H:%M:%S') ,
            user=user,
        )
        # call centre mode only
        if countertype.countermode == 'cc':
            # end of 'walking' period
            objusl = UserStatusLog.objects.filter(Q(user=user) & Q(status=lcounterstatus[lcounterstatus.index('walking')]) & Q(endtime=None))
            for usl in objusl:
                usl.endtime = datetime_now
                usl.save()
            # start of 'processing' period
            UserStatusLog.objects.create(
                user = user,
                starttime = datetime_now,
                status = lcounterstatus[lcounterstatus.index('processing')],
            )  
        # websocket to web softkey for update counter status
        # wscounterstatus(counterstatus)

        redis_online = check_redis_connection()
        # pass the sub to celery parallel run
        if redis_online:
            try:
                t_ws_cs = t_WS_CounterStatus.apply_async (args=[counterstatus.id], countdown=0)
                logging.info('Start task : t_ws_cs (wscounterstatus) : ' + str(t_ws_cs))
            except Exception as e:
                logging.error('Error t_ws_cs : ' + str(e))
                pass
        else:
            logging.error('Redis is offline. Cannot run t_ws_cs')

        status = dict({'status': 'OK'})
        msg =  dict({'msg':'Process ticket.'})
    return status, msg

@shared_task
def t_WS_CounterStatus(counterstatus_id):
    from celery import current_task

    # Get my task ID
    my_id = current_task.request.id
    logger.info(f'CounterStatus WS data out (wscounterstatus): {my_id}')

    counterstatus = CounterStatus.objects.get(id=counterstatus_id)

    current_task.status = 'PROGRESS'
    # websocket to web softkey for update counter status
    try:
        wscounterstatus(counterstatus)
    except Exception as e:
        current_task.status = 'ERROR'
        return current_task.status
    
    current_task.status = 'SUCCESS'
    return current_task.status

def funCounterComplete(user, branch, countertype, counterstatus, logtext, rx_app, rx_version, datetime_now):
    status = dict({})
    msg = dict({})

    if status == dict({}) :
        ticket = counterstatus.tickettemp
        if ticket == None :
            status = dict({'status': 'Error'})
            msg =  dict({'msg':'Ticket not found ' })
    if status == dict({}) :
        # update ticketdata db
        td = None
        obj_td = TicketData.objects.filter(
            tickettemp=ticket,
            countertype=countertype,
            step=ticket.step,
            branch=branch,            
        )
        if obj_td.count() == 1 :
            td = obj_td[0]
        else:
            status = dict({'status': 'Error'})
            msg =  dict({'msg':'TicketData is multi ' })   
        if td == None:        
            status = dict({'status': 'Error'})
            msg =  dict({'msg':'TicketData not found ' })            
        elif td.calltime == None or td.walkingperiod == None or td.waitingperiod == None :
            status = dict({'status': 'Error'})
            msg =  dict({'msg':'TicketData - data not correct'})


    if status == dict({}) :
        td.donetime = datetime_now
        td.doneuser = user
        time_diff = datetime_now - td.calltime
        tsecs = int(time_diff.total_seconds())
        td.processingperiod = tsecs
        total = tsecs + td.walkingperiod + td.waitingperiod
        td.totalperiod = total
        td.save()

        # update counterstatus db 
        counterstatus.tickettemp = None
        counterstatus.status = lcounterstatus[0]
        counterstatus.save()

        # check ticket next step
        step = ticket.step
        nextstep = step +1
        routeobj = TicketRoute.objects.filter(branch=branch, step=nextstep, tickettype=ticket.tickettype)       

        # booking ticket 
        if ticket.booking_id != None:
            from booking.views import funBookingLog

            booking = Booking.objects.get(id=ticket.booking_id)
            booking.status = Booking.STATUS.COMPLETED
            booking.save()
            # get the new timeslot and create a log
            funBookingLog(datetime_now, booking.timeslot, booking, TimeSlot.ACTION.NULL, Booking.STATUS.COMPLETED, user, None)

        if routeobj.count() != 1 :
            # no next step
            ticket.status = lcounterstatus[3]  #'done'
            ticket.save()

            # add ticketlog
            localdate_now = funUTCtoLocal(datetime_now, branch.timezone)
            TicketLog.objects.create(
                tickettemp=ticket,
                logtime=datetime_now,
                app = rx_app,
                version = rx_version,
                logtext=logtext + branch.bcode + '_' + ticket.tickettype + '_'+ ticket.ticketnumber + '_' + localdate_now.strftime('%Y-%m-%d_%H:%M:%S') ,
                user=user,
            )

        else:
            # next step
            route = routeobj[0] 
            route.waiting = route.waiting + 1
            route.save()

            countertype = route.countertype
            ticket.countertype = countertype
            ticket.ticketroute = routeobj[0]
            ticket.status = lcounterstatus[0]
            ticket.step = nextstep
            ticket.save()

            redis_online = check_redis_connection()
            # pass the sub to celery parallel run
            if redis_online:
                try:
                    t_ws_completenext = t_WS_CompleteNext.apply_async (args=[branch.id, countertype.id, ticket.id, 'add'], countdown=0)
                    logging.info('Start task : t_ws_completenext (wssendql, wssendwebtv) : ' + str(t_ws_completenext))
                except Exception as e:
                    logging.error('Error t_ws_completenext : ' + str(e))
                    pass
            else:
                logging.error('Redis is offline. Cannot run t_ws_completenext')

            # new ticket data
            TicketData.objects.create(
                tickettemp=ticket,
                branch = branch,
                countertype=countertype,
                step=ticket.step,
                starttime = datetime_now,
                startuser=user,
            )

            # add ticketlog
            localdate_now = funUTCtoLocal(datetime_now, branch.timezone)
            TicketLog.objects.create(
                tickettemp=ticket,
                logtime=datetime_now,
                app = rx_app,
                version = rx_version,
                logtext= 'Next step ' + logtext + branch.bcode + '_' + ticket.tickettype + '_'+ ticket.ticketnumber + '_' + localdate_now.strftime('%Y-%m-%d_%H:%M:%S'),
                user=user,
            )

            # call centre mode only
            if countertype.countermode == 'cc':
                objusl = UserStatusLog.objects.filter(Q(user=user) & Q(status=lcounterstatus[lcounterstatus.index('processing')]) & Q(endtime=None))
                for usl in objusl:
                    usl.endtime = datetime_now
                    usl.save()

        # # websocket to web my ticket
        # wsSendTicketStatus(branch, ticket, counterstatus)    

        # # websocket to web softkey for update counter status
        # wscounterstatus(counterstatus)
        redis_online = check_redis_connection()
        # pass the sub to celery parallel run
        if redis_online:
            try:
                t_ws_complete = t_WS_Complete.apply_async (args=[branch.id, ticket.id, counterstatus.id], countdown=0)
                logging.info('Start task : t_ws_complete (wsSendTicketStatus, wscounterstatus) : ' + str(t_ws_complete))
            except Exception as e:
                logging.error('Error t_ws_complete : ' + str(e))
                pass
        else:
            logging.error('Redis is offline. Cannot run t_ws_complete')

        status = dict({'status': 'OK'})
        msg =  dict({'msg':'Ticket done.'})
    return status, msg

@shared_task
def t_WS_Complete(branch_id, ticket_id, counterstatus_id):
    from celery import current_task

    # Get my task ID
    my_id = current_task.request.id
    logger.info(f'TicketStatus WS data out (wsSendTicketStatus): {my_id}')

    branch = Branch.objects.get(id=branch_id)
    ticket = TicketTemp.objects.get(id=ticket_id)
    counterstatus = CounterStatus.objects.get(id=counterstatus_id)
    
    current_task.status = 'PROGRESS'
    # websocket to web my ticket
    try:
        wsSendTicketStatus(branch, ticket, counterstatus)    
    except Exception as e:
        current_task.status = 'ERROR'
        return current_task.status

    #  websocket to web softkey for update counter status
    try:
        wscounterstatus(counterstatus)
    except Exception as e:
        current_task.status = 'ERROR'
        return current_task.status

    current_task.status = 'SUCCESS'
    return current_task.status
@shared_task
def t_WS_CompleteNext(branch_id, countertype_id, tickett_id, ql):
    from celery import current_task

    # Get my task ID
    my_id = current_task.request.id
    logger.info(f't_WS_CompleteNext WS data out (wssendql, wssendwebtv): {my_id}')

    branch = Branch.objects.get(id=branch_id)
    countertype = CounterType.objects.get(id=countertype_id)
    tickett = TicketTemp.objects.get(id=tickett_id)

    current_task.status = 'PROGRESS'
    # websocket to softkey (update Queue List)
    try:
        wssendql(branch, countertype, tickett, ql)
    except Exception as e:
        current_task.status = 'ERROR'
        return current_task.status
    
    # websocket to webtv
    try:
        wssendwebtv(branch, countertype)
    except Exception as e:
        current_task.status = 'ERROR'
        return current_task.status
        
    current_task.status = 'SUCCESS'
    return current_task.status

def funCounterMiss(user, branch, countertype, counterstatus, logtext, rx_app, rx_version, datetime_now):
    status = dict({})
    msg = dict({})

    if status == dict({}) :
        ticket = counterstatus.tickettemp
        if ticket == None :
            status = dict({'status': 'Error'})
            msg =  dict({'msg':'Ticket not found ' })
    if status == dict({}) :
        # update ticketdata db
        td = None
        obj_td = TicketData.objects.filter(
            tickettemp=ticket,
            countertype=countertype,
            step=ticket.step,
            branch=branch,
        )
        if obj_td.count() == 1 :
            td = obj_td[0]
        else:
            status = dict({'status': 'Error'})
            msg =  dict({'msg':'TicketData is multi ' })     
        if td == None :
            status = dict({'status': 'Error'})
            msg =  dict({'msg':'TicketData not found ' })            
        elif td.calltime == None:
            status = dict({'status': 'Error'})
            msg =  dict({'msg':'TicketData : call time is None'})  

    if status == dict({}) :
        td.misstime = datetime_now
        td.missuser = user
        time_diff = datetime_now - td.calltime
        tsecs = int(time_diff.total_seconds())
        td.walkingperiod = tsecs
        td.save()

        # update counterstatus db 
        counterstatus.tickettemp = None
        counterstatus.status = lcounterstatus[0]
        counterstatus.save()

        # update ticket 
        ticket.user = user
        ticket.status = 'miss'
        ticket.save()
        

        # add ticketlog
        localdate_now = funUTCtoLocal(datetime_now, branch.timezone)
        TicketLog.objects.create(
            tickettemp=ticket,
            logtime=datetime_now,
            app = rx_app,
            version = rx_version,
            logtext=logtext + branch.bcode + '_' + ticket.tickettype + '_'+ ticket.ticketnumber + '_' + localdate_now.strftime('%Y-%m-%d_%H:%M:%S') ,
            user=user,
        )

        # booking ticket
        if ticket.booking_id != None:
            from booking.views import funBookingLog
            
            booking = Booking.objects.get(id=ticket.booking_id)
            booking.status = Booking.STATUS.NOSHOW
            booking.save()
            # get the new timeslot and create a log
            funBookingLog(datetime_now, booking.timeslot, booking, TimeSlot.ACTION.NULL, Booking.STATUS.NOSHOW, user, None)


        # Call Centre mode only
        if countertype.countermode == 'cc':
            # end of 'walking' period
            objusl = UserStatusLog.objects.filter(Q(user=user) & Q(status=lcounterstatus[lcounterstatus.index('walking')]) & Q(endtime=None))
            for usl in objusl:
                usl.endtime = datetime_now
                usl.save()
            # turn to 'AUX' status
            counterstatus.status = lcounterstatus[lcounterstatus.index('AUX')]
            counterstatus.save()


        # # websocket to web my ticket
        # wsSendTicketStatus(branch, ticket, counterstatus)    
        # # websocket to web softkey for update counter status
        # wscounterstatus(counterstatus)

        redis_online = check_redis_connection()
        # pass the sub to celery parallel run
        if redis_online:
            try:
                t_ws_complete = t_WS_Complete.apply_async (args=[branch.id, ticket.id, counterstatus.id], countdown=0)
                logging.info('Start task : t_ws_complete (wsSendTicketStatus, wscounterstatus) : ' + str(t_ws_complete))
            except Exception as e:
                logging.error('Error t_ws_complete : ' + str(e))
                pass
        else:
            logging.error('Redis is offline. Cannot run t_ws_complete')

        status = dict({'status': 'OK'})
        msg =  dict({'msg':'Ticket no show.'})  
    return status, msg

def funCounterRecall(user, branch, countertype, counterstatus, logtext, rx_app, rx_version, datetime_now):
    status = dict({})
    msg = dict({})

    if status == dict({}) :
        ticket = counterstatus.tickettemp
        if ticket == None :
            status = dict({'status': 'Error'})
            msg =  dict({'msg':'Ticket not found ' })
    if status == dict({}) :
        # add ticketlog

        localdate_now = funUTCtoLocal(datetime_now, branch.timezone)
        TicketLog.objects.create(
            tickettemp=ticket,
            logtime=datetime_now,
            app = rx_app,
            version = rx_version,
            logtext=logtext + branch.bcode + '_' + ticket.tickettype + '_'+ ticket.ticketnumber + '_' + localdate_now.strftime('%Y-%m-%d_%H:%M:%S') ,
            user=user,
        )

        # do display and voice temp db
        newdisplayvoice(branch, countertype, counterstatus.counternumber, ticket, datetime_now, user)

        redis_online = check_redis_connection()
        # logging.info('redis_online:' + str(redis_online))
        

        # websocket to Display Panel display ticket
        # pass the sub to celery parallel run
        if redis_online:
            try:
                t_ws_recall = t_WS_Recall.apply_async (args=[branch.id, counterstatus.id, countertype.id, ticket.id], countdown=0)
                logging.info('Start task : t_ws_recall (wssendwebtv, wssenddispcall_v840, wssendvoice_v840, wssendflashlight) : ' + str(t_ws_recall))
            except Exception as e:
                logging.error('Error t_WS_Recall : ' + str(e))
                pass
        else:
            logging.error('Redis is offline. Cannot run t_WS_Recall')
    # WS send data :
        # # websocket to web tv
        # wssendwebtv(branch, countertype)
        # wssenddispcall(branch, counterstatus, countertype, ticket)
        # # websocket to voice com and flash light
        # wssendvoice(branch.bcode, countertype.name, ticket.tickettype, ticket.ticketnumber, counterstatus.counternumber)
        # wssendvoice830(branch.bcode, countertype.name, counterstatus.id, ticket.tickettype_disp, ticket.ticketnumber_disp, counterstatus.counternumber)
        # wssendflashlight(branch, countertype, counterstatus, 'flash')

        status = dict({'status': 'OK'})
        msg =  dict({'msg':'Recall ticket.'}) 
    return status, msg

@shared_task
def t_WS_Recall(branch_id, counterstatus_id, countertype_id, ticket_id):
    from celery import current_task

    branch = Branch.objects.get(id=branch_id)
    counterstatus = CounterStatus.objects.get(id=counterstatus_id)
    countertype = CounterType.objects.get(id=countertype_id)
    ticket = TicketTemp.objects.get(id=ticket_id)

    # Get my task ID
    my_id = current_task.request.id
    logger.info(f'Recall WS data out (wssendwebtv, wssenddispcall_v840, wssendvoice_v840, wssendflashlight): {my_id}')

    current_task.status = 'PROGRESS'

    # websocket to voice com
    msgid_h = 'voice_recall_' + datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S%f')
    try:
        wssendvoice_v840(branch, countertype, counterstatus, ticket, msgid_h)
    except Exception as e:
        current_task.status = 'ERROR'
        return current_task.status

    # websocket to Display Panel display ticket
    try:
        wssenddispcall_v840(branch, counterstatus, countertype, ticket)
    except Exception as e:
        current_task.status = 'ERROR'
        return current_task.status

    # websocket to web tv
    try:
        wssendwebtv(branch, countertype)
    except Exception as e:
        current_task.status = 'ERROR'
        return current_task.status

    # websocket to flash light
    try:
        wssendflashlight(branch, countertype, counterstatus, 'flash')    
    except Exception as e:
        current_task.status = 'ERROR'
        return current_task.status

    current_task.status = 'SUCCESS'
        
    return current_task.status

@transaction.atomic
def funCounterGet_v840(gettnumber, user, branch, countertype, counterstatus, logtext, rx_app, rx_version, datetime_now):
    status = dict({})
    msg = dict({})
    context = dict({})
    ticket = None
    gettt = ''
    gettno = ''

    input_tno_list = []
    input_tno_list = funTicketToList(gettnumber)

    if status == dict({}) :
        if input_tno_list == []:
            status = dict({'status': 'Error'})
            msg =  dict({'msg':'Please input ticket'})
    
    
    if status == dict({}) :
        if counterstatus.status != 'waiting':
            status = dict({'status': 'Error'})
            msg =  dict({'msg':'Counter status is not waiting.'})


    if status == dict({}) :
        # find ticket in waiting list
        objt = TicketTemp.objects.filter(
            branch=branch,
            status='waiting',
            locked=False).order_by('-tickettime')

        for t in objt:
            tno = t.tickettype_disp + t.ticketnumber_disp
            tno_list = funTicketToList(tno)
            if input_tno_list == tno_list:
                ticket = t
                break
        if ticket == None:
            # find ticket in miss list
            objt = TicketTemp.objects.filter(
                branch=branch,
                status='miss',
                locked=False).order_by('-tickettime')
            for t in objt:
                tno = t.tickettype_disp + t.ticketnumber_disp
                tno_list = funTicketToList(tno)
                if input_tno_list == tno_list:
                    ticket = t
                    break
        if ticket == None:
            status = dict({'status': 'Error'})
            msg =  dict({'msg':'Ticket not found'}) 
    

    if status == dict({}) and ticket != None :
        # lock the ticket
        try:
            ticket = TicketTemp.objects.select_for_update(nowait=True).get(id=ticket.id)
            # for testing
            # time.sleep(3)
        except Exception as e:
            from base.a_global import str_db_locked
            status = dict({'status': 'Error'})
            msg =  dict({'msg':str_db_locked})
        
    if status == dict({}) :
        # update ticketdata db
        objtd = TicketData.objects.filter(
            tickettemp=ticket,
            countertype=countertype,
            step=ticket.step,
            branch=branch,
        )
        td = None
        if objtd.count() == 1 :
            td = objtd[0]
        else:
            status = dict({'status': 'Error'})
            msg =  dict({'msg':'TicketData is multi ' })   
        if td == None:                 
            status = dict({'status': 'Error'})
            msg =  dict({'msg':'TicketData not found ' })
        else:
            if td.starttime == None:
                status = dict({'status': 'Error'})
                msg =  dict({'msg':'Ticket time is NONE' })
            else :
                td.calltime = datetime_now
                td.calluser = user
                time_diff = datetime_now - td.starttime
                tsecs = int(time_diff.total_seconds())
                td.waitingperiod = tsecs
                td.save()

    if status == dict({}) :
        # update counterstatus db 
        counterstatus.tickettemp = ticket
        counterstatus.status = lcounterstatus[1]
        counterstatus.save()

        # update ticket 
        
        delsq = False
        # waiting on queue
        if ticket.status == 'waiting':
            ticket.ticketroute.waiting = ticket.ticketroute.waiting - 1
            ticket.ticketroute.save()
            delsq = True
         
        ticket.user = user
        ticket.status = 'calling'
        ticket.save()
        

        # add ticketlog
        localdate_now = funUTCtoLocal(datetime_now, branch.timezone)
        TicketLog.objects.create(
            tickettemp=ticket,
            logtime=datetime_now,
            app = rx_app,
            version = rx_version,
            logtext=logtext  + branch.bcode + '_' + ticket.tickettype + '_'+ ticket.ticketnumber + '_' + localdate_now.strftime('%Y-%m-%d_%H:%M:%S') ,
            user=user,
        )

        # do display and voice temp db
        newdisplayvoice(branch, countertype, counterstatus.counternumber, ticket, datetime_now, user)

    # # WS send data :
        # # websocket to web my ticket
        # wsSendTicketStatus(branch, ticket, counterstatus)    
        # # websocket to voice com and flash light
        # wssendvoice(branch.bcode, countertype.name, ticket.tickettype, ticket.ticketnumber, counterstatus.counternumber)
        # wssendvoice830(branch.bcode, countertype.name, counterstatus.id, ticket.tickettype_disp, ticket.ticketnumber_disp, counterstatus.counternumber)
        # wssendvoice840(branch, countertype, counterstatus, ticket, 'asdf1234')

        # wssendflashlight(branch, countertype, counterstatus, 'flash')
        # # websocket to web softkey for update counter status
        # wscounterstatus(counterstatus)
        # # websocket to web tv
        # wssendwebtv(branch, countertype)
        # # websocket to Display Panel display ticket
        # wssenddispcall840(branch, counterstatus, countertype, ticket)

        redis_online = check_redis_connection()
        # pass the sub to celery parallel run
        if redis_online:
            try:
                t_ws_call = t_WS_Call.apply_async (args=[branch.id, counterstatus.id, countertype.id, ticket.id, delsq], countdown=0)
                logging.info('Start task : t_ws_call from funCounterGet_v840 (wssendwebtv, wssenddispcall_v840, wssendql, wssendvoice_v840, wssendflashlight, wscounterstatus) : ' + str(t_ws_call))
            except Exception as e:
                logging.error('Error t_ws_call from funCounterGet_v840: ' + str(e))
                pass
        else:
            logging.error('Redis is offline. Cannot run t_ws_call from funCounterGet_v840') 

        context = {'tickettype': ticket.tickettype, 
                   'ticketnumber': ticket.ticketnumber , 
                   'tickettime': ticket.tickettime}
        context = dict({'data':context})
        status = dict({'status': 'OK'})
        msg =  dict({'msg':'Ticket Get.'})
    return status, msg, context

def funTicketToList(input:str):
    out_list = []

    if input == None:
        pass
    else:
        i = 0
        while i < len(input):
            if input[i].isalpha():
                if i > 0 and input[i-1].isalpha():
                    out_list[-1] += input[i].upper()
                else:
                    out_list.append(input[i].upper())
            elif input[i].isdigit():
                if i > 0 and input[i-1].isdigit():
                    out_list[-1] = int(str(out_list[-1]) + input[i])
                else:
                    out_list.append(int(input[i]))
            i += 1

    return out_list

# def funCounterGet_old(getticket, getttype, gettnumber, user, branch, countertype, counterstatus, logtext, rx_app, rx_version, datetime_now):
#     status = dict({})
#     msg = dict({})
#     context = dict({})
#     ticket = None
#     gettt = ''
#     gettno = ''

#     if getticket == '' :
#         gettt = getttype
#         gettno = gettnumber
#     else:
#         if status == dict({}) :
#             if getticket == '':
#                 status = dict({'status': 'Error'})
#                 msg =  dict({'msg':'Please input ticket'})
#         if status == dict({}) :
#             # split getticket to gettt and gettno
#             for i in range(len(getticket)):
#                 if getticket[i].isalpha() == False:
#                     gettt = getticket[0:i]
#                     gettno = getticket[i:]
#                     break
#     if status == dict({}) :
#         if gettt == '':
#             status = dict({'status': 'Error'})
#             msg =  dict({'msg':'Please input ticket type.'})
#     # check gettt is letter only
#     if status == dict({}) :
#         if gettt.isalpha() == False:
#             status = dict({'status': 'Error'})
#             msg =  dict({'msg':'Ticket type must be letter only.'})
#     if status == dict({}) :
#         if gettno == '':
#             status = dict({'status': 'Error'})
#             msg =  dict({'msg':'Please input ticket number.'})
#     if status == dict({}) :
#         # check gettno is number only
#         if gettno.isnumeric() == False:
#             status = dict({'status': 'Error'})
#             msg =  dict({'msg':'Ticket number must be number only.'})        
#     if status == dict({}) :
#         # change gettno to "000" format and convert to string
#         tformat = counterstatus.countertype.branch.ticketnoformat 
#         gettno = tformat + str(gettno)
#         # get gettno string right 3 char
#         gettno = gettno[-len(tformat):]

#     if status == dict({}) :
#         if counterstatus.status != 'waiting':
#             status = dict({'status': 'Error'})
#             msg =  dict({'msg':'Counter status is not waiting.'})


#     if status == dict({}) :
#         # find ticket in waiting list
#         objt = TicketTemp.objects.filter(
#             tickettype=gettt,
#             ticketnumber=gettno,
#             branch=branch,
#             status='waiting',
#             locked=False).order_by('-tickettime')
#         if objt.count() >= 1 :
#             ticket = objt[0]
#         else:
#             # find ticket in miss list
#             objt = TicketTemp.objects.filter(
#                 tickettype=gettt,
#                 ticketnumber=gettno,
#                 branch=branch,
#                 status='miss',
#                 locked=False).order_by('-tickettime')
#             if objt.count() >= 1 :
#                 ticket = objt[0]
#         if ticket == None:
#             status = dict({'status': 'Error'})
#             msg =  dict({'msg':'Ticket not found'}) 

      
        
#     if status == dict({}) :
#         # update ticketdata db
#         objtd = TicketData.objects.filter(
#             tickettemp=ticket,
#             countertype=countertype,
#             step=ticket.step,
#             branch=branch,
#         )
#         td = None
#         if objtd.count() == 1 :
#             td = objtd[0]
#         else:
#             status = dict({'status': 'Error'})
#             msg =  dict({'msg':'TicketData is multi ' })   
#         if td == None:                 
#             status = dict({'status': 'Error'})
#             msg =  dict({'msg':'TicketData not found ' })
#         else:
#             if td.starttime == None:
#                 status = dict({'status': 'Error'})
#                 msg =  dict({'msg':'Ticket time is NONE' })
#             else :
#                 td.calltime = datetime_now
#                 td.calluser = user
#                 time_diff = datetime_now - td.starttime
#                 tsecs = int(time_diff.total_seconds())
#                 td.waitingperiod = tsecs
#                 td.save()

#     if status == dict({}) :
#         # update counterstatus db 
#         counterstatus.tickettemp = ticket
#         counterstatus.status = lcounterstatus[1]
#         counterstatus.save()

#         # update ticket 
        
#         # waiting on queue
#         if ticket.status == 'waiting':
#             ticket.ticketroute.waiting = ticket.ticketroute.waiting - 1
#             ticket.ticketroute.save()
#             # websocket to softkey (update Queue List)
#             wssendql(branch, countertype, ticket, 'del')
#         ticket.user = user
#         ticket.status = 'calling'
#         ticket.save()
        

#         # add ticketlog
#         localdate_tickettime = funUTCtoLocal(ticket.tickettime, branch.timezone)
#         TicketLog.objects.create(
#             tickettemp=ticket,
#             logtime=datetime_now,
#             app = rx_app,
#             version = rx_version,
#             logtext=logtext  + branch.bcode + '_' + ticket.tickettype + '_'+ ticket.ticketnumber + '_' + localdate_tickettime.strftime('%Y-%m-%d_%H:%M:%S') ,
#             user=user,
#         )

#         # do display and voice temp db
#         newdisplayvoice(branch, countertype, counterstatus.counternumber, ticket, datetime_now, user)
#         # websocket to web my ticket
#         wsSendTicketStatus(branch, ticket, counterstatus)    
#         # websocket to voice com and flash light
#         wssendvoice(branch.bcode, countertype.name, ticket.tickettype, ticket.ticketnumber, counterstatus.counternumber)
#         wssendvoice830(branch.bcode, countertype.name, counterstatus.id, ticket.tickettype_disp, ticket.ticketnumber_disp, counterstatus.counternumber)
#         wssendvoice840(branch, countertype, counterstatus, ticket, 'asdf1234')
#         wssendflashlight(branch, countertype, counterstatus, 'flash')
#         # websocket to web softkey for update counter status
#         wscounterstatus(counterstatus)
#         # websocket to web tv
#         wssendwebtv(branch, countertype)
#         # websocket to Display Panel display ticket
#         wssenddispcall840(branch, counterstatus, countertype, ticket)

#         context = {'tickettype': ticket.tickettype, 
#                    'ticketnumber': ticket.ticketnumber , 
#                    'tickettime': ticket.tickettime}
#         context = dict({'data':context})
#         status = dict({'status': 'OK'})
#         msg =  dict({'msg':'Ticket Get.'})
#     return status, msg, context

def funCounterLogout(counterstatus, datetime_now):

    logoutOK = logcounterlogout(counterstatus.user, counterstatus.countertype, counterstatus.counternumber, counterstatus.logintime, datetime_now)
    if logoutOK == 'OK' :
        # counter replace new user
        counterstatus.user = None
        counterstatus.loged = False
        counterstatus.logintime = None
        counterstatus.lastactive = None
        counterstatus.status = lcounterstatus[0]
        counterstatus.tickettemp = None
        counterstatus.save()

        status = dict({'status': 'OK'})
        msg =  dict({'msg':'Logout completed'})  
    else:
        status = dict({'status': 'Error'})
        msg =  dict({'msg':logoutOK})  
    return status, msg














def funCounterLogin(datetime_now, user, branch, counterstatus, rx_counternumber, countertype):
    status = dict({})
    msg = dict({})
    context = dict({})
    booking_time_local = ''
    booking_id = None
    booking_name = None    

    if status == dict({}) :
        # check the counter is enabled
        if counterstatus.enabled == False :
            status = dict({'status': 'Error'})
            msg =  dict({'msg':'Counter is disabled'})  

    # get user profiles
    if status == dict({}) :
        userp = None
        obj_userp =UserProfile.objects.filter(user__exact=user)
        if obj_userp.count() == 1 :
            userp = obj_userp[0]
        if userp == None :
            status = dict({'status': 'Error'})
            msg =  dict({'msg':'user profile not found or more then one'})       

    # check the user is already login 
    if status == dict({}) :
        if branch.usersinglelogin == True :
            csobj = CounterStatus.objects.filter(loged=True, user=user)
            if csobj.count() > 0 :
                    islogged = False
                    error = ''
                    for cs in csobj:
                        if cs.countertype.branch == branch and cs.counternumber != rx_counternumber:
                            islogged = True
                            error = 'User already logged-in at counter ' + cs.counternumber
                            break
                        if cs.countertype.branch != branch :
                            islogged = True
                            error = 'User already logged-in at other branch ' + cs.countertype.branch.name
                            break
                    if islogged == True:
                        status = dict({'status': 'Error'})
                        msg =  dict({'msg':error})    
    
    ttype=''
    tno = ''
    ttime=''
    # check the user come back to counter
    if status == dict({}) :
        if counterstatus.loged == True:
            if counterstatus.user == user :
                # user come back to counter
                counterstatus.lastactive = datetime_now
                counterstatus.save()
                status = dict({'status': 'OK'})
                msg =  dict({'msg':'Welcome back'})  

                if counterstatus.tickettemp != None:
                    ttype = counterstatus.tickettemp.tickettype_disp
                    tno = counterstatus.tickettemp.ticketnumber_disp
                    ttime = counterstatus.tickettemp.tickettime

                # context = {'name': user.first_name + ' ' + user.last_name , 'ttype': userp.tickettype, 'timezone': branch.timezone,
                # 'counterstatus':counterstatus.status, 'tickettype':ttype, 'ticketnumber':tno, 'tickettime':ttime,
                # 'ticketnoformat':branch.ticketnoformat,
                # }
                # context = dict({'data':context})

            else :
                # other user login to this counter
                #  need auto logout ? and then login again
                timediff = datetime_now - counterstatus.lastactive 
                timediff = timediff.seconds / 60
                if timediff >= counteractive : # if the counter keep active > 6 minutes then auto logout and the counter replace the new user
                    # auto logout and counter replace new user
                    autologoutOK = logcounterlogout(counterstatus.user, countertype, rx_counternumber, counterstatus.logintime, counterstatus.lastactive)
                    if autologoutOK == 'OK' :
                        # counter replace new user
                        counterstatus.user = user
                        counterstatus.loged = True
                        counterstatus.logintime = datetime_now
                        counterstatus.lastactive = datetime_now
                        counterstatus.save()
                        
                        logcounterlogin(user, countertype, rx_counternumber, datetime_now)
                        status = dict({'status': 'OK'})
                        msg =  dict({'msg':'Have a nice day'})  

                        if counterstatus.tickettemp != None:
                            ttype = counterstatus.tickettemp.tickettype
                            tno = counterstatus.tickettemp.ticketnumber
                            ttime = counterstatus.tickettemp.tickettime
                       
                    else:
                        status = dict({'status': 'Error'})
                        msg =  dict({'msg':'Counter auto logout fault'}) 
                else:
                    status = dict({'status': 'Error'})
                    msg =  dict({'msg':'Counter already Login, please wait ' + str(counteractive) + ' minutes'})
    # normal login
    if status == dict({}) : 
        # login 
        if countertype.countermode == 'normal':
            pass
        elif countertype.countermode == 'cc':
            # counter status sould be start at 'AUX'
            counterstatus.status = lcounterstatus[lcounterstatus.index('AUX')]
            counterstatus.save()

        counterstatus.user = user
        counterstatus.loged = True
        counterstatus.logintime = datetime_now
        counterstatus.lastactive = datetime_now
        counterstatus.save()       

        logcounterlogin(user, countertype, rx_counternumber, datetime_now)

        if counterstatus.tickettemp != None:
            ttype = counterstatus.tickettemp.tickettype
            tno = counterstatus.tickettemp.ticketnumber
            ttime = counterstatus.tickettemp.tickettime
    if status == dict({}) or status.get('status') == 'OK': 
        if counterstatus.tickettemp != None:
            if counterstatus.tickettemp.booking_id != None:
                booking_id = counterstatus.tickettemp.booking_id
                booking_name = counterstatus.tickettemp.booking_name                
                booking_time_local = funUTCtoLocal(counterstatus.tickettemp.booking_time, branch.timezone)
                booking_time_local = booking_time_local.strftime('%Y-%m-%d %H:%M:%S')            
        status = dict({'status': 'OK'})
        msg =  dict({'msg':'Have a nice day'})  


    context = {
        'branch':branch.name,
        'bcode':branch.bcode,
        'countertype':counterstatus.countertype.name, 
        'counternumber':counterstatus.counternumber,
        'name': user.first_name + ' ' + user.last_name , 
        'username': user.username,
        'userttype': userp.tickettype, 
        'timezone': branch.timezone,
        'counterstatus':counterstatus.status, 
        'tickettype':ttype, 
        'ticketnumber':tno, 
        'tickettime':ttime,
        'booking_id':booking_id,
        'booking_name':booking_name,
        'booking_time':booking_time_local,
        }
    context = dict({'data':context})
    return status, msg, context

@transaction.atomic
def funVoid(user, tickett, td, logtext, rx_app, rx_version, datetime_now):
    status = dict({})
    msg = dict({})
    ticket = None

    if status == dict({}) :
        # lock the ticket
        try:
            ticket = TicketTemp.objects.select_for_update(nowait=True).get(id=tickett.id)
            # for testing
            # time.sleep(3)
        except Exception as e:
            from base.a_global import str_db_locked
            status = dict({'status': 'Error'})
            msg =  dict({'msg':str_db_locked})

    if status == dict({}) and ticket != None :
    # update ticket 
    # waiting on queue
        if ticket.status == 'waiting':
            ticket.ticketroute.waiting = ticket.ticketroute.waiting - 1
            ticket.ticketroute.save()
        ticket.user = user
        ticket.status = 'void'
        ticket.save()

        # update ticketdata db
        td.voidtime = datetime_now
        td.voiduser = user
        time_diff = datetime_now - td.starttime
        tsecs = int(time_diff.total_seconds())
        td.waitingperiod = tsecs
        td.save()

        # add ticketlog
        localdate_now = funUTCtoLocal(datetime_now, ticket.branch.timezone)
        TicketLog.objects.create(
            tickettemp=ticket,
            logtime=datetime_now,
            app = rx_app,
            version = rx_version,
            logtext= logtext + ticket.branch.bcode + '_' + ticket.tickettype + '_'+ ticket.ticketnumber + '_' + localdate_now.strftime('%Y-%m-%d_%H:%M:%S') ,
            user=user,
        )
    # # WS data send out
    #     # websocket to softkey (update Queue List)
    #     wssendql(ticket.branch , ticket.countertype, ticket, 'del')
    #     # websocket to web tv
    #     wssendwebtv(ticket.branch, ticket.countertype)
    #     # websocket to Display Panel waiting number update
    #     wssenddispwait(ticket.branch, ticket.countertype, ticket)
    #     # websocket to web my ticket
    #     wsSendTicketStatus(ticket.branch, ticket, None)
        
        redis_online = check_redis_connection()
        # pass the sub to celery parallel run
        if redis_online:
            try:
                t_ws_void = t_WS_Void.apply_async (args=[ticket.branch.id, ticket.countertype.id, ticket.id], countdown=0)
                logging.info('Start task : t_ws_void (wssendql, wssendwebtv, wssenddispwait, wsSendTicketStatus) : ' + str(t_ws_void))
            except Exception as e:
                logging.error('Error t_ws_void : ' + str(e))
                pass
        else:
            logging.error('Redis is offline. Cannot run t_ws_void')

        status = dict({'status': 'OK'})
        msg =  dict({'msg':'Ticket voided.'})
    return status, msg
@shared_task
def t_WS_Void(branch_id, countertype_id, ticket_id):
    from celery import current_task

    branch = Branch.objects.get(id=branch_id)
    countertype = CounterType.objects.get(id=countertype_id)
    ticket = TicketTemp.objects.get(id=ticket_id)

    # Get my task ID
    my_id = current_task.request.id
    logger.info(f'Void WS data out (wssendql, wssendwebtv, wssenddispwait, wsSendTicketStatus): {my_id}')

    current_task.status = 'PROGRESS'

    # websocket to softkey (update Queue List)
    try:
        wssendql(branch,countertype, ticket, 'del')
    except Exception as e:
        current_task.status = 'ERROR'
        return current_task.status

    # websocket to web tv
    try:
        wssendwebtv(branch, countertype)
    except Exception as e:
        current_task.status = 'ERROR'
        return current_task.status

    # websocket to Display Panel waiting number update
    try:
        wssenddispwait_v840(branch, countertype, ticket)
    except Exception as e:
        current_task.status = 'ERROR'
        return current_task.status

    # websocket to web my ticket
    try:
        wsSendTicketStatus(ticket.branch, ticket, None)
    except Exception as e:
        current_task.status = 'ERROR'
        return current_task.status

    current_task.status = 'SUCCESS'
    return current_task.status
# def funVoid_old(user, tickett, td, datetime_now):
#     # update ticket 
#     # waiting on queue
#     if tickett.status == 'waiting':
#         tickett.ticketroute.waiting = tickett.ticketroute.waiting - 1
#         tickett.ticketroute.save()
#     tickett.user = user
#     tickett.status = 'void'
#     tickett.save()

#     # update ticketdata db
#     td.voidtime = datetime_now
#     td.voiduser = user
#     time_diff = datetime_now - td.starttime
#     tsecs = int(time_diff.total_seconds())
#     td.waitingperiod = tsecs
#     td.save()

#     # websocket to softkey (update Queue List)
#     wssendql(tickett.branch.bcode , tickett.countertype.name, tickett, 'del')
#     # websocket to web tv
#     wssendwebtv(tickett.branch, tickett.countertype)
#     # websocket to Display Panel waiting number update
#     wssenddispwait(tickett.branch, tickett.countertype, tickett)
#     # websocket to web my ticket
#     wsSendTicketStatus(tickett.branch.bcode, tickett.tickettype, tickett.ticketnumber, tickett.securitycode)




def logcounterlogout (user, countertype, counternumber, logintime, logouttime) -> str :
    sOut = 'Error'

    obj = CounterLoginLog.objects.filter( Q(user=user) & Q(countertype=countertype)  & Q(counternumber=counternumber)  & Q(logintime=logintime) )
    if not(obj.count() > 0) :
        sOut = 'Counter Login Log not find ... Username:' + user.username + ',Counter:' + countertype.name + ',Counter#:' + str(counternumber) + ',Login time:' + str(logintime)
    else :        
        loginlog = obj[0]
        loginlog.logouttime = logouttime
        loginlog.save()
        sOut = 'OK'

    if countertype.countermode == 'cc':
        obj = UserStatusLog.objects.filter( Q(user=user) & Q(endtime=None) )
        for usl in obj:
            usl.endtime = logouttime
            usl.save()

    return sOut

def logcounterlogin (user, countertype, counternumber, logintime) :

    CounterLoginLog.objects.create(
            countertype=countertype,
            counternumber = counternumber ,
            user = user,
            logintime = logintime,
        )
    
    if countertype.countermode == 'cc':
        # Call centre mode : login counter status is AUX
        UserStatusLog.objects.create(
        user = user,
        starttime = logintime,
        status = lcounterstatus[lcounterstatus.index('login')],
        )
        UserStatusLog.objects.create(
        user = user,
        starttime = logintime,
        status = lcounterstatus[lcounterstatus.index('AUX')],
        )

def cc_autocall(countertype, rx_app, rx_version, datetime_now):
    # auto send ticket to counters
    called = False

    def fun(cs, called, k,):
        if cs.status == lcounterstatus[lcounterstatus.index('ready')] :
            # counter is ready
            user = cs.user
            branch = cs.countertype.branch
            logtext = 'CallCentre mode - Auto call '
            status, msg, context_call = cc_ready(user, branch, countertype, cs, logtext, rx_app, rx_version, datetime_now)
            if status['status'] == 'OK' and context_call != {'data': {}} :
                # counter is calling a ticket 
                called = True
                new_i = k + 1
                if new_i >= objcs.count():
                    new_i = 0
                countertype.nextcounter = new_i
                countertype.save()
            elif status['status'] == 'OK' and context_call == {'data': {}} :
                # no ticket to call
                pass
            else:
                # error
                pass
        return called

    objcs = CounterStatus.objects.filter(Q(countertype=countertype) & Q(enabled=True)).order_by('counternumber')

    i = countertype.nextcounter
    for k in range(i, objcs.count()):
        
        cs = objcs[k]
        called = fun(cs, called, k)
        if called == True :            
            break
    if called == False :
        if i > 0 :
            for k in range(0, i):
                cs = objcs[k]
                called = fun(cs, called, k)
                if called == True :
                    break
    # # for debug
    # if called == True :
    #     print('Auto call : ' + str(k))
    #     print('Counter:' + cs.counternumber)
    #     print('Next counter = ' + str(countertype.nextcounter))
        


def cc_ready(user, branch, countertype, counterstatus, logtext, rx_app, rx_version, datetime_now):
    # Softkey pass 'Ready' button

    # if counter status is 'processing' then complete the ticket
    if counterstatus.status == lcounterstatus[lcounterstatus.index('processing')] :
        status, msg = funCounterComplete(user, branch, countertype, counterstatus, 'Ticket completed by SK:Ready ', rx_app, rx_version, datetime_now)
        logger.warning('cc_ready status = ' + str(status) + ' msg = ' + str(msg))
        
    if counterstatus.status == lcounterstatus[lcounterstatus.index('ACW')] :
        counterstatus.tickettemp = None

    # user status log for end last status
    objusl = UserStatusLog.objects.filter( Q(user=user) & Q(endtime=None) & Q(status=counterstatus.status) )
    if objusl.count() > 0 :
        for usl in objusl:
            usl.endtime = datetime_now
            usl.save()
    
    # change status to ready first
    counterstatus.status = lcounterstatus[lcounterstatus.index('ready')]
    counterstatus.save()
    # websocket to web softkey for update counter status
    wscounterstatus(counterstatus)

    # add user status log 'ready' status
    objusl = UserStatusLog.objects.filter( Q(user=user) & Q(endtime=None) & Q(status=lcounterstatus[lcounterstatus.index('ready')]) )
    if objusl.count() == 0 :
        UserStatusLog.objects.create(
            user = user,
            starttime = datetime_now,
            status = lcounterstatus[lcounterstatus.index('ready')],
        )


    # old version no database lock may be cause double call
    ############### modify funCounterCall function from only accept 'waiting' to accept 'waiting' and 'ready'
    # status, msg, context_call = funCounterCall(user, branch, countertype, counterstatus, logtext, rx_app, rx_version, datetime_now)
    # new version with database lock
    for i in range(0, 10):
        status, msg, context_call = funCounterCall_v840(user, branch, countertype, counterstatus, logtext, rx_app, rx_version, datetime_now)
        if status['status'] == 'OK':
            break
        else:
            error = msg['msg']
            from base.a_global import str_db_locked
            if error == str_db_locked:
                logger.warning('Database is locked. Retry ' + str(i + 1) + ' times.')
                time.sleep(0.05)
            else:
                break
    
    logger.warning('cc_ready status = ' + str(status) + ' msg = ' + str(msg) + ' context_call = ' + str(context_call))
    if status['status'] == 'OK' and context_call != {'data': {}} :
        # counter is calling a ticket 
        # add user status log 'walking' status
        UserStatusLog.objects.create(
            user = user,
            starttime = datetime_now,
            status = lcounterstatus[lcounterstatus.index('walking')],
        )
    elif status['status'] == 'OK' and context_call == {'data': {}} :
        # no ticket to call 
        # add user status log 'waiting' status
        UserStatusLog.objects.create(
            user = user,
            starttime = datetime_now,
            status = lcounterstatus[lcounterstatus.index('waiting')],
        )  
    return status, msg, context_call

def cc_aux(user, branch, countertype, counterstatus, logtext, rx_app, rx_version, datetime_now):
    if counterstatus.status == lcounterstatus[lcounterstatus.index('ACW')] :
        # user status log for ACW status
        objusl = UserStatusLog.objects.filter( Q(user=user) & Q(endtime=None) & Q(status=lcounterstatus[lcounterstatus.index('ACW')]) )
        if objusl.count() > 0 :
            for usl in objusl:
                usl.endtime = datetime_now
                usl.save()
        
        # When counter have ticket with ACW status then remove it
        if counterstatus.tickettemp != None:
            ticket = counterstatus.tickettemp
            # add ticketlog
            localdate_tickettime = funUTCtoLocal(ticket.tickettime, branch.timezone)
            TicketLog.objects.create(
                tickettemp=ticket,
                logtime=datetime_now,
                app = rx_app,
                version = rx_version,
                logtext='ACW completed by SK:AUX '  + branch.bcode + '_' + ticket.tickettype + '_'+ ticket.ticketnumber + '_' + localdate_tickettime.strftime('%Y-%m-%d_%H:%M:%S') ,
                user=user,
            )
            counterstatus.tickettemp = None
            counterstatus.save()
        
    elif counterstatus.status == lcounterstatus[lcounterstatus.index('ready')] :
        # user status log for ready status
        objusl = UserStatusLog.objects.filter( Q(user=user) & Q(endtime=None) & Q(status=lcounterstatus[lcounterstatus.index('ready')]) )
        if objusl.count() > 0 :
            for usl in objusl:
                usl.endtime = datetime_now
                usl.save()  
    elif counterstatus.status == lcounterstatus[lcounterstatus.index('processing')] :
        status, msg = funCounterComplete(user, branch, countertype, counterstatus, 'Ticket completed by SK:AUX ', rx_app, rx_version, datetime_now)

    # change status to AUX
    counterstatus.status = lcounterstatus[lcounterstatus.index('AUX')]
    counterstatus.save()
    # add user status log 'walking' status
    UserStatusLog.objects.create(
        user = user,
        starttime = datetime_now,
        status = lcounterstatus[lcounterstatus.index('AUX')],
    )
    # websocket to web softkey for update counter status
    wscounterstatus(counterstatus)

def cc_acw(user, branch, countertype, counterstatus, logtext, rx_app, rx_version, datetime_now):
    if counterstatus.status == lcounterstatus[lcounterstatus.index('AUX')] :
        # user status log for AUX status
        objusl = UserStatusLog.objects.filter( Q(user=user) & Q(endtime=None) & Q(status=lcounterstatus[lcounterstatus.index('AUX')]) )
        if objusl.count() > 0 :
            for usl in objusl:
                usl.endtime = datetime_now
                usl.save()         
    if counterstatus.status == lcounterstatus[lcounterstatus.index('ready')] :
        # user status log for ready status
        objusl = UserStatusLog.objects.filter( Q(user=user) & Q(endtime=None) & Q(status=lcounterstatus[lcounterstatus.index('ready')]) )
        if objusl.count() > 0 :
            for usl in objusl:
                usl.endtime = datetime_now
                usl.save()  

    # if counter status is 'processing' then complete the ticket
    ticket = None
    tticket = None
    if counterstatus.status == lcounterstatus[lcounterstatus.index('processing')] :
        tticket = counterstatus.tickettemp
        ticket = counterstatus.tickettemp.ticket
        status, msg = funCounterComplete(user, branch, countertype, counterstatus, 'Ticket completed by SK:ACW ', rx_app, rx_version, datetime_now)
        # counter status add ticket back
        counterstatus.tickettemp = tticket
        counterstatus.save()

        # add 
    # change status to ACW
    counterstatus.status = lcounterstatus[lcounterstatus.index('ACW')]
    counterstatus.save()
    # add user status log 'ACW' status
    UserStatusLog.objects.create(
        user = user,
        starttime = datetime_now,
        status = lcounterstatus[lcounterstatus.index('ACW')],
        ticket = ticket,
    )
    # websocket to web softkey for update counter status
    wscounterstatus(counterstatus)