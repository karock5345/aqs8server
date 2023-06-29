from django.urls import path, reverse 
# from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('', views.homeView, name='home'),
    path('login/', views.UserLoginView, name='login'),
    path('logout/', views.UserLogoutView, name='logout'),
    path('user/', views.UserSummaryView, name='usersummary'),
    path('update-user/<str:pk>/', views.UserUpdateView, name='update-user'),
    path('update-user-tickettype/<str:pk>/', views.UserUpdateTTView, name='update-user-tt'),
    path('new-user/', views.UserNewView, name='new-user'),
    path('password/', views.UserChangePWView, name='pw-user'),   
    path('delete/<str:pk>/', views.UserDelView, name='delete-user'),
    path('menu/', views.MenuView, name='menu'),

    path('branch/', views.BranchSummaryView, name='branchsummary'),
    path('update-branch/<str:pk>/', views.BranchUpdateView, name='update-branch'),
    path('update-branch/<str:pk>/savebranch/', views.Branch_Save, name='a'),

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
    
    path('rawdata/', views.Report_RAW_q, name='reportrawq'),
    path('rawdata/result/', views.Report_RAW_Result , name='reportraw'),

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
    
    # for Hypic
    path('repair/', views.repair ),
]