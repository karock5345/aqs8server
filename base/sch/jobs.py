from datetime import datetime
# from apscheduler.schedulers.background import BackgroundScheduler
import logging
import time

logger = logging.getLogger(__name__)

# from .views import job_shutdown

# sch = BackgroundScheduler()
# sch.start()

# def job_branch(branch):
#     print('--- Start job branch_reset:' + branch +  ' ---')

#     pass

job_delStartupFlag_id = 'job_delStartupFlag'
def job_delStartupFlag():
    from .views import sch
    sch.add_job(_delStartupFlag, 'interval' , seconds=20, id=job_delStartupFlag_id)
def _delStartupFlag():
    from base.models import StartupFlag
    from .views import sch
    # Optionally delete the flag at the end of the method
    sfobj = StartupFlag.objects.filter(has_run=True)
    for sf in sfobj:
        sf.worker = 0
        sf.save()
    logger.info('--- Deleted StartupFlag ---')
    # remove job_delStartupFlag
    sch.remove_job(job_delStartupFlag_id)
    # sch.add_job(_delStartupFlag, 'interval' , hours=3, id=job_delStartupFlag_id)


def job_testing(input, text, text2):
    from .views import sch

    txt_job = 'job_' + text
    sch.add_job(job, 'interval', args=[text,text2], seconds=input, id=txt_job)


    # job2()
    

def job(text,text2):    
    now = datetime.now()
    snow = now.strftime("%m/%d/%Y, %H:%M:%S")
    text_out = '---' +  snow + ' Testing job - ' + text + text2 + '---'

    time.sleep(0.8)
    print ( text_out )    
    pass

# def job_stop(job):
#     print('--- Stop testing job here' + job +  ' ---')
#     sch.remove_job(job)

def job_stopall():
    logger.info('--- Stop all jobs ---')

    # sch.shutdown()

