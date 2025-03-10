from django.apps import AppConfig
from django.db.utils import OperationalError
from django.db import transaction
from aqs.settings import FORCE_MIGRATIOINS

class BaseConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'base'

    def ready(self) -> None:
        from base.sch.jobs import  job_stopall, job_testing, job_delStartupFlag
        import logging
        from base.sch.views import sch
      
        logger = logging.getLogger(__name__)
        # Check if the system is inited or not        
        if FORCE_MIGRATIOINS == True:
            logger.info('   ------ Force Migrations on ------')
            return super().ready()
        
        sch.start()

        job_init()

        # remove all jobs
        # sch.remove_all_jobs()
        # job_testing(3, '3 Seconds', ' 0')
        # job_testing(10, '10 Seconds', ' |')      
        # job_stop('job_        1 Seconds')  
        # job_stop('job_4 Seconds')  
        # job_stopall()
        return super().ready()
    
job_init_id = 'job_init'
def job_init():
    from base.sch.views import sch

    sch.add_job(_init, 'interval' , seconds=1, id=job_init_id)

@transaction.atomic
def _init():
    from base.models import StartupFlag
    from base.sch.views import sch
    from base.sch.jobs import  job_stopall, job_testing, job_delStartupFlag
    import base.a_global 
    from base.sch.views import sch_bookingtemp, sub_booking_temp, init_branch_reset, check_pending_migrations
    from datetime import datetime, timezone
    from base.models import SystemLog
    import logging
    logger = logging.getLogger(__name__)
 
    logger.info('--- Starting Init ---')
    # remove job_init_id
    sch.remove_job(job_init_id)

    datetime_now = datetime.now(timezone.utc)
    now = datetime.now(timezone.utc)

    # Check if the startup code has already run
    try:
        sf = StartupFlag.objects.select_for_update(nowait=True).filter(has_run=True).first()
    except:
        logger.info('   ------ Force Migrations on ------')
        return None
    if sf is None:
        StartupFlag.objects.create(has_run=True, worker=0)
        sf = StartupFlag.objects.select_for_update().filter(has_run=True).first()

    now = datetime.now(timezone.utc)
    seconds = (now - sf.updated).total_seconds() 

    if sf.worker > 0 and seconds > 30:
        # check the sf timestamp
        # set worker to 1
        sf.worker = 1
        sf.save()
        logger.info('Diff seconds (now and update): ' + str(seconds) + 'seconds. Set worker to 1')
    else:
        sf.worker = sf.worker + 1
        logger.info(f'Worker {sf.worker} started' )
        sf.save()
    if sf.worker == 1:
        # Run your startup code here
        logger.info('   *** Queuing System Started ***')
        job_delStartupFlag()

        logger.info('-SCH- Schedule INIT start @ base.sch.view.py -SCH-')

        snow = now.strftime("%m/%d/%Y, %H:%M:%S")
        logger.info('-SCH- Now:' + snow)

        # check pending migrations
        migrations_needed, error = check_pending_migrations()
        if error == '' :
            if migrations_needed == True:
                logger.info('-SCH- Migrations are needed')
            else:
                logger.info('-SCH- No migrations are needed')

        if error != '':
            logger.info('-SCH- Error : ' + error)

        if error == '' :
            try:
                SystemLog.objects.create(
                        logtime=datetime_now,
                        logtext =  'System inited',
                    )
                base.a_global.system_inited = True
            except:
                base.a_global.system_inited = False
                logger.info('-SCH- System not inited -SCH-')

            if base.a_global.system_inited == True and migrations_needed == False and FORCE_MIGRATIOINS == False:
                # Scheduler 6 hours run sch_bookingtemp
                sch_bookingtemp(6)
                sub_booking_temp(None, None)

                init_branch_reset()        