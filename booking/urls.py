from django.urls import path

from .views import TimeSlotSummaryView, TimeSlotUpdateView, TimeSlotNewView, TimeSlotDelView 
from .views import BookingView, Booking_DetailsView


urlpatterns = [
    # Testing page
    # path('', views.WelcomeView, name='crmhome'),

    # Booking html pages
    path('timeslot/', TimeSlotSummaryView, name='bookingtimeslot'),
    path('timeslot-update/<str:pk>/', TimeSlotUpdateView, name='ts-update'),
    path('timeslot-new/', TimeSlotNewView, name='ts-new'),
    path('timeslot-del/<str:pk>/', TimeSlotDelView, name='ts-delete'),
    # http://127.0.0.1:8000/booking/KB/
    path('<str:bcode>/', BookingView, name='booking'),
    path('details/<str:pk>/', Booking_DetailsView, name='booking-details'),
    # path('success/', None, name='booking-success'),
]