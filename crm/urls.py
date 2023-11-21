from django.urls import path

from . import views


urlpatterns = [
    # Testing page
    path('', views.WelcomeView, name='welcome'),

    # CRM APIs for mobile app
    path('api/login/', views.crmUserLoginView, name='login'),
]