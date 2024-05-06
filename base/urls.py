# base.urls.py
from django.urls import path, reverse 
# from django.contrib.auth import views as auth_views
from . import views

# Touch URL : 127.0.0.1:8000/touch?bc=KB&t=t1
# New or edit the WEB Touch panel : open 127.0.0.1:8000/admin and webtouch table



urlpatterns = [
    # path('adminlocked/', views.adminlockedView, name='adminlocked'),
    path('', views.homeView, name='home'),
    path('login/', views.UserLoginView, name='login'),
    path('logout/', views.UserLogoutView, name='logout'),
    path('user/', views.UserSummaryView, name='usersummary'),
    path('userlist/', views.UserSummaryListView, name='user-list'),
    path('update-user/<str:pk>/', views.UserUpdateView, name='update-user'),
    path('update-user-tickettype/<str:pk>/', views.UserUpdateTTView, name='update-user-tt'),
    path('new-user/', views.UserNewView, name='new-user'),
    path('new-user2/<str:pk>/', views.UserNewView2, name='new-user2'),
    path('new-user3/<str:pk>/', views.UserNewView3, name='new-user3'),
    path('password/', views.UserChangePWView, name='pw-user'),   
    path('delete/<str:pk>/', views.UserDelView, name='delete-user'),
    path('reset/<str:pk>/', views.UserResetView, name='resetpw-user'),
    path('menu/', views.MenuView, name='menu'),

    path('settings/', views.SettingsSummaryView, name='settingssummary'),
    path('update-settings/<str:pk>/', views.SettingsUpdateView, name='update-settings'),
    path('update-settings/<str:pk>/save/', views.Settings_Save),
    # path('update-settings/<str:pk>/save/', views.Settings_Save, name='a'),

    path('tfs/', views.TicketFormatSummaryView, name='tfsummary'),
    path('update-tf/<str:pk>/', views.TicketFormatUpdateView, name='update-tf'),
    path('delete-tf/<str:pk>/', views.TicketFormatDelView, name='delete-tf'),
    path('new-tf/', views.TicketFormatNewView, name='new-tf'),

    path('routes/', views.TicketRouteSummaryView, name='routesummary'),
    path('update-route/<str:pk>', views.TicketRouteUpdateView, name='update-route'),
    path('delete-route/<str:pk>/', views.TicketRouteDelView, name='delete-route'),
    path('new-route/', views.TicketRouteNewView, name='new-route'),

    path('supervisors/', views.SuperVisorListView, name='supersummary'),
    path('supervisor/<str:pk>/', views.SuperVisorView, name='supervisor'),
    path('supervisor/forcelogout/<str:pk>/<str:csid>/', views.SuperVisor_ForceLogoutView ,  name='forcelogout'),    
    
    path('reports/', views.Reports, name='reports'),
    path('reports/raw/', views.Report_RAW_Result , name='reportraw'),
    path('reports/ticket/', views.Report_Ticket_Result , name='reportticket'),
    path('reports/staff/', views.Report_Staff_Result , name='reportstaff'),

    # http://127.0.0.1:8000/webtv/KB/Reception/
    path('webtv/<str:bcode>/<str:ct>/', views.webtv ),
    # path('webtv/', views.webtv_old_school),
    # path('my/', views.webmyticket_old_school, name='myticket'),
    path('my/<str:bcode>/<str:ttype>/<str:tno>/<str:sc>/', views.webmyticket, name='myticket'),
    path('cancel/<str:pk>/<str:sc>/', views.CancelTicketView,  name='cancelticket'),
    path('touch/', views.webtouchView),

    path('softkey_login_b/', views.SoftkeyLoginBranchView,  name='softkeyloginb'),
    path('softkey_login/<str:pk>/', views.SoftkeyLoginView,  name='softkeylogin'),
    path('softkey/<str:pk>/', views.SoftkeyView, name='softkey'),
    # path('softkey_logout/<str:pk>/', views.SoftkeyLogoutView,  name='softkeylogout'),
    path('softkey_logout/', views.SoftkeyLogoutView,  name='softkeylogout'),
    # error : django.urls.exceptions.NoReverseMatch: Reverse for 'softkeylogout' with arguments '('',)' not found. 1 pattern(s) tried: ['softkey_logout/\\Z']
    # path('softkey_logout/', views.SoftkeyLogoutView,  name='softkeylogout'),
    # error : django.urls.exceptions.NoReverseMatch: Reverse for 'softkeylogout' with arguments '('',)' not found. 1 pattern(s) tried: ['softkey_logout/\\Z']
    path('softkey_logout/<str:pk>/', views.SoftkeyLogoutView,  name='softkeylogout'),
    path('softkey_call/<str:pk>/', views.SoftkeyCallView,  name='softkeycall'),
    path('softkey_process/<str:pk>/', views.SoftkeyProcessView,  name='softkeyprocess'),
    
    path('softkey_done/<str:pk>/', views.SoftkeyDoneView,  name='softkeydone'),
    path('softkey_miss/<str:pk>/', views.SoftkeyMissView,  name='softkeymiss'),
    path('softkey_recall/<str:pk>/', views.SoftkeyRecallView,  name='softkeyrecall'),
    path('softkey_void/<str:pk>/<str:ttid>/', views.Softkey_VoidView,  name='softkeyvoid'),
    path('softkey_get/<str:pk>/<str:ttid>/', views.Softkey_GetView,  name='softkeyget'),

    # for Hypic
    path('repair/', views.repair ),



]