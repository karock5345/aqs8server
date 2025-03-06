from django.apps import AppConfig
from django.db.utils import OperationalError
from django.db import transaction

# Set to True Force the system is not inited
force_migrations = False

class BaseConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'base'

    @transaction.atomic
    def ready(self) -> None:
        from base.sch.jobs import  job_stopall, job_testing, job_delStartupFlag
        import logging
        from base.models import StartupFlag
        from base.sch.views import sch
        from datetime import datetime, timezone
      
        logger = logging.getLogger(__name__)
        # Check if the system is inited or not        
        if force_migrations == True:
            logger.info('   *** Force Migrations on ***')
            return super().ready()
               
        # Check if the startup code has already run
        try:
            sf = StartupFlag.objects.select_for_update().filter(has_run=True).first()
        except:
            logger.info('   *** Force Migrations on ***')
            return super().ready()
        if sf is None:
            StartupFlag.objects.create(has_run=True, worker=0)
            sf = StartupFlag.objects.select_for_update().filter(has_run=True).first()

        sch.start()

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
            sf.save()
        if sf.worker == 1:
            # Run your startup code here
            logger.info('   *** Queuing System Started ***')
            sub_init()
            job_delStartupFlag()

            # remove all jobs
            # sch.remove_all_jobs()
            # job_testing(3, '3 Seconds', ' 0')
            # job_testing(10, '10 Seconds', ' |')      
            # job_stop('job_        1 Seconds')  
            # job_stop('job_4 Seconds')  
            # job_stopall()
        return super().ready()
    
def sub_init():
    import base.a_global 
    from base.sch.views import sch_bookingtemp, sub_booking_temp, init_branch_reset, check_pending_migrations
    from datetime import datetime, timezone
    from base.models import SystemLog
    import logging

    # global system_inited

    logger = logging.getLogger(__name__)

    datetime_now = datetime.now(timezone.utc)
    now = datetime.now(timezone.utc)
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

        if base.a_global.system_inited == True and migrations_needed == False and force_migrations == False:

            # Scheduler 6 hours run sch_bookingtemp
            sch_bookingtemp(6)
            sub_booking_temp(None, None)

            init_branch_reset()

