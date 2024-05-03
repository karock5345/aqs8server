"""aqs URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include, reverse
from django.http import HttpResponse
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from django.conf import settings
from django.conf.urls.static import static

from base.views import adminlockedView
urlpatterns =[]


    

urlpatterns2 = [    
    path('', include('base.urls')),
    path('api/', include('base.api.urls')),
    path('sch/', include('base.sch.urls')),
    path('crm/', include('crm.urls')),
    path('booking/', include('booking.urls')),
    
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]


if settings.ADMIN_ENABLED:
    urlpatterns.append(path('admin/', admin.site.urls))
else:
    # direct to 'base/templates/base/admin_locked.html'
    urlpatterns.append(path('admin/', (adminlockedView)))


urlpatterns = urlpatterns + urlpatterns2 + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
