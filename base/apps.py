from django.apps import AppConfig


force_migrations = False  # Set to True Force the system is not inited

class BaseConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'base'

    def ready(self) -> None:
        from base.sch.jobs import  job_stopall, job_testing
        import logging

        logger = logging.getLogger(__name__)
        logger.info('   *** Queuing System Started ***')
        
        sub_init()

        # job_testing(1, '1 Seconds', ' 0')
        # job_testing(10, '10 Seconds', ' |')      

        # job_stop('job_1 Seconds')  
        # job_stop('job_4 Seconds')  
        # job_stopall()
        
        return super().ready()
    
def sub_init():
    import base.a_global 
    from base.sch.views import sch_bookingtemp, sub_booking_temp, init_branch_reset, sch, check_pending_migrations
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
                    logtext =  'System started',
                )
            base.a_global.system_inited = True
        except:
            base.a_global.system_inited = False
            logger.info('-SCH- System not inited -SCH-')

        if base.a_global.system_inited == True and migrations_needed == False and force_migrations == False:
            sch.start()
            # Scheduler 6 hours run sch_bookingtemp
            sch_bookingtemp(6)
            sub_booking_temp(None, None)

            init_branch_reset()  

