from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
import logging

logger = logging.getLogger(__name__)

# from .views import job_shutdown

sch = BackgroundScheduler()
sch.start()

# def job_branch(branch):
#     print('--- Start job branch_reset:' + branch +  ' ---')

#     pass


def job_testing(input, text, text2):
    txt_job = 'job_' + text
    sch.add_job(job, 'interval', args=[text,text2], seconds=input, id=txt_job)

    # time.sleep(15)
    # job2()
    

def job(text,text2):    
    now = datetime.now()
    snow = now.strftime("%m/%d/%Y, %H:%M:%S")
    text_out = '---' +  snow + ' Testing job - ' + text + text2 + '---'

    print ( text_out )    
    pass

# def job_stop(job):
#     print('--- Stop testing job here' + job +  ' ---')
#     sch.remove_job(job)

def job_stopall():
    logger.info('--- Stop all jobs ---')

    # sch.shutdown()

