from django.urls import path

from .views import TimeSlotSummaryView, TimeSlotUpdateView, TimeSlotNewView, TimeSlotDelView


urlpatterns = [
    # Testing page
    # path('', views.WelcomeView, name='crmhome'),

    # Booking html pages
    path('timeslot/', TimeSlotSummaryView, name='bookingtimeslot'),
    path('timeslot-update/<str:pk>/', TimeSlotUpdateView, name='ts-update'),
    path('timeslot-new/', TimeSlotNewView, name='ts-new'),
    path('timeslot-del/<str:pk>/', TimeSlotDelView, name='ts-delete')
    
]