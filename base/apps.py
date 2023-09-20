from django.apps import AppConfig
from base.sch.jobs import  job_stopall, job_testing
import logging
# from base.sch.views import job_testing


logger = logging.getLogger(__name__)



class BaseConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'base'
    
    def ready(self) -> None:
        logger.info('   *** Queuing System Started ***')

        # job_testing(1, '1 Seconds', ' 0')
        # job_testing(10, '10 Seconds', ' |')      

        # job_stop('job_1 Seconds')  
        # job_stop('job_4 Seconds')  
        # job_stopall()
        
        return super().ready()
