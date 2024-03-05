from django.urls import path

from .views import TimeSlotSummaryView, TimeSlotUpdateView, TimeSlotNewView, TimeSlotDelView 
from .views import BookingClientView, Booking_Details_ClientView
from .views import BookingSummaryView, BookingUpdateView, BookingDelView, BookingNewView


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
    path('<str:bcode>/', BookingClientView, name='booking_client'),
    

    # path('success/', None, name='booking-success'),
]