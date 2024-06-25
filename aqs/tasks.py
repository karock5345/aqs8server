# aqs/tasks.py
from datetime import timedelta
import os
from celery import shared_task
import csv
from django.http import HttpResponse
from django.utils import timezone
from base.api.views import funUTCtoLocal, funLocaltoUTC, funUTCtoLocaltime, funLocaltoUTCtime
import pickle
from base.models import TicketData, TicketFormat, Ticket, Branch, UserStatusLog, TicketLog
from booking.models import SMS_Log
from django.contrib.auth.models import User
from django.db.models import Q
import logging
# from celery import Celery
# app = Celery()
from django.conf import settings
# from django.core.mail import send_mail
from django.core.mail import EmailMessage
import requests
from django.http import JsonResponse
import time
logger = logging.getLogger(__name__)





@shared_task(bind = True,)
def sendSMS(self, tophone, message, bcode, msg_for):

    error = ''
    output = ''
    branch = None

    if error == '' :
        if tophone == '':
            error = 'No phone number'
    if error == '' :
        if message == '':
            error = 'No message'
    if error == '' :
        if bcode == '':
            error = 'No branch code'
    if error == '' :
        branch = Branch.objects.get(bcode=bcode)
        if branch == None:
            error = 'Branch not found'

    if error == '':
        # get the message length and check how many SMS will be sent
        # Max. is 160 characters / 70 characters (Unicode) per SMS
        lenpersms = 70
        if message.isascii() == True:
            lenpersms = 160
        # get the message length
        lenmessage = len(message) - 1
        # get the number of SMS
        numsms = int(lenmessage / lenpersms) + 1
        
        # check SMS quota
        used = branch.SMSUsed + numsms
        if used > branch.SMSQuota:
            error = 'SMS Quota exceeded'

                                
    if error != '':
        output = error
        # save error to DB
        SMS_Log.objects.create(
            branch = branch,
            phone = tophone,
            sent = False,
            msg_for = msg_for,
        )



    if error == '':
        # SMS provider: UFO
        url = 'https://api3.ufosend.com/v3.0/sms_connect.php?'
    
        url += 'account_name=' + settings.SMS_ACCOUNT_NAME
        url += '&api_key=' + settings.SMS_API_KEY
        url += '&sender=' + settings.SMS_SENDER
        url += '&mobile=' + tophone
        url += '&sms_content=' + message

        response = requests.get(url)

        # response converted to json
        json = response.json()
        try:
            # get the 'ref' from json
            ref = json['ref']
        except:
            pass
        try:
            # get the 'status' from json
            status = json['status']
        except:
            pass
        try:            
            # get ret
            return_code = json['return_code']
        except:
            pass
        try:
            test = json['test']
        except:
            pass
        # logger.info(f'SMS sent to: {tophone} ref: {ref} status: {status} return_code: {return_code}')

        output = response.text


        if status == 1 and return_code == 100 :
            # Success
            branch.SMSUsed = branch.SMSUsed + numsms
            branch.save()
        # save to DB
        SMS_Log.objects.create(
            branch = branch,
            phone = tophone,
            sent = True,
            numSMS = numsms,
            ref = ref,
            status = status,
            return_code = return_code,
            msg_for = msg_for,
        )
    return output

@shared_task(bind=True)
def sendemail(self, subject, message, toemail):

    email = EmailMessage(
        subject,
        message,
        from_email=settings.EMAIL_HOST_USER,
        to=[toemail],
        # cc=['elton@tsvd.com.hk'],
        # bcc=['sales@tsvd.com.hk'],
        reply_to=['sales@tsvd.com.hk'],
    )
    email.content_subtype = "html"
    email.fail_silently = True

    # task_id = self.request.id
    # task_name = self.name
    # logger.info(f'Email sending To: {toemail}')
    result = email.send()
    # logger.info(f'Email sent To: {toemail} Result: {result}')
    # logger.info(f'Email sending Task id: {task_id} Task name: {task_name} To: {toemail}')

    return 'Email sent'

@shared_task
def long_running_task():
    # Perform the long-running task here and update the progress as needed
    # You can store the progress in a database or cache

    # For demonstration purposes, let's assume the task runs for 10 seconds
    import time
    for i in range(1, 11):
        time.sleep(1)
        # Update progress here
        progress = i * 10
        # Store the progress in Redis, database, or cache for later retrieval
        # (we'll simulate this by printing the progress here)
        print(f"Progress: {progress}%")

    # Return the final result (optional)
    return "Long-running task completed!"

@shared_task
def export_raw(quesrystr, reporttitle1, reporttitle2, reporttitle3, reporttitle4, reporttitle5, bcode ):
    from celery import  current_task


    report_str = ''
    # Get my task ID
    my_id = current_task.request.id
    logger.info(f'Exporting raw data task id: {my_id}')

    # Get settings.py STATIC_ROOT
    static_root = None
    if settings.STATIC_ROOT != None:
        # This is for production
        static_root = str(settings.STATIC_ROOT)
    if static_root == None:
        # This is for development
        static_root = str(settings.STATICFILES_DIRS[0])
    # logger.info(f'Static Root: {static_root}')



    current_task.status = 'PROGRESS'

    per = -1

    # Restore the queryset convert table (list) to DataManager[TicketData]
    table = TicketData.objects.all() 
    table.query = pickle.loads(quesrystr)

    # table convert to csv
    # response = HttpResponse(content_type='text/csv')
    # response['Content-Disposition'] = 'attachment; filename="raw.csv"'
    # writer = csv.writer(response)                
    # add table header
    # writer.writerow(['Ticket', 'Branch', 'Counter Type', 'Step', 'Start Time', 'Start by', 'Call Time', 'Call by', 'Process Time', 'Process by', 'Done Time', 'Done by', 'No Show Time', 'No Show by', 'Void Time', 'Void by', 'Waiting Time (s)', 'Walking time (s)', 'Process time (s)', 'Total time (s)'])
    
    # get branch code
    #bcode = table[0].branch.bcode
    # get django static path
    save_path = static_root + '/download/' + bcode + '/raw_' + my_id +'.csv'
    logger.info(f'Full path of save file: {save_path}')

    # create new folder if not exist
    # Directory 
    newdir = 'download'               
    # Path 
    path = os.path.join(static_root, newdir) 
    try:
        os.mkdir(path)
    except:
        # logger.error('Error new "download" folder')
        pass

    # Directory 
    newdir = bcode           
    # Path 
    path = os.path.join(static_root + '/download/', newdir) 
    try:
        os.mkdir(path)
    except:
        # logger.error('Error new "bcode" folder')
        pass

    

    i = 0
    for row in table:
        i += 1
        newper = int(i/ len(table) * 100)
        if newper != per:
            per = newper
            # Set the progress in the task's state (for WebSocket consumer)
            current_task.update_state(state='PROGRESS', meta={'progress': per})
            # logger.info(f'Exporting raw data {per}%')

        starttime = None
        if row.starttime != None:
            starttime = funUTCtoLocal(row.starttime, row.branch.timezone).strftime('%Y-%m-%d %H:%M:%S')
        calltime = None
        if row.calltime != None:                        
            calltime = funUTCtoLocal(row.calltime, row.branch.timezone).strftime('%Y-%m-%d %H:%M:%S')
        processtime = None
        if row.processtime != None:
            processtime = funUTCtoLocal(row.processtime, row.branch.timezone).strftime('%Y-%m-%d %H:%M:%S')
        donetime = None
        if row.donetime != None:
            donetime = funUTCtoLocal(row.donetime, row.branch.timezone).strftime('%Y-%m-%d %H:%M:%S')
        misstime = None
        if row.misstime != None:
            misstime = funUTCtoLocal(row.misstime, row.branch.timezone).strftime('%Y-%m-%d %H:%M:%S')
        voidtime = None
        if row.voidtime != None:
            voidtime = funUTCtoLocal(row.voidtime, row.branch.timezone).strftime('%Y-%m-%d %H:%M:%S')

        # save data row to report_str for CSV format
        report_str += f'{row.ticket.tickettype}{row.ticket.ticketnumber},{row.ticket.tickettype},{row.ticket.ticketnumber},{row.branch.bcode},{row.countertype.name},{row.step},{starttime},{row.startuser},{calltime},{row.calluser},{processtime},{row.processuser},{donetime},{row.doneuser},{misstime},{row.missuser},{voidtime},{row.voiduser},{row.waitingperiod},{row.walkingperiod},{row.processingperiod},{row.totalperiod}\n'


        # writer.writerow([
        #                 row.ticket.tickettype + row.ticket.ticketnumber,  
        #                 row.branch.bcode,
        #                 row.countertype.name,
        #                 row.step,
        #                 starttime,
        #                 row.startuser,
        #                 calltime,
        #                 row.calluser,
        #                 processtime,
        #                 row.processuser,
        #                 donetime,
        #                 row.doneuser,
        #                 misstime,
        #                 row.missuser,
        #                 voidtime,
        #                 row.voiduser,
        #                 row.waitingperiod,
        #                 row.walkingperiod,
        #                 row.processingperiod,
        #                 row.totalperiod,
        #                     ])


        

    # save report_str to save_path    
    with open(save_path, 'w') as f:
        # add report title
        f.write(reporttitle1 + '\n')
        f.write(reporttitle2 + '\n')
        f.write(reporttitle3 + '\n')
        f.write(reporttitle4 + '\n')
        f.write(reporttitle5 + '\n')        

        # add table header
        # writer.writerow(['Ticket', 'Branch', 'Counter Type', 'Step', 'Start Time', 'Start by', 'Call Time', 'Call by', 'Process Time', 'Process by', 'Done Time', 'Done by', 'No Show Time', 'No Show by', 'Void Time', 'Void by', 'Waiting Time (s)', 'Walking time (s)', 'Process time (s)', 'Total time (s)']                
        f.write('Ticket,Type,No.,Branch,Counter Type,Step,Start Time,Start by,Call Time,Call by,Process Time,Process by,Done Time,Done by,No Show Time,No Show by,Void Time,Void by,Waiting Time (s),Walking time (s),Process time (s),Total time (s)\n')
        f.write(report_str)
    f.close()

    # with open(fstatic_path'static/download/{row.branch.bcode}/raw.csv', 'w') as f:
    
    
    current_task.status = 'SUCCESS'



    return current_task.status

@shared_task
def export_report(quesrystr, report_text, bcode , filename):
    from celery import current_task

    report_str = ''
    # Get my task ID
    my_id = current_task.request.id
    logger.info('Exporting report({filename}) task id: {my_id}')

    # Get settings.py STATIC_ROOT
    static_root = None
    if settings.STATIC_ROOT != None:
        # This is for production
        static_root = str(settings.STATIC_ROOT)
    if static_root == None:
        # This is for development
        static_root = str(settings.STATICFILES_DIRS[0])
    # logger.info(f'Static Root: {static_root}')

    current_task.status = 'PROGRESS'

    per = -1

    # Restore the queryset convert table (list) to DataManager[TicketData]
    # table = TicketData.objects.all() 
    # table.query = pickle.loads(quesrystr)

    # table convert to csv
    # response = HttpResponse(content_type='text/csv')
    # response['Content-Disposition'] = 'attachment; filename="raw.csv"'
    # writer = csv.writer(response)                
    # add table header
    # writer.writerow(['Ticket', 'Branch', 'Counter Type', 'Step', 'Start Time', 'Start by', 'Call Time', 'Call by', 'Process Time', 'Process by', 'Done Time', 'Done by', 'No Show Time', 'No Show by', 'Void Time', 'Void by', 'Waiting Time (s)', 'Walking time (s)', 'Process time (s)', 'Total time (s)'])
    
    # get branch code
    #bcode = table[0].branch.bcode
    # get django static path
    save_path = static_root + '/download/' + bcode + '/' + filename
    logger.info(f'Full path of save file: {save_path}')

    # create new folder if not exist
    # Directory 
    newdir = 'download'               
    # Path 
    path = os.path.join(static_root, newdir) 
    try:
        os.mkdir(path)
    except:
        # logger.error('Error new "download" folder')
        pass

    # Directory 
    newdir = bcode           
    # Path 
    path = os.path.join(static_root + '/download/', newdir) 
    try:
        os.mkdir(path)
    except:
        # logger.error('Error new "bcode" folder')
        pass

    

    i = 0
    for row in quesrystr:
        i += 1
        newper = int(i/ len(quesrystr) * 100)
        if newper != per:
            per = newper
            # Set the progress in the task's state (for WebSocket consumer)
            current_task.update_state(state='PROGRESS', meta={'progress': per})
            # logger.info(f'Exporting raw data {per}%')

        line_str = ''
        for item in row:
            line_str += str(item) + ','
        report_str += line_str + '\n'

    # save report_str to save_path    
    with open(save_path, 'w') as f:
        # add report title
        f.write(report_text + '\n')

        # add table header
        # writer.writerow(['Ticket', 'Branch', 'Counter Type', 'Step', 'Start Time', 'Start by', 'Call Time', 'Call by', 'Process Time', 'Process by', 'Done Time', 'Done by', 'No Show Time', 'No Show by', 'Void Time', 'Void by', 'Waiting Time (s)', 'Walking time (s)', 'Process time (s)', 'Total time (s)']                
        f.write(report_str)
    f.close()

    # with open(fstatic_path'static/download/{row.branch.bcode}/raw.csv', 'w') as f:
    
    
    current_task.status = 'SUCCESS'



    return current_task.status

@shared_task
def report_ticket(branch_id, ticketformat_id, startdate, enddate):
    from celery import current_task
    # Get my task ID
    my_id = current_task.request.id
    
    current_task.status = 'PROGRESS'
    current_task.table = []

    per = -1

    ticketformat = None
    if ticketformat_id != '':
        ticketformat = TicketFormat.objects.get(id=int(ticketformat_id))
    branch = Branch.objects.get(pk=(branch_id))
    
    report_table = []
    if ticketformat == None  :
        # tfobj = TicketFormat.objects.filter(branch=branch)
        slist = 'A,B,C,D,E,F,G,H,I,J,K,L,M,N,O,P,Q,R,S,T,U,V,W,X,Y,Z'
        # slist = 'A,B,C'
        tlist = slist.split(',')

        i = 0
        for ttype1 in tlist:
            for ttype2 in tlist:
                i += 1                
                newper = int(i/ (26 * 26) * 100)
                if newper != per:
                    per = newper
                    # Set the progress in the task's state (for WebSocket consumer)
                    current_task.update_state(state='PROGRESS', meta={'progress': per})


                ttype = ttype1 + ttype2
                # for tf in tfobj:  
                # ttype = tf.ttype
                # ttype in report_table?
                # found = False
                # for row in report_table:
                #     if row[0] == ttype:
                #         found = True
                #         break
                # if found == False:
                ticketobj = Ticket.objects.filter(
                    Q(branch=branch),
                    Q(tickettime__range=[startdate,enddate]),
                    Q(tickettype=ttype),                        
                    )
                total = ticketobj.count()
                ticketobj = Ticket.objects.filter(
                    Q(branch=branch),
                    Q(tickettime__range=[startdate,enddate]),
                    Q(tickettype=ttype),
                    Q(status='miss'),
                    )
                miss = ticketobj.count()
                done = total - miss
                if total > 0 :
                    report_table.append([ttype,done,miss,total])
    else:
        # Set the progress in the task's state (for WebSocket consumer)
        per = 30
        current_task.update_state(state='PROGRESS', meta={'progress': per})
        ttype = ticketformat.ttype
        ticketobj = Ticket.objects.filter(
            Q(branch=branch),
            Q(tickettime__range=[startdate,enddate]),
            Q(tickettype=ttype),                        
            )
        
        per = 60
        current_task.update_state(state='PROGRESS', meta={'progress': per})
        total = ticketobj.count()
        ticketobj = Ticket.objects.filter(
            Q(branch=branch),
            Q(tickettime__range=[startdate,enddate]),
            Q(tickettype=ttype),
            Q(status='miss'),
            )
        miss = ticketobj.count()
        done = total - miss
        report_table.append([ttype,done,miss,total])

    current_task.table = report_table
    current_task.status = 'SUCCESS'

    # print('report_table',current_task.table )

    return  current_task.status, current_task.table


@shared_task
def report_staff(selected_user_id, querystr_auth_userlist, startdate, enddate):
    from celery import current_task
    report_table = []

    # Get my task ID
    my_id = current_task.request.id
    
    current_task.status = 'PROGRESS'
    current_task.table = []

    per = -1
    # Restore the queryset convert table (list) to DataManager[TicketData]
    auth_userlist = User.objects.all() 
    auth_userlist.query = pickle.loads(querystr_auth_userlist)

    selected_user = None
    if selected_user_id != '':
        selected_user = User.objects.get(id=int(selected_user_id))          
   

    if selected_user == None  :
        # auth_branchs , auth_userlist, auth_userlist_active, auth_profilelist, auth_ticketformats , auth_routes, auth_countertype = auth_data(request_user)
        
        # total rows of auth_userlist * rows of userlogobj
        userlogobj_all = UserStatusLog.objects.filter(
            Q(starttime__range=[startdate, enddate]),
            ~Q(starttime = None),
            ~Q(endtime = None),
        )
        total = userlogobj_all.count() * len(auth_userlist)        
        i = 0
        for user in auth_userlist:
            userlogobj = UserStatusLog.objects.filter(
                Q(starttime__range=[startdate, enddate]),
                Q(user=user),
                ~Q(starttime = None),
                ~Q(endtime = None),
            )
            login = 0
            ready = 0
            waiting = 0
            walking = 0
            process = 0
            acw = 0
            aux =0
            for ul in userlogobj:
                i += 1                
                newper = int(i/ total * 100)
                if newper != per:
                    per = newper
                    # Set the progress in the task's state (for WebSocket consumer)
                    current_task.update_state(state='PROGRESS', meta={'progress': per})

                seconds = (ul.endtime - ul.starttime).seconds
                if ul.status == 'login':
                    login = login + seconds
                elif ul.status == 'ready':
                    ready = ready + seconds
                elif ul.status == 'waiting':
                    waiting = waiting + seconds
                elif ul.status == 'walking':
                    walking = walking + seconds
                elif ul.status == 'processing':
                    process = process + seconds
                elif ul.status == 'ACW':
                    acw = acw + seconds
                elif ul.status == 'AUX':
                    aux = aux + seconds
            # convert all to '00:00:00' string
            login_s = str(timedelta(seconds=login))
            ready_s = str(timedelta(seconds=ready))
            waiting_s = str(timedelta(seconds=waiting))
            walking_s = str(timedelta(seconds=walking))
            process_s = str(timedelta(seconds=process))
            acw_s = str(timedelta(seconds=acw))
            aux_s = str(timedelta(seconds=aux))

            report_table.append([user.username, user.first_name + ' ' + user.last_name, login_s, ready_s, waiting_s, walking_s, process_s, acw_s, aux_s])


    else:
        userlogobj = UserStatusLog.objects.filter(
            Q(starttime__range=[startdate,enddate]),
            Q(user=selected_user),
            ~Q(starttime = None),
            ~Q(endtime = None),
        )
        login = 0
        ready = 0
        waiting = 0
        walking = 0
        process = 0
        acw = 0
        aux =0
        total = userlogobj.count()       
        i = 0
        for ul in userlogobj:
            i += 1                
            newper = int(i/ total * 100)
            if newper != per:
                per = newper
                # Set the progress in the task's state (for WebSocket consumer)
                current_task.update_state(state='PROGRESS', meta={'progress': per})

            seconds = (ul.endtime - ul.starttime).seconds
            if ul.status == 'login':
                login = login + seconds
            elif ul.status == 'ready':
                ready = ready + seconds
            elif ul.status == 'waiting':
                waiting = waiting + seconds
            elif ul.status == 'walking':
                walking = walking + seconds
            elif ul.status == 'processing':
                process = process + seconds
            elif ul.status == 'ACW':
                acw = acw + seconds
            elif ul.status == 'AUX':
                aux = aux + seconds
        # convert all to '00:00:00' string
        login_s = str(timedelta(seconds=login))
        ready_s = str(timedelta(seconds=ready))
        waiting_s = str(timedelta(seconds=waiting))
        walking_s = str(timedelta(seconds=walking))
        process_s = str(timedelta(seconds=process))
        acw_s = str(timedelta(seconds=acw))
        aux_s = str(timedelta(seconds=aux))

        report_table.append([selected_user.username, selected_user.first_name + ' ' + selected_user.last_name, login_s, ready_s, waiting_s, walking_s, process_s, acw_s, aux_s])
    
    current_task.table = report_table
    current_task.status = 'SUCCESS'

    # print('report_table',current_task.table )

    return  current_task.status, current_task.table


@shared_task
def report_ticketdetails(ticket_id,  ):
    from celery import current_task
    report_table = []
    error = ''

    # Get my task ID
    my_id = current_task.request.id
    
    current_task.status = 'PROGRESS'
    current_task.table = []
    count = 0
    per = -1
    # Restore the queryset convert table (list) to DataManager[TicketData]
    # auth_userlist = User.objects.all() 
    # auth_userlist.query = pickle.loads(querystr_auth_userlist)

    if error == '' :
        try:
            ticket = Ticket.objects.get(pk=ticket_id)
        except:
            error = 'Ticket not found'

    per = 0
    current_task.update_state(state='PROGRESS', meta={'progress': per})

    if error == '' :
        table = None
        try:
            # table = TicketLog.objects.filter(ticket=ticket).values('id').order_by('logtime')
            table = TicketLog.objects.filter(ticket=ticket).values('ticket','logtime','logtext','user', 'app','version').order_by('logtime')

        except:
            pass
        
        irow = 0
        for row in table:
            # for test
            # time.sleep(0.3)

            logtime = funUTCtoLocal(row['logtime'], ticket.branch.timezone).strftime('%Y-%m-%d %H:%M:%S')
            tno = ticket.tickettype + ticket.ticketnumber
            user = User.objects.get(pk=row['user'])
            row['user'] = user.first_name + ' ' + user.last_name + ' (' + user.username + ')'
            
            # for i in range(0,100):
            report_table.append([tno, logtime, row['logtext'], row['user'], row['app'], row['version']])
            # report_table.append(['ticket':row['ticket'] , logtime, row['logtext'], row['app'], row['version']])
            
            irow += 1
            newper = int(irow/ len(table) * 100)
            if per != newper:
                current_task.update_state(state='PROGRESS', meta={'progress': newper})
                per = newper
        per = 100
        current_task.update_state(state='PROGRESS', meta={'progress': per})

        # convert table to list (current_task.table)
        # report_table = list(table)
        # header = {'Ticket', 'Log Time', 'Details', 'User', 'App', 'Version'}
        # add header to the first row of report_table
        # report_table.insert(0, header)
        
        current_task.table = report_table
        current_task.status = 'SUCCESS'

        # print('report_table',current_task.table )
        count = 0
        if error == '':
            if table != None:
                count = table.count() 
    
    print('report_table',current_task.table)

    return  current_task.status, current_task.table, count