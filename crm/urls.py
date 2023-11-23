from django.urls import path

from . import views
from . import api


urlpatterns = [
    # Testing page
    # path('', views.WelcomeView, name='crmhome'),

    # CRM APIs for mobile app
    path('api/login/', api.crmUserLoginView, name='crmlogin'),
    path('api/info/', api.crmMemberInfoView, name='crmmeminfo'),
]