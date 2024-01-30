from aqs.settings import aqs_version
from django.shortcuts import render, redirect, HttpResponse
from django.urls import reverse
from urllib.parse import urlencode
from django.contrib.auth.models import User, Group
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.hashers import make_password
from django.db.models import Q
from django.contrib.auth.forms import UserCreationForm, PasswordChangeForm
# from datetime import datetime
from base.decorators import *
# from django.contrib.auth.views import PasswordChangeView
from django.urls import reverse_lazy

from .models import *
from django.utils.timezone import localtime, get_current_timezone
import pytz
from django.utils import timezone
from base.views import auth_data


import logging
from aqs.tasks import *

logger = logging.getLogger(__name__)



@unauth_user
@allowed_users(allowed_roles=['admin','support','supervisor','manager'])
def TimeSlotSummaryView(request):     
    auth_branchs , \
    auth_userlist, \
    auth_userlist_active, \
    auth_grouplist, \
    auth_profilelist, \
    auth_ticketformats , \
    auth_routes, \
    auth_countertype, \
    auth_timeslots, \
    = auth_data(request.user)
 
    context = {'users':auth_userlist, 
               'users_active':auth_userlist_active, 
               'profiles':auth_profilelist, 
               'branchs':auth_branchs, 
               'ticketformats':auth_ticketformats, 
               'routes':auth_routes,
               'timeslots':auth_timeslots,
               }
    context = {'aqs_version':aqs_version} | context 
    return render(request, 'booking/timeslot.html', context)