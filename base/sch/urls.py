from django.urls import path
from . import views
from base.sch.views import job_testing, init_branch_reset
#from base.api.views import funUTCtoLocaltime

urlpatterns = [
    path('', views.getRoutes),
    path('test/', views.getJobTesting),
    
    # http://127.0.0.1:8000/sch/shutdown/?bcode=KB
    path('shutdown/', views.getShutdown),
]

# job_testing(10, '10 Seconds', ' 0')

init_branch_reset()