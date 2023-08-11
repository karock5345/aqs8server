# aqs/tasks.py
import os
from celery import shared_task
import csv
from django.http import HttpResponse
from django.utils import timezone
from base.api.views import funUTCtoLocal, funLocaltoUTC, funUTCtoLocaltime, funLocaltoUTCtime
import pickle
from base.models import TicketData
from django.db.models import Q
import logging
# from celery import Celery
# app = Celery()
from django.conf import settings

logger = logging.getLogger(__name__)

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
def export_raw(quesrystr):
    from celery import  current_task
    report_str = ''
    # Get my task ID
    my_id = current_task.request.id

    static_root = str(settings.STATICFILES_DIRS[0])


    logger.info(f'Exporting raw data task id: {my_id}')

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
    bcode = table[0].branch.bcode
    # get django static path
    save_path = static_root + '/download/' + bcode + '/raw_' + my_id +'.csv'
    logger.info(f'Full path of save file: {save_path}')


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
        report_str += f'{row.ticket.tickettype}{row.ticket.ticketnumber},{row.branch.bcode},{row.countertype.name},{row.step},{starttime},{row.startuser},{calltime},{row.calluser},{processtime},{row.processuser},{donetime},{row.doneuser},{misstime},{row.missuser},{voidtime},{row.voiduser},{row.waitingperiod},{row.walkingperiod},{row.processingperiod},{row.totalperiod}\n'


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

    # create new folder if not exist
    # Directory 
    newdir = 'download'               
    # Path 
    path = os.path.join(static_root, newdir) 
    try:
        os.makedirs(path)
    except:
        pass

    # Directory 
    newdir = bcode           
    # Path 
    path = os.path.join(static_root + '/download/', newdir) 
    try:
        os.makedirs(static_root + '/download/' + bcode)
    except:
        pass

        

    # save report_str to save_path    
    with open(save_path, 'w') as f:
        # add table header
        # writer.writerow(['Ticket', 'Branch', 'Counter Type', 'Step', 'Start Time', 'Start by', 'Call Time', 'Call by', 'Process Time', 'Process by', 'Done Time', 'Done by', 'No Show Time', 'No Show by', 'Void Time', 'Void by', 'Waiting Time (s)', 'Walking time (s)', 'Process time (s)', 'Total time (s)'])
        f.write('Ticket,Branch,Counter Type,Step,Start Time,Start by,Call Time,Call by,Process Time,Process by,Done Time,Done by,No Show Time,No Show by,Void Time,Void by,Waiting Time (s),Walking time (s),Process time (s),Total time (s)\n')
        f.write(report_str)
    f.close()

    # with open(fstatic_path'static/download/{row.branch.bcode}/raw.csv', 'w') as f:
    
    
    current_task.status = 'SUCCESS'



    return current_task.status

