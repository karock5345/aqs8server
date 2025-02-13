from django.urls import path


from . import views
from . import api


urlpatterns = [
    # Testing page
    # path('', views.WelcomeView, name='crmhome'),
    path('customer/', views.CustomerListView, name='crmcustomerlist'),
    path('customer-update/<str:pk>/', views.CustomerUpdateView, name='customerupdate'),
    path('customer-new/<str:ccode>/', views.CustomerNewView, name='customernew'),
    path('customer-del/<str:pk>/', views.CustomerDelView, name='customerdelete'),
    path('quotation/', views.QuotationView, name='crmquotation'),
    path('quotation/<str:pk>/', views.QuotationView, name='crmquotation'),
    path('quotation-new/<str:ccode>/', views.QuotationNewView, name='quotationnew'),
    path('quotation-del/<str:pk>/', views.QuotationDelView, name='quotationdelete'),
    path('quotation-pdf/<str:pk>/', views.QuotationPDFView, name='quotationpdf'),
    path('invoice/', views.InvoiceView, name='crminvoice'),
    path('invoice/<str:pk>/', views.InvoiceView, name='crminvoice'),
    path('invoice-new/<str:ccode>/', views.InvoiceNewView, name='invoicenew'),
    path('invoice-del/<str:pk>/', views.InvoiceDelView, name='invoicedelete'),
    path('invoice-pdf/<str:pk>/', views.InvoicePDFView, name='invoicepdf'),
    path('receipt/', views.ReceiptView, name='crmreceipt'),
    path('receipt/<str:pk>/', views.ReceiptView, name='crmreceipt'),
    path('receipt-new/<str:ccode>/', views.ReceiptNewView, name='receiptnew'),
    path('receipt-del/<str:pk>/', views.ReceiptDelView, name='receiptdelete'),
    path('receipt-pdf/<str:pk>/', views.ReceiptPDFView, name='receiptpdf'),    
    path('member/', views.MemberListView, name='crmmember'),
    path('member-update/<str:pk>/', views.MemberUpdateView, name='memberupdate'),
    path('member-del/<str:pk>/', views.MemberDelView, name='memberdelete'),
    path('member-new/<str:ccode>/', views.MemberNewView, name='membernew'),
    path('supplier/', views.SupplierListView, name='crmsupplierlist'),
    path('supplier-update/<str:pk>/', views.SupplierUpdateView, name='supplierupdate'),
    path('supplier-new/<str:ccode>/', views.SupplierNewView, name='suppliernew'),
    path('supplier-del/<str:pk>/', views.SupplierDelView, name='supplierdelete'),
    path('product/', views.ProductListView, name='crmproductlist'),

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