from django.urls import path
# from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('', views.homeView, name='home'),
    path('login/', views.UserLoginView, name='login'),
    path('logout/', views.UserLogoutView, name='logout'),
    path('user/', views.UserSummaryView, name='usersummary'),
    path('update-user/<str:pk>/', views.UserUpdateView, name='update-user'),
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

    
    path('rawdata/', views.Report_RAW_q, name='reportrawq'),
    path('rawdata/result/', views.Report_RAW_Result , name='reportraw'),

    # path('webtv/', views.disptvView ),
    path('webtv/', views.webtv_old_school),
    path('my/', views.webmyticket_old_school, name='myticket'),
    path('cancel/<str:pk>/<str:sc>/', views.CancelTicketView,  name='cancelticket'),
    path('touch/', views.webtouchView),
]