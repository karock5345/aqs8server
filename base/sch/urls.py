from django.urls import path
from . import views
from base.sch.views import job_testing, init_branch_reset, job_testWS
#from base.api.views import funUTCtoLocaltime

urlpatterns = [
    path('', views.getRoutes),
    path('test/', views.getJobTesting),
]

# job_testing(10, '10 Seconds', ' 0')
# job_testing('WS Test send (1-100)')
job_testWS('WS Test send (1-100)')

init_branch_reset()