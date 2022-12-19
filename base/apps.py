from django.apps import AppConfig
from base.sch.jobs import  job_stopall
# from base.sch.views import job_testing

class BaseConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'base'

    def ready(self) -> None:
        print('   *** Queuing System Started ***')

        # job_testing(1, '1 Seconds', ' 0')
        # job_testing(4, '4 Seconds', ' |')      

        # job_stop('job_1 Seconds')  
        # job_stop('job_4 Seconds')  
        # job_stopall()
        
        return super().ready()
