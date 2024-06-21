from django.urls import path

from .views import TimeSlotSummaryView, TimeSlotUpdateView, TimeSlotNewView, TimeSlotDelView 
from .views import BookingClientView, Booking_Details_ClientView
from .views import BookingSummaryView, BookingUpdateView, BookingDelView, BookingNewView
from .views import TimeslotTempSummaryView, TimeSlotTempUpdateView, TimeSlotTempDelView, TimeSlotTempItemUpdateView, TimeSlotTempItemDelView, TimeSlotTempNewView


urlpatterns = [
    # Testing page
    # path('', views.WelcomeView, name='crmhome'),

    # Booking html pages
    path('booking/', BookingSummaryView, name='bookingsummary'),
    path('booking-update/<str:pk>/', BookingUpdateView, name='bookingupdate'),
    path('booking-del/<str:pk>/', BookingDelView, name='bookingdelete'),
    path('booking-new/', BookingNewView, name='bookingnew'),

    path('timeslot/', TimeSlotSummaryView, name='bookingtimeslot'),
    path('timeslot-update/<str:pk>/', TimeSlotUpdateView, name='ts-update'),
    path('timeslot-new/', TimeSlotNewView, name='ts-new'),
    path('timeslot-del/<str:pk>/', TimeSlotDelView, name='ts-delete'),
    # http://127.0.0.1:8000/booking/KB/

    path('details/<str:pk>/', Booking_Details_ClientView, name='booking-details_client'),

    
    path('timeslottemp/', TimeslotTempSummaryView, name='timeslottemp'),
    path('timeslottemp-new/', TimeSlotTempNewView, name='temp-new'),
    path('timeslottemp-update/<str:pk>/', TimeSlotTempUpdateView, name='temp-update'),
    path('timeslottemp-del/<str:pk>/', TimeSlotTempDelView, name='temp-delete'),
    path('tempitem-update/<str:pk>/<str:tempid>/', TimeSlotTempItemUpdateView, name='tempitem-update'),
    path('tempitem-del/<str:pk>/<str:tempid>/', TimeSlotTempItemDelView, name='tempitem-delete'),
    # path('success/', None, name='booking-success'),


    # this path should be the last one
    path('<str:bcode>/', BookingClientView, name='booking_client'),
]