from collections.abc import Callable, Iterable, Mapping
import threading
from typing import Any
from base.models import *
import csv
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import User, Group
from django.db import connection
import logging

logger = logging.getLogger(__name__)
class MigrateDBThread(threading.Thread):

    def __init__(self, branch, staff_file, maindb_file, userlog_file):
        self.branch = branch
        self.staff_file = staff_file
        self.maindb_file = maindb_file
        self.userlog_file = userlog_file
        threading.Thread.__init__(self)
    
    def run(self):        
        try:
            logger.info("MigrateDBThread: run()")
            logger.info('Start migrating staff data...' + self.staff_file)

            # first step create user if not exist

            # Hash the password using Django's default algorithm (PBKDF2)
            password = '1234'
            password_hash = make_password(password)
            today = datetime.datetime.now()
            group = Group.objects.get(name='frontline')

            with open(self.staff_file, 'r') as file:
                reader = csv.reader(file)

                # Iterate over each row in the CSV file and insert into the PostgreSQL table
                for row in reader:
                    staffno, name, password, ttype, winuser, adminright, theend = row

                    # check if user exist
                    user = None
                    try:
                        user = User.objects.get(username=staffno)
                    except User.DoesNotExist:
                        user = None
                    if user == None:
                        # create user
                        user = User.objects.create(username=staffno, password=password_hash, first_name=name, last_name=self.branch.bcode, email='', is_staff=False, is_active=False, is_superuser=False, last_login=today, date_joined=today)
                        user.groups.add(group)

                        # add userprofile
                        userprofile = UserProfile.objects.create(user=user)
                        userprofile.branchs.add(self.branch)
                    # break  # for test
            logger.info('Completed migrating staff data...' + self.staff_file)
            
        except Exception as e:
            print("MigrateDBThread: run() Exception: ", e)

