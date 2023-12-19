from django.urls import path

from . import views
from . import api


urlpatterns = [
    # Testing page
    # path('', views.WelcomeView, name='crmhome'),

    # CRM APIs for mobile app
    path('api/login/', api.crmMemberLoginView, name='crmlogin'),
    path('api/info/', api.crmMemberInfoView, name='crmmeminfo'),
    path('api/items/', api.crmMemberItemListView, name='crmmemitemlist'),
    path('api/logout/', api.crmMemberLogoutView, name='crmlogout'),
    path('api/reg/', api.crmMemberRegistrationView, name='crmreg'),
    
]