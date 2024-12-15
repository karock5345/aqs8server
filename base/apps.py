from django.apps import AppConfig
from django.db.utils import OperationalError

force_migrations = False  # Set to True Force the system is not inited

class BaseConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'base'

    def ready(self) -> None:
        from base.sch.jobs import  job_stopall, job_testing, job_delStartupFlag
        import logging
        from base.models import StartupFlag
        from base.sch.views import sch

        from base.models import StartupFlag
        # Optionally delete the flag at the end of the method
        # StartupFlag.objects.all().delete()
        # print('--- Deleted StartupFlag ---')

        # remove all jobs
        # sch.remove_all_jobs()
        # job_testing(3, '3 Seconds', ' 0')
        # job_testing(10, '10 Seconds', ' |')      
        # job_stop('job_        1 Seconds')  
        # job_stop('job_4 Seconds')  
        # job_stopall()        
        job_delStartupFlag()
        sch.start()


        # Check if the startup code has already run
        logger = logging.getLogger(__name__)


        try:
            if not StartupFlag.objects.filter(has_run=True).exists():        
                # Set the flag to indicate that the startup code has run
                StartupFlag.objects.create(has_run=True)
                # Run your startup code here
                logger.info('   *** Queuing System Started ***')
                sub_init()
        except OperationalError:
            # Handle the case where the database is not ready yet
            logger.warning('Database is not ready yet. Startup code will not run.')
        
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

