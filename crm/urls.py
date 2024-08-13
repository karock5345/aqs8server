from django.urls import path

from . import views
from . import api


urlpatterns = [
    # Testing page
    # path('', views.WelcomeView, name='crmhome'),
    path('customer/', views.CustomerListView, name='crmcustomerlist'),
    path('customer-update/<str:pk>/', views.CustomerUpdateView, name='customerupdate'),
    path('quotation/', views.QuotationView, name='crmquotation'),
    path('invoice/', views.InvoiceView, name='crminvoice'),
    path('receipt/', views.ReceiptView, name='crmreceipt'),
    path('member/', views.MemberListView, name='crmmember'),
    path('member-update/<str:pk>/', views.MemberUpdateView, name='memberupdate'),
    path('member-del/<str:pk>/', views.MemberDelView, name='memberdelete'),
    path('member-new/<str:ccode>/', views.MemberNewView, name='membernew'),


    # CRM APIs for mobile app
    path('api/login/', api.crmMemberLoginView, name='crmlogin'),
    path('api/info/', api.crmMemberInfoView, name='crmmeminfo'),
    path('api/items/', api.crmMemberItemListView, name='crmmemitemlist'),
    path('api/logout/', api.crmMemberLogoutView, name='crmlogout'),
    path('api/reg/', api.crmMemberRegistrationView, name='crmreg'),
    path('api/verify/', api.crmMemberVerificationView, name='crmverify'),
    path('api/remove/', api.crmMemberDelView, name='crmremove'),
    path('api/pushdata/', api.crmPushMessageDataView, name='crmgetpushdata'),

]