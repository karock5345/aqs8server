# AQS version 8 For PCCW 2023
## Main Server (Causeway Bay)
- Linux main server (DELL 13th i5) 
- IP : 10.202.2.108
- Linux server su: ubuntu /// wert2206EDC5345 (change password cmd:passwd)
- Django SU : supertim /// YtZqEIpk5345 ,  admin : pccwadmin /// YEjLZBYGF4
- Network enp0s31f6

## DB server
- Linux DB server (DELL 12th i3) 
- IP : 10.202.2.109
- Linux server su: ubuntu /// wert2206EDC5345 
- Network enp1s0

## Relocate to Causeway Bay

| Item | IP | Gateway | DNS |
| --- | --- | --- | --- |
| Q. Server | 10.202.2.108 | 10.202.2.254 | 10.168.9.6 10.203.65.53 |
| Database server | 10.202.2.109 | 10.202.2.254 | 10.168.9.6  10.203.65.53 |
| Kiosk Computer | 10.202.2.110  | 10.202.2.254 | 10.168.9.6  10.203.65.53 |
| TV Computer (Kiosk) | 10.202.2.167  | 10.202.2.254 | 10.168.9.6  10.203.65.53 |
| TV Computer (#2) | 10.202.2.168  | 10.202.2.254 | 10.168.9.6  10.203.65.53 |

## Q. Server settings:
### `Step 1` : Change Q. Server IP:
```
# Config server IP
sudo nano /etc/netplan/00-installer-config.yaml
```
Edit:
```ini
# This is the network config written by 'subiquity'
      addresses:
        - 10.202.2.108/24
      routes:
        - to: default
          via: 10.202.2.254
      nameservers:
        addresses: [10.168.9.6, 10.203.65.53]
  version: 2
```
### `Step 2` : Change Nginx config
```bash
# Nginx
sudo nano /etc/nginx/sites-available/aqs8server
```
Edit:
```ini
    server_name localhost 127.0.0.1 10.202.2.108;
```
### `Step 3` : Change Django settings.py for production DB server IP 
```bash
sudo nano ~/aqs8server/aqs/settings.py
```
Edit:
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'aqsdb8',
        'USER': 'aqsdbuser',
        'PASSWORD': 'dbpassword-Dlcg1dwMOXSKIAIM',
        'HOST': '10.202.2.109',
        'PORT': '5432',
    }
}
```

## DB Server settings:
### `Step 1` : Change DB Server IP:
```
# Config server IP
sudo nano /etc/netplan/00-installer-config.yaml
```
Edit:
```ini
# This is the network config written by 'subiquity'
      addresses:
        - 10.202.2.109/24
      routes:
        - to: default
          via: 10.202.2.254
      nameservers:
        addresses: [10.168.9.6, 10.203.65.53]
  version: 2
```
### `Step 2` : Change DB Server PostgreSQL config
```bash
sudo find / -name pg_hba.conf
sudo nano /path/to/pg_hba.conf
# this case:
sudo nano /etc/postgresql/14/main/pg_hba.conf
# add line:
host    aqsdb8    aqsdbuser    10.202.2.108/32    md5
```

```bash
sudo systemctl reload postgresql.service
```

## Upgrade Server v8.1.5 (Phase 4)
- Switch to new server
- Fixed bug : base > v_softkey_sub.py > cc_aux : Counter can not call ticket when counter is hold a ticket > ACW > AUX > Ready
- gUnicorn workers = 1 for production server

## Upgrade Server v8.1.4 (Phase 3)
- new Python lib : django-crequest (for raw data report)
- New Python lib : celery[redis] (for long time task)
- New Python lib : wcwidth vine redis prompt-toolkit colorama billiard click amqp kombu click-repl click-plugins click-didyoumean (for celery)

## Upgrade Server v8.1.4  (Phase 3)
### Switch to new server
### `Step 1` : Change the server IP

```
# Config server IP
sudo nano /etc/netplan/00-installer-config.yaml
```
Edit:
```ini
# This is the network config written by 'subiquity'
      addresses:
        - 10.95.157.237/24
      routes:
        - to: default
          via: 10.95.157.254
      nameservers:
        addresses: [10.2.202.1, 10.3.220.160]
  version: 2
```


### `Step 2` : Change Nginx config
```bash
# Nginx
sudo nano /etc/nginx/sites-available/aqs8server
```
Edit:
```ini
    server_name localhost 127.0.0.1 10.95.157.237;
```
### `Step 3` : Change Django settings.py for production DB server IP 
```bash
sudo nano ~/aqs8server/aqs/settings.py
```
Edit:
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'aqsdb8',
        'USER': 'aqsdbuser',
        'PASSWORD': 'dbpassword-Dlcg1dwMOXSKIAIM',
        'HOST': '10.95.157.236',
        'PORT': '5432',
    }
}
```
### `Step 4` : Change Q.Server SU password
```bash
sudo passwd ubuntu
> wert2206EDC5345
```
### `Done` for switch to new server ------------------

```bash
# Backup settings.py
cp ~/aqs8server/aqs/settings.py ~/
# Backup previous version
cp -r ~/aqs8server/ ~/aqs8server813.bak/
# Remove previous version
rm -r ~/aqs8server/

# Copy new version from PC or USB drive
# from PC :
# in server
mkdir ~/aqs8server/
# in PC
pscp -r your/folder/aqs8server/* ubuntu@10.95.157.237:/home/ubuntu/aqs8server/
# change owner
sudo chown ubuntu ~/aqs8server -R

# Or from USB drive :
# find out your usb drive my case is sdb1
lsblk
sudo mkdir /mnt/usb
sudo mount /dev/sdb /mnt/usb
cd /mnt/usb
sudo cp aqs8server /home/ubuntu/aqs8server/ -r
# change owner
sudo chown ubuntu ~/aqs8server -R
sudo umount /mnt/usb
```

### copy settings.py from backup
```bash
cp ~/settings.py ~/aqs8server/aqs/settings.py
```
### copy env from backup
```bash
rm -r ~/aqs8server/env
cp -r ~/aqs8server813.bak/env ~/aqs8server/
```


### Install python lib offline
```bash
# Download python lib to local PC
pip download django-crequest -d ./static_deploy
pip download celery[redis] -d ./static_deploy

# new dir on server
mkdir ~/aqs8server/static_deploy
# Copy to server from PC
cd (your project folder)
pscp -r ./aqs8server/static_deploy/* ubuntu@10.95.157.237:/home/ubuntu/aqs8server/static_deploy/

# change owner
sudo chown ubuntu ~/aqs8server -R

# Install python lib on liunx server
cd /home/ubuntu/static_deploy
cd /home/ubuntu/aqs8server
source ./env/bin/activate
pip3 install django-crequest --no-index --find-links=/home/ubuntu/static_deploy
pip3 install celery[redis] --no-index --find-links=/home/ubuntu/static_deploy
```
### Edit settings.py after restore from backup
> nano ~/aqs8server/aqs/settings.py

```python
# settings.py
REDIS_HOST = '127.0.0.1'
CHANNEL_LAYERS = {
    'default':{
        'BACKEND':'channels_redis.core.RedisChannelLayer',
        # 'BACKEND':'channels_redis.pubsub.RedisPubSubChannelLayer',
        'CONFIG': {
            # 'hosts':[('127.0.0.1', '6379')],
            'hosts':[(REDIS_HOST, '6379')],      # vm
        # "channel_capacity": {
        #         "http.request": 200,
        #         "http.response!*": 10,
        #         re.compile(r"^websocket.send\!.+"): 20,
        #     },
        },
    }
}
CELERY_BROKER_URL = 'redis://' + REDIS_HOST + ':6379/0'
CELERY_RESULT_BACKEND = 'redis://' + REDIS_HOST + ':6379/0'
```
# Run Celery worker on the server
### Using Systemd (Process Manager):
### Step 1: Create the dedicated user and group
```bash
sudo groupadd celery ;
sudo useradd -g celery celery ;
sudo mkdir /var/run/celery ;
sudo chown -R celery:celery /var/run/celery/ ;
sudo chmod o+w /var/run/celery ;
sudo mkdir /var/log/celery ;
sudo chown -R celery:celery /var/log/celery/ ;
sudo chmod o+w /var/log/celery
```
### Step 2: Create the Celery Worker Configuration File

Create a Celery configuration file (e.g., `celeryd`) in the `/etc/default/` directory:

```bash
sudo nano /etc/default/celeryd
```

Add the following content to the `celeryd` file. Modify the values for your specific setup:

```ini
# /etc/default/celeryd
#   most people will only start one node:
CELERYD_NODES="worker1"
#   but you can also start multiple and configure settings
#   for each in CELERYD_OPTS
#CELERYD_NODES="worker1 worker2 worker3"
#   alternatively, you can specify the number of nodes to start:
#CELERYD_NODES=10

# Absolute or relative path to the 'celery' command:
CELERY_BIN="/home/ubuntu/aqs8server/env/bin/celery"
#CELERY_BIN="/virtualenvs/def/bin/celery"

# App instance to use
# comment out this line if you don't use an app
CELERY_APP="aqs.celery:app"
# or fully qualified:
#CELERY_APP="proj.tasks:app"

# Where to chdir at start.
CELERYD_CHDIR="/home/ubuntu/aqs8server"

# Extra command-line arguments to the worker
CELERYD_OPTS="--time-limit=300 --concurrency=8"
# Configure node-specific settings by appending node name to arguments:
#CELERYD_OPTS="--time-limit=300 -c 8 -c:worker2 4 -c:worker3 2 -Ofair:worker1"

# Set logging level to DEBUG
#CELERYD_LOG_LEVEL="DEBUG"

# %n will be replaced with the first part of the node name.
CELERYD_LOG_FILE="/var/log/celery/%n%I.log"
CELERYD_PID_FILE="/var/run/celery/%n.pid"

# Workers should run as an unprivileged user.
#   You need to create this user manually (or you can choose
#   a user/group combination that already exists (e.g., nobody).
CELERYD_USER="celery"
CELERYD_GROUP="celery"
CELERYD_LOG_LEVEL="INFO"
# If enabled PID and log directories will be created if missing,
# and owned by the userid/group configured.
CELERY_CREATE_DIRS=1
```

Replace the placeholders (`<your_django_user>`, `<your_django_group>`, `your_project_name`, and other paths) with the appropriate values for your setup.

### Step 3: Create the Celery Worker Systemd Service File

Create a Systemd service file (e.g., `celery.service`) in the `/etc/systemd/system/` directory:

```bash
sudo nano /etc/systemd/system/celery.service
```

Add the following content to the `celery.service` file:

```ini
# /etc/systemd/system/celery.service
[Unit]
Description=Celery Service
After=network.target

[Service]
Type=forking
User=ubuntu
Group=ubuntu

EnvironmentFile=/etc/default/celeryd
WorkingDirectory=/home/ubuntu/aqs8server
ExecStart=/home/ubuntu/aqs8server/env/bin/celery multi start ${CELERYD_NODES} \
  -A ${CELERY_APP} --pidfile=${CELERYD_PID_FILE} \
  --logfile=${CELERYD_LOG_FILE} --loglevel=${CELERYD_LOG_LEVEL} ${CELERYD_OPTS}
ExecStop=/home/ubuntu/aqs8server/env/bin/celery multi stopwait ${CELERYD_NODES} \
  --pidfile=${CELERYD_PID_FILE}
ExecReload=/home/ubuntu/aqs8server/env/bin/celery multi restart ${CELERYD_NODES} \
  -A ${CELERY_APP} --pidfile=${CELERYD_PID_FILE} \
  --logfile=${CELERYD_LOG_FILE} --loglevel=${CELERYD_LOG_LEVEL} ${CELERYD_OPTS}

[Install]
WantedBy=multi-user.target

```

### Step 4: Enable and Start the Celery Service

Now that you have created the configuration and service files, enable and start the Celery service:

```bash
sudo systemctl enable celery
sudo systemctl start celery
```

The `enable` command ensures that the Celery service starts automatically during server startup.

### Step 5: Add autorun script for auto shutdown
```bash
sudo nano /home/ubuntu/autorun.sh
```
Add following script:
```bash
# For Celery
# The dir will auto deleted when every time reboot.
mkdir /var/run/celery
chown -R celery:celery /var/run/celery/
chmod o+w /var/run/celery
```

### Step 6: Check the Celery Service Status

You can check the status of the Celery service to ensure it is running:

```bash
sudo systemctl status celery
```

This command will display the current status and any logs related to the Celery service.

### Step 7: Monitor Celery Worker Logs

You can monitor the Celery worker logs at the location specified in the `CELERYD_LOG_FILE` configuration (e.g., `/var/log/celery/%N.log`). These logs will contain information about the Celery worker's activities and task execution.

That's it! Your Celery worker is now set up as a Systemd service and will start automatically during server startup. It will continue to run in the background, processing your asynchronous tasks as needed.

## Upgrade Server v8.1.3 (Phase 2)
- Report function (1. Staff performance report, 2. Total ticket report)
- Migration old DB to new server

### JWT settings
```bash
nano ./aqs/settings.py
```
Edit:

```python
SIMPLE_JWT = {
    # Debug mode set 120 minutes, otherwise 5 minutes    
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=5),
    # Debug mode set 30 minutes, otherwise days=1
    "REFRESH_TOKEN_LIFETIME": timedelta(days=1),
    "ROTATE_REFRESH_TOKENS": False,
    "BLACKLIST_AFTER_ROTATION": False,
    "UPDATE_LAST_LOGIN": False,

    "ALGORITHM": "HS256",
    "SIGNING_KEY": SECRET_KEY,
    "VERIFYING_KEY": None,
    "AUDIENCE": None,
    "ISSUER": None,
   
    "AUTH_HEADER_TYPES": ("Bearer",),
}
```
exit and save
## Upgrade Server v8.1.2 (Phase 1)
- Support new Display Panel
- New 'Force Logout' function for Supervise
- New API for shutdown branch and run INIT_SCH
- New API for Display Panel get latest 5 tickets
- Fixed bug : Schedule task not run when branchs is shutdown time same. Casue by the init_branch_reset() function is remove all schedule task first.

### Check the server auto shutdown?
```
# See log of my Linux system shutdown
last -x shutdown
```
## Auto power off script (for Linux server)
```bash
cd /etc/systemd/system/
sudo nano autorun.service
```
- add line:
```
[Unit]
Description=Autorun
After=network.target

[Service]
ExecStart=/bin/bash /home/ubuntu/autorun.sh

[Install]
WantedBy=default.target
```
- Save and exit

```bash
sudo systemctl enable autorun.service
```

```
nano /home/ubuntu/autorun.sh
```

```nano
# Auto shutdown at 00:30
shutdown -h 00:30
# Reboot at 00:00
shutdown -r 00:00
```
## Wrong Auto power off script (for Linux server)

~~sudo nano /etc/rc.local~~

~~- add line:~~

~~shutdown -h 23:55~~

~~- Save and exit~~


## Upgrade Server v8.1.2
```bash
# Backup settings.py
cp ~/aqs8server/aqs/settings.py ~/
# Backup previous version
cp -r ~/aqs8server/ ~/aqs8server.bak/
# Remove previous version
rm -r ~/aqs8server/

# mount USB drive
# find out your usb drive my case is sdb1
lsblk
sudo mkdir /mnt/usb
sudo mount /dev/sdb /mnt/usb
cd /mnt/usb
sudo cp aqs8server /home/ubuntu/aqs8server/ -r
# change owner
sudo chown ubuntu ~/aqs8server -R
sudo umount /mnt/usb


```
## PCCW is no internet access
~~cd ~/aqs8server~~

~~virtualenv env~~

~~source env/bin/activate~~

~~sudo nano requirements.txt~~

~~# [del line :] twisted-iocpsupport=x.x.x~~

~~pip install -r requirements.txt~~

~~pip install gunicorn psycopg2~~

~~pip install daphne~~

```
# copy backup env to new version folder
cp ~/aqs8server.bak/env/ ~/aqs8server/env/
# test env
cd ~/aqs8server
source ./env/bin/activate

cp ~/settings.py ~/aqs8server/aqs/

rm ./readme.md

python3 manage.py collectstatic
sudo gpasswd -a www-data ubuntu
sudo chmod g+x /home/ubuntu && chmod g+x /home/ubuntu/aqs8server/ && chmod g+x /home/ubuntu/aqs8server/static_deploy

# DB is modified, so need to migrate
python manage.py makemigrations
python manage.py migrate

sudo nginx -s reload
sudo reboot

```

### <span style="color:orange;">**Version 8.0.0**</span>
- First Django version for Queuing Server
### <span style="color:orange;">**Version 8.0.1**</span>
- Admin can edit TV scrolling text
- New 3 APIs for Roche
- Admin Supervise add Printer Status with color
- WebTV support multi-branch and multi-counter
- WebTV add counter type text (2 languages)
- Web auto logout
- New webTV HTML layout
- New web my ticket function
- Add Cancel Ticket to web my ticket
- Add My e-Ticket link QR code for print ticket
- Add Web Touch function for new ticket
- Change user branch authority (Admin, Report) : User in group Admin or Report. For example, if user mary is Admin Group and Branch 1,2. Mary only add / edit / del user which is Branch 1 or 2 or 1,2. If the user_A is branch 1,2,3. Mary do not have access to user_A.
- fixed waiting on queue (TicketRoute) show on TV / WebTV
- Deploy to Production Server with Websocket + SSL is work
- WebTV (HTML) is support WS
### <span style="color:orange;">**Version 8.0.2**</span>
- Support SMS Module
- Softkey web version
### <span style="color:orange;">**Version 8.0.3**</span>
- fixed Print replaced by Django Log for debug on server
### <span style="color:orange;">**Version 8.1.0**</span>
- API Support JWT
- All API request.user should be user group 'api'
- Separete Touch Panel API functions to new file : v_touch.py
- Added TicketFormat , TicketRoute HTML input check
- Support Ticket Type more than 1 char and not case sensitive (e.g. Ticket type: A, AA, Aa, LAB, ...)
- user.update.html add HTML ticket type data input by checkbox
- fixed checkbox only show user related branch
- New Ticketformat will create new ticket route automatically
- Web Softkey login select Branch first then select Counter
- New API : /api/touchkeys/ for PCCW Touch Panel
- Fixed Error when open admin page : Error HTTP GET /static/admin/js/actions.js 500 (aqs/urls.py)
- Upgrade some packages (hiredis==2.2.3, cryptography==41.0.1, pyOpenSSL==23.2.0 etc.)
- upgrade django to 4.1.9 from 4.1.7
- Fixed already login user in other branch 
- Fixed Web Softkey ticket sub total hiden ticketFormat Disabled
- Support Control Box python version (Flash light function only. Next version will support Keypad)
- Improve Web Softkey CallCentre UI
- Remove Search function for all HTML (include mobile version)
- Improve HTML: Branch list, Ticket Format list, Ticket Route list, Supervisor list (Show red color when disabled)
- Fixed number not correct in m-menu for mobile version (base/views -> MenuView)
- Improve HTML UI for Branch settings
### <span style="color:orange;">**Version 8.1.1 for PCCW 2023**</span>
- New Ticket Format, Ticket Type should be 2 letters and should be uppercase
- User group 'frontline' 'support' 'admin' 'manager' for PCCW 2023 
### <span style="color:orange;">**Version 8.1.1**</span>
- Fixed bug : Counter can not logout and Counter status is not correct (waiting) in Call Centre mode when reset branch, if counter still login then.
### <span style="color:orange;">**Version 8.1.2**</span>
- Add 'force logout' function for supervise.html
- New API for shutdown branch and run INIT_SCH : /sch/shutdown/?bcode=KB&app=postman&version=8.1
```bash
# get JWT (this api should be use superuser)
curl -X POST http://127.0.0.1/api/token/ -d "username=<su username>&password=<your-password>"
# Shutdown branch api
curl -X GET http://127.0.0.1/sch/shutdown/?bcode=<branch code>&app=curl&version=8.1 -H "Authorization: JWT <your-token>"
```
- Fixed bug : Schedule task not run when branchs is shutdown time same. Casue by the init_branch_reset() function is remove all schedule task first.
- New API for Display Panel get latest 5 tickets 
- Websocket disp_ for Display Panel replace from webtv_, websocket webtv_ only for HTML online ticket number
- Websocket disp_ new commands: call, removeall, wait
### <span style="color:orange;">**Version 8.1.3 (pccw2023_v2)**</span>
- Report function (1. Staff performance report, 2. Total ticket report)
- Add new API function for migrate 2 branchs (SCP, WTT) old DB to new server (http://127.0.0.1:8000/api/db2/?app=postman&version=8.1)


### <span style="color:orange;">**Version 8.1.4 (pccw2023_v3)**</span>
- Fixed bug : Callcentre mode, auto call ticket the counter sequence is not correct
- Add function : Update user add "reset password"
- Add new API function for migrate HHT old DB to new server (http://127.0.0.1:8000/api/db_tst/?app=postman&version=8.1)
- Romove API function for migrate 2 branchs (SCP, WTT) 
- Add new function for export report to excel
- Fixed bug : User ticket type 
- Raw data report add split data into multiple pages (using django-crequest)
- Add error message for new user 
- Show "active user number" in user list
- Celery support long time task (e.g. export report to excel)
- fixed bug : user group : 'manager' and 'support' can not Force Logout
- Web softkey add WS CounterStatus for receive loged or not then redirect to home page
- Web softkey ticket queue list add 'Call' button for each ticket
- Re-design "New User" page and change to 4 steps
- Add new page for "User List"

### <span style="color:orange;">**Version 8.1.5 (pccw2023_v4)**</span>
- Romove API function for migrate DB for HHT 
- Fixed bug : deploy to production server, the static_deploy folder is not correct 
for download CSV file (aqs/tasks.py -> export_raw)

<h3 style="color:orange;">Version 8.1.6 (pccw2023_v5)</h3>

- Fixed bug : base > v_softkey_sub.py > cc_aux : Counter can not call ticket when counter is hold a ticket > ACW > AUX > Ready
- gUnicorn workers = 1 for production (because of the call Ticket function is not work when workers > 1)
- ~~Softkey web cc version release waiting list, only 'void' with the list and 'call' is disabled~~
- They do not need waiting list on Softkey web cc version

# For Project PCCW 2023
## Main Server (WTT)
- Linux main server (DELL 13th i5) 
- IP : 10.95.157.237
- Sub mask : /24 (255.255.255.0)
- Gateway : 10.95.157.254
- DNS : 10.2.202.1, 10.3.220.160
- Linux server su: ubuntu /// wert2206EDC5345 (change password cmd:passwd)
- Django SU : supertim /// YtZqEIpk5345 ,  admin : pccwadmin /// YEjLZBYGF4
- Network enp0s31f6
- Change Server IP CMD:
```
# Config server IP
sudo nano /etc/netplan/00-installer-config.yaml
# Nginx
sudo nano /etc/nginx/sites-available/aqs8server
```
- Change Django settings.py for DB server IP was changed

```bash
sudo nano ~/aqs8server/aqs/settings.py
```
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'aqsdb8',
        'USER': 'aqsdbuser',
        'PASSWORD': 'dbpassword-Dlcg1dwMOXSKIAIM',
        'HOST': '10.95.157.236',
        'PORT': '5432',
    }
}
```
## Backup server

- Linux backup server (DELL 12th i3) IP : 10.95.157.237
- Linux server su: ubuntu /// wert2206EDC5345
- Network 


## DB server
- Linux DB server (DELL 12th i3) 
- IP : 10.95.157.236
- Sub mask : /24 (255.255.255.0)
- Gateway : 10.95.160.254
- DNS : 10.2.202.1, 10.3.220.160
- Linux server su: ubuntu /// wert2206EDC5345 
- Network enp1s0

- Change DB server IP
```
# Config DB server IP
sudo nano /etc/netplan/00-installer-config.yaml
# PostgreSQL
sudo find / -name pg_hba.conf
sudo nano /path/to/pg_hba.conf
# edit:
host    aqsdb8    aqsdbuser    10.95.157.237/32    md5
```
## TV PC (Ubuntu 22)

- Linux SU : ts /// asdf
- Sheung Wan (WTT)
- IP : TV1 10.95.157.233, TV2 10.95.157.234, TV3 10.95.157.235
- Sha Tin (SCP)
- IP : TV1 10.95.160.233, TV2 10.95.160.234, TV3 (reserve) 10.95.160.235
- TST (HHT)
- IP : TV1
### Setting Ubuntu 22 for TV PC 
- Install our software and auto run
- No screen saver
- No sleep
- No lock screen
- No auto update:


`Step 1:`

Goto Ubuntu Desktop -> Settings -> Software & Updates -> Updates -> Automatically check for updates: Never

Settings -> Software & Updates -> Updates -> Notify me of new Ubuntu version: Never

`Step 2:`
> Change update setting
```bash
sudo nano /etc/apt/apt.conf.d/20auto-upgrades
```
Add lines:
```ini
APT::Periodic::Update-Package-Lists "0";
APT::Periodic::Download-Upgradeable-Packages "0";
APT::Periodic::AutocleanInterval "0";
APT::Periodic::Unattended-Upgrade "1";
```

`Step 3:`
> Remove update-manager
```bash
sudo apt-get remove update-manager
```
## Touch PC (Windows 10)
- Sheung Wan (WTT)
- IP : 10.95.157.231
- Sha Tin (SCP)
- IP : 10.95.157.232
- TST (HHT)
- IP :

## Control Box Server (Ubuntu 22)
- Linux SU : ubuntu /// asdf
- Sheung Wan (WTT)
- IP : 10.95.157.232
- Flash ID:
```
ID      Counter#
1       1
2       2
3       3
...
...
...
10      10
```

- Sha Tin (SCP)
- IP : 10.95.160.236
- Flash ID:
```
ID      Counter#
2       1
3       2
4       3
5       4
6       5
7       A (6)
9       B (8)
```
- TST (HHT)
- IP :

# Development env setup
### <span style="color:orange;">**Setup python: :**</span>
install python for all users

find the python path
> python -c 'import os, sys;print(os.path.dirname(sys.executable))'

Windows add PATH for exe

Right click on My Computer ->Properties ->Advanced System setting ->Environment Variable ->New

### <span style="color:orange;">**New Django project with Virtual Env setup:**</span>
```sh
pip install virtualenv
# New virtual Env:
cd '\Projects\'
virtualenv env
# or
python -m virtualenv env
# activate virtual env:
.\env\scripts\activate
# install your packages e.g. 
python -m pip install -r requirements.txt
# new project: 
django-admin startproject newproj
# [update/ upgrade package] 
pip install django -U
#deactivate virtual env:
.\env\scripts\deactivate
```
move dir \Projects\env to \Projects\newproj\env

vscode open folder '\Projects\newproj'

new terminal in vscode
```bash
.\env\Scripts\activate
python manage.py startapp base
#*** please note that here is 'startapp' NOT 'startproject'

python manage.py runserver 0.0.0.0:8000
# run celery
# open new terminal
celery -A aqs.celery:app worker --loglevel=info --pool=solo
# Celery task always PENDING problem
# It is a Windows issue. Celery --pool=solo option solves the issue.
```
try http://127.0.0.1:8000/

### <span style="color:orange;">**Setup Linux VM for development**</span>
>Windows install VMware

>Download Ubuntu ISO and install on VMware

>Install Docker:
```bash
sudo apt-get update
sudo apt-get install ca-certificates curl gnupg -y
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg
```
```bash
echo \
  "deb [arch="$(dpkg --print-architecture)" signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  "$(. /etc/os-release && echo "$VERSION_CODENAME")" stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
```
```bash
sudo apt-get update
sudo apt-get install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
```
Verify that the Docker Engine installation is successful by running the hello-world image:
```bash
sudo docker run hello-world
```
Install Redis version 5
```bash
sudo docker run -p 6379:6379 -d redis:5
```
# Linux server setup
### <span style="color:orange;">**AWS vm**</span>
AWS EC2 : AQS8_Server_RVD, key=aws_rvd_server_key, Security Group = aqs_security

AWS Route53 : add sub domain rvd.tsvd.com.hk, www.rvd.tsvd.com.hk

## AWS cost:
RVD + Test + CF = $2.02 

RVD $1.46   
- t2.medium 
- vCPUs-2	
- HD-50G 
- us-east-1b

Test $0.28
- t2.micro
- vCPUs-1
- HD-30G 
- us-east-1e

CF $0.28 (Install at 2023-5-2)
- t2.micro
- vCPUs-1
- HD-24G 
- us-east-1e

### <span style="color:orange;">**Local server (Ubuntu Linux server)**</span>
network:

show ip address :
```bash
sudo apt install net-tools -y
sudo ifconfig -a
sudo ip link
# output:
#1: lo: <LOOPBACK,UP,LOWER_UP> mtu 65536 qdisc noqueue state UNKNOWN mode DEFAULT group default qlen 1000
#    link/loopback 00:00:00:00:00:00 brd 00:00:00:00:00:00
#2: ens3: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc fq_codel #state UP mode DEFAULT group default qlen 1000
#    link/ether 08:00:27:6c:13:63 brd ff:ff:ff:ff:ff:ff

sudo nano /etc/netplan/xxx.yaml 
# (01-netcfg.yaml, 50-cloud-init.yaml, or NN_interfaceName.yaml)
```
edit (main server): 
```sh
# This is the network config written by 'subiquity'
network:
  ethernets:
    enp0s31f6:
      dhcp4: no
      addresses:
        - 192.168.1.190/24
      routes:
        - to: default
          via: 192.168.1.1
      nameservers:
        addresses: [8.8.8.8, 1.1.1.1]
  version: 2
```
edit (db server): 
```sh
# This is the network config written by 'subiquity'
network:
  ethernets:
    enp1s0:
      dhcp4: no
      addresses:
        - 192.168.1.173/24
      routes:
        - to: default
          via: 192.168.1.1
      nameservers:
        addresses: [8.8.8.8, 1.1.1.1]
  version: 2
```
exit and save
```sh
sudo netplan apply
```
# Local server startup
1. Add user (htopuser) and password (asdf1234) for cmd htop
```sh
sudo adduser htopuser
# set htopuser as sudoer
# sudo usermod -aG sudo htopuser
# change password
sudo passwd htopuser
```
2. Install bashtop
```sh
sudo apt-get install -y bashtop btop
```
3. Setup auto login for user htopuser
```sh
sudo nano /etc/systemd/system/getty@tty1.service.d/override.conf
# add lines:
[Service]
ExecStart=
ExecStart=-/sbin/agetty --autologin htopuser --noclear %I $TERM
```

4. Server startup autorun bashtop
```sh
sudo nano /home/htopuser/.bashrc
# add line: bashtop / btop
```
5. Done, logout then auto login as htopuser
```sh
logout
```

>The server will auto login as htopuser and run bashtop after reboot. Even if logout, the server will auto login as htopuser and run bashtop again.

>So if you want to login as other user, you need to change user by cmd: 

>su - htopuser

>or goto tty2

> Ctrl+Alt+F2

## Auto power off script (for Ubuntu Desktop / Raspberry Pi Window OS):
```bash
sudo nano /home/ubuntu/.config/autostart/autooff.desktop
```
```nano
	[Desktop Entry]
	Type=Application
	Name=Auto Power Off at 23:55
	Exec=sh -c "shutdown -h 23:55"
```
- Restart Pi:
```
sudo reboot
```
## Auto power off script (for Linux server)
```bash
cd /etc/systemd/system/
sudo nano autorun.service
```
- add line:
```
[Unit]
Description=Autorun
After=network.target

[Service]
ExecStart=/bin/bash /home/ubuntu/autorun.sh

[Install]
WantedBy=default.target
```
- Save and exit

```bash
sudo systemctl enable autorun.service
```

```
nano /home/ubuntu/autorun.sh
```

```nano
# Auto shutdown at 00:30
shutdown -h 00:30
# add some script for auto run Control box program
sudo chmod 666 /dev/ttyS0
cd /home/ubuntu/cb
./cb
```

```
chmod +x /home/ubuntu/autorun.sh
```
- Save and exit

## Make Linux Use Local Time (On linux system BIOS time is UTC time)
- Please note that: Auto power on (In BIOS setting) will not work.

- Please note that the hardware clock is always stored as UTC time, and Linux converts it to local time when displaying it to the user. So 2 times seem to be different, but they are actually the same time.
```bash
sudo timedatectl set-local-rtc 1 --adjust-system-clock
```

### <span style="color:orange;">**Locate PuTTY setup (for AWS):**</span>

Download the key (aws_rvd_server_key) from AWS

Open PuTTYgen -> Type of key to generate -> choose **RSA** or **SSH-2 RSA** -> Load the downloaded key -> Save private key

Open PuTTY -> Host Name (rvd.tsvd.com.hk or IP) -> Saved Sessions (RVD) -> Category -> Connection -> SSH -> Auth -> Browse (your gen private key)

PuTTY -> Data -> Auto-login username (ubuntu) -> Session -> Save

# Basic server settings

```sh
sudo timedatectl set-timezone Asia/Hong_Kong
sudo hwclock -w
sudo apt-get update ; sudo apt-get upgrade -y
sudo apt-get install -y python3 python3-pip python3-dev libpq-dev postgresql postgresql-contrib nginx git 
sudo nano ~/.bashrc
```

add line : 
> alias python='python3'

save and exit 

restart the cmd terminal
```bash
python -V
# CHECK Firewall:
sudo ufw status verbose
# Create an exception for port 8000. So, we can test that django setup is installed properly.
```
~~sudo ufw allow 8000~~
>(no need, use AWS firewall so Ubuntu firewall can be disabled)




# SETUP SOURCE CODE
### <span style="color:orange;">**Copy / git source code to home dir**</span>
Preparation:
- Backup previous version settings.py : cp ~/aqs8server/aqs/settings.py ~/settings.py.bak
- Remove previous version : sudo rm -r ~/aqs8server/
- Before install packages (python -m pip freeze > requirements.txt)
- Set Github repo to public

```bash
git clone https://github.com/karock5345/aqs8server.git
# or
git clone --branch pccw2023 https://github.com/karock5345/aqs8server.git
# remove .git folder
sudo rm -r ~/aqs8server/.git
# remove readme.md (it stores password and other sensitive info)
sudo rm ~/aqs8server/readme.md
sudo apt-get install -y virtualenv
cd to project folder
virtualenv env
source env/bin/activate
```

- OR download private repo
```bash
# Generate SSH key (optional): If you haven't already, you can generate an SSH key pair to securely authenticate with GitHub. Run the following command to generate an SSH key:

ssh-keygen -t rsa -b 4096 -C "your_email@example.com"
# Follow the prompts and leave the passphrase blank if you want to avoid entering it every time.

# Add SSH key to GitHub: Copy the contents of the public key (~/.ssh/id_rsa.pub) using the following command:
cat ~/.ssh/id_rsa.pub
# Then, go to your GitHub account's settings, navigate to "SSH and GPG keys," and click on "New SSH key." Paste the copied key into the "Key" field and save it.

# Clone the repository: Once you have Git installed and your SSH key set up, you can clone the private repository to your local machine using the git clone command. Replace <repository> with the URL of your private repository. For example:
git clone git@github.com:<username>/<repository>.git
```

> twisted-iocpsupport is a package providing bindings to the Windows "I/O Completion Ports" APIs. These are Windows-only APIs.

> You cannot use this package on Debian. Fortunately, you also don't need to as you have access to 

>a good Linux-based non-blocking I/O system - epoll - which is supported in Twisted without the use of any additional packages.

```bash
sudo nano requirements.txt
# [del line :] twisted-iocpsupport=x.x.x

pip install -r requirements.txt
# [List of installed packages] pip list
# [update package] 
pip install django -U

pip install gunicorn psycopg2
python manage.py runserver 0.0.0.0:8000
# test the server : ip:8000
deactivate
```


# SETUP DB (PostgreSQL) in this Project we use other server for DB
```bash
sudo systemctl reload postgresql.service
sudo su -l postgres
psql
```
PostgreSQL command:
```sql
CREATE DATABASE aqsdb8;
CREATE USER aqsdbuser WITH PASSWORD 'dbpassword-Dlcg1dwMOXSKIAIM';
ALTER ROLE aqsdbuser SET client_encoding TO 'utf8';
ALTER ROLE aqsdbuser SET default_transaction_isolation TO 'read committed';
SHOW TIMEZONE;
SET TIMEZONE='UTC';
SHOW TIMEZONE;
ALTER ROLE aqsdbuser SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE aqsdb8 TO aqsdbuser;
\q
exit
```
Allow remote access to PostgreSQL server
```bash
nano /etc/postgresql/14/main/postgresql.conf
# Edit: search (CTRL + W) listen_addresses
listen_addresses = '*'
```
```bash
sudo find / -name pg_hba.conf
sudo nano /path/to/pg_hba.conf
# this case:
sudo nano /etc/postgresql/14/main/pg_hba.conf
# add line:
host    aqsdb8    aqsdbuser    10.95.157.237/32    md5
```

```bash
sudo systemctl reload postgresql.service
```
Edit settings.py
```bash
sudo nano ~/aqs8server/aqs/settings.py
```
```
DEBUG = False
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'aqsdb8',
        'USER': 'aqsdbuser',
        'PASSWORD': 'dbpassword-Dlcg1dwMOXSKIAIM',
        'HOST': '192.168.1.173',
        'PORT': '5432',
    }
}
```

```bash
source .env/bin/activate
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
```
supertim /// YtZqEIpk5345

Test the Postgres DB:
```bash
python manage.py runserver 0.0.0.0:8000
```

# SECRET KEY

### <span style="color:orange;">**Django secret key**</span>

Save the SECRET_KEY from settings.py to text file (e.g. : django-insecure-BITRaxa&rupHUGo&rab@JaRe4iT@amuQlDroFunljib$duxogO):

```bash
sudo touch /etc/secret_key.txt
sudo nano /etc/secret_key.txt
```

Remove SECRET_KEY in settings.py and change to load file
```
with open('/etc/secret_key.txt') as f:
    SECRET_KEY = f.read().strip()
```
### <span style="color:orange;">**ReCaptcha secret key**</span>

Save the RECAPTCHA_PRIVATE_KEY to text file (6LflOq0iAAAAAFAKsEWvj1ZY_JFKihRaxUR_vlqG):
```bash
sudo touch /etc/recaptcha_key.txt
sudo nano /etc/recaptcha_key.txt
```
Remove RECAPTCHA_PRIVATE_KEY in settings.py and change to load file
```
with open('/etc/recaptcha_key.txt') as f:
    RECAPTCHA_PRIVATE_KEY = f.read().strip()
```
close and save

> Disable Recaptcha for debug / test
```bash
nano ~/aqs8server/base/views.py    
 ```   
>enable_captcha = False

# INIT AND SETUP the AQS8

### <span style="color:orange;">**Please note that, new version is skip this:**</span>
~~If use sql lite should disable 'SCH' function:~~

~~remark base/sch/urls.py ->~~
```bash
# init_branch_reset()
```

### <span style="color:orange;">**Change the token_api at base/api/views.py**</span>
```bash
sudo nano base/api/views.py 
token_api = 'WrE-1t7IdrU2iB3a0e'
```


### <span style="color:orange;">**SETUP nginx + gunicorn**</span>

```bash
nano ./aqs/settings.py
```
Edit:
```python
STATIC_URL = '/static/'
STATICFILES_DIRS =[
    BASE_DIR / 'static'
]
STATIC_ROOT = BASE_DIR / 'static_deploy'
```
```python
SIMPLE_JWT = {
    # Debug mode set 120 minutes, otherwise 5 minutes    
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=5),
    # Debug mode set 30 minutes, otherwise days=1
    "REFRESH_TOKEN_LIFETIME": timedelta(days=1),
    "ROTATE_REFRESH_TOKENS": False,
    "BLACKLIST_AFTER_ROTATION": False,
    "UPDATE_LAST_LOGIN": False,

    "ALGORITHM": "HS256",
    "SIGNING_KEY": SECRET_KEY,
    "VERIFYING_KEY": None,
    "AUDIENCE": None,
    "ISSUER": None,
   
    "AUTH_HEADER_TYPES": ("Bearer",),
}
```
exit and save
```bash
python3 manage.py collectstatic
# for upload new files to static_deploy/
# python3 manage.py collectstatic --clear
```

Try Gunicorn. The only difference is we are not doing startserver command from Django, instead Gunicorn will take care of that.
```bash
gunicorn --bind 0.0.0.0:8000 aqs.wsgi
```

```bash
deactivate
sudo touch /etc/systemd/system/gunicorn.socket
sudo nano /etc/systemd/system/gunicorn.socket
```

edit :
```bash
[Unit]
Description=gunicorn socket

[Socket]
ListenStream=/run/gunicorn.sock
# Our service won't need permissions for the socket, since it
# inherits the file descriptor by socket activation
# only the nginx daemon will need access to the socket
SocketUser=www-data
# Optionally restrict the socket permissions even more.
# SocketMode=600

[Install]
WantedBy=sockets.target
```
```bash
sudo touch /etc/systemd/system/gunicorn.service
sudo nano /etc/systemd/system/gunicorn.service
```
edit:
```bash
[Unit]
Description=gunicorn daemon
Requires=gunicorn.socket
After=network.target

[Service]
Type=notify
# the specific user that our service will run as
User=ubuntu
# Group=someuser
# another option for an even more restricted service is
# DynamicUser=yes
# see http://0pointer.net/blog/dynamic-users-with-systemd.html
RuntimeDirectory=gunicorn
WorkingDirectory=/home/ubuntu/aqs8server
ExecStart=/home/ubuntu/aqs8server/env/bin/gunicorn \
	--workers 10 \
	--bind unix:/run/gunicorn.sock \
	aqs.wsgi:application
ExecReload=/bin/kill -s HUP $MAINPID
KillMode=mixed
TimeoutStopSec=5
PrivateTmp=true

[Install]
WantedBy=multi-user.target
```
****ubuntu should be changed you user**
```bash
sudo systemctl start gunicorn.socket
sudo systemctl enable gunicorn.socket
sudo systemctl status gunicorn.socket
file /run/gunicorn.sock
# Output: /run/gunicorn.sock: socket
sudo systemctl status gunicorn
#Output :
● gunicorn.service - gunicorn daemon
   Loaded: loaded (/etc/systemd/system/gunicorn.service; disabled; vendor preset: enabled)
   Active: inactive (dead)
curl --unix-socket /run/gunicorn.sock localhost
#You should see the HTML output (have not output)
#If the output from curl or the output of systemctl status indicates that a problem occurred, check the logs for additional details:
#and Check the /etc/systemd/system/gunicorn.service file for problems.
sudo journalctl -u gunicorn
sudo systemctl daemon-reload
sudo systemctl restart gunicorn
```
Uninstall Apache 
```bash
sudo systemctl stop apache2 ; sudo systemctl disable apache2 ; sudo apt remove apache2
```
### <span style="color:orange;">**NGINX**</span>

```bash
sudo touch /etc/nginx/sites-available/aqs8server
sudo nano /etc/nginx/sites-available/aqs8server
```
edit:
```python
server {
    server_name localhost 127.0.0.1 rvd.tsvd.com.hk www.rvd.tsvd.com.hk;

    location = /favicon.ico { access_log off; log_not_found off; }
    location /static/ {
        autoindex on;
        alias /home/**ubuntu/aqs8server/static_deploy/;
    }

    location / {
        include proxy_params;
        proxy_pass http://unix:/run/gunicorn.sock;
    }
}
```
****ubuntu should be changed you user**
```bash
sudo ln -s /etc/nginx/sites-available/aqs8server /etc/nginx/sites-enabled
# Test the Nginx configuration for syntax errors by using the following command
sudo nginx -t
sudo systemctl restart nginx
# sudo ufw delete allow 8000
sudo ufw allow 'Nginx Full'
# sudo systemctl restart ufw
# Using AWS firewall, so no need enable Linux firewall
```


If can not show files in static/

Nginx operates within the directory, so if you can't cd to that directory from the nginx user 

then it will fail (as does the stat command in your log). Make sure the www-data can 

cd all the way to the /username/test/static. You can confirm that the stat will fail or succeed by running

>sudo -u www-data stat /home/ubuntu/aqs8server/static_deploy
```bash
sudo gpasswd -a www-data ubuntu
sudo chmod g+x /home/ubuntu && chmod g+x /home/ubuntu/aqs8server/ && chmod g+x /home/ubuntu/aqs8server/static_deploy
sudo nginx -s reload
```
### <span style="color:orange;">**Init the DB**</span>
```bash
source env/bin/activate
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
```
Superuser: supertim /// YtZqEIpk5345

Open web browser http://[ip address]/admin

create settings : Name=global, Branch=---, disabled API log

create user groups : api web admin support manager frontline 

create user : userapi /// asdf2206 (group:api)

create user : userweb /// asdf2206 (group:web, set:in-active)

create branch (bcode=WTT, SCP, HHT)

create counter type (c)

create counter (CounterStatus) 1-4

create ticket type (TicketFormat)

create TicketRoute

create admin, api user for our customer
admin : pccwadmin /// YEjLZBYGF4


# Troubleshooting and Debug
check the logs for additional details:
```bash
sudo nano /var/log/nginx/error.log

# check folder permissions
ls -ltr ./static_deploy/
# list all users
cut -d: -f1 /etc/passwd
# list all groups
less /etc/group
```

# DB replication Setup (Master)
```bash
sudo su -l postgres
psql
CREATE USER repuser REPLICATION LOGIN ENCRYPTED PASSWORD 'reppass-Fr8sEp2pat';
\q
logout
sudo nano /etc/postgresql/14/main/postgresql.conf
```

edit:
```bash
wal_level = logical
wal_log_hints = on
max_wal_senders = 8
max_wal_size = 1GB
hot_standby = on
```

```bash
sudo nano /etc/postgresql/14/main/pg_hba.conf
```
add :
> host replication repuser [slave ip]/32 md5

Reset PSQL :
```bash
sudo systemctl restart postgresql
```

# DB Backup server init and setup
```bash
sudo timedatectl set-timezone Asia/Hong_Kong
sudo apt-get update
sudo apt-get -y upgrade
sudo apt install -y postgresql

sudo service postgresql stop
sudo -s
cd /
rm -R /var/lib/postgresql/14/main
# mv /var/lib/postgresql/14/main /var/lib/postgresql/14/main_old
sudo chown postgres:postgres /var/lib/postgresql/14/main
sudo -u postgres pg_basebackup -h 192.168.5.131 -D /var/lib/postgresql/14/main -U repuser --checkpoint=fast -R --slot=some_name -C --wal-method=stream
nano /etc/postgresql/14/main/postgresql.conf
```
Edit:
> listen_addresses = '*'          

What IP address(es) to listen on;

```bash
sudo nano /etc/postgresql/14/main/pg_hba.conf
# change all scram-sha-256 to md5
sudo service postgresql start

#Look at the Postgres log on each server. These logs can contain information that will help you troubleshoot the issue.
less ../../var/log/postgresql/postgresql-14-main.log
```



# DB replication Testing 
Insert data to Primary DB for Testing

```
sudo su -l postgres
psql
\c aqsdb8
INSERT INTO base_testingModel(name, des) VALUES ('David','is good guy');
```
View data from postgres
```
sudo su -l postgres
psql
\c aqsdb8
\dt
TABLE base_userprofile;
TABLE base_testingModel;
INSERT INTO base_testingModel(name, des) VALUES ('David','is good guy');
\q
logout
```

### <span style="color:orange;">**Check the server stat**</span>

```
sudo su -l postgres
psql
\x
select * from pg_stat_replication;
```
### <span style="color:orange;">**check slot at main server**</span>

```
select * from pg_replication_slots;
```

remove slot from main server

```
select pg_drop_replication_slot('some_name');
\x
```
### <span style="color:orange;">**Troubleshoot:**</span>

Check error : Django code run on Gunicorn
```
sudo systemctl status gunicorn
```
```bash
# check PSQL status
sudo service postgresql status
# start PSQL
sudo service postgresql start
# Restart
sudo service postgresql restart
# stop
sudo service postgresql stop
```

# Setup Redis Server (Websocket)
### <span style="color:orange;">**Change Redis server IP**</span>
> edit settings.py
```bash
nano ~/aqs8server/aqs/settings.py
```
```python
CHANNEL_LAYERS = {
    'default':{
        'BACKEND':'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            'hosts':[('127.0.0.1', '6379')],
            },
     }
}
```
sudo nano /etc/nginx/sites-available/aqs8server
```nginx
server {
    listen 80;
    server_name localhost 127.0.0.1 34.207.57.210 test.tsvd.com.hk www.test.tsvd.com.hk;

    location = /favicon.ico { access_log off; log_not_found off; }
    location /static/ {
        autoindex on;
        alias /home/**ubuntu/aqs8server/static_deploy;
    }

    location / {
        include proxy_params;
        proxy_pass http://unix:/run/gunicorn.sock;
    }
	location /ws/ {
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_redirect off;
        proxy_pass http://127.0.0.1:8001;
    }
}
```
****ubuntu should be changed you user**

Restart nginx and allow the changes to take place
```bash
sudo systemctl restart nginx
```
Test your Nginx configuration for syntax errors by typing
```bash
sudo nginx -t
```

### <span style="color:orange;">**Install Redis Server**</span>
```bash
sudo apt install redis-server -y
```
```bash
sudo nano /etc/redis/redis.conf
```

CTRL+W to find 'supervised no' and replace with ‘supervised systemd’ and SAVE .
```bash
sudo systemctl restart redis.service
sudo systemctl status redis
```
Press CTRL+C to exit.

Confirm Redis is running at 127.0.0.1. Port should be 6379 by default.
```bash
sudo apt install net-tools -y
sudo netstat -lnp | grep redis
sudo systemctl restart redis.service
```
```bash
nano ~/aqs8server/aqs/asgi.py
```
Add under "import base.routing":
```python
import django
django.setup()
```
Install Daphne 
```bash
sudo apt install daphne -y
# And install it in your project virtual enviroment.
source ~/aqs8server/env/bin/activate
pip3 install daphne
deactivate
sudo nano /etc/systemd/system/daphne.service
```
```nano
[Unit]
Description=Daphne service
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/aqs8server
ExecStart=/home/ubuntu/aqs8server/env/bin/python /home/ubuntu/aqs8server/env/bin/daphne -b 0.0.0.0 -p 8001 aqs.asgi:application
Restart=always
StartLimitBurst=2

#StartLimitInterval=600
# Restart, but not more than once every 30s (for testing purposes)
StartLimitInterval=30

[Install]
WantedBy=multi-user.target
```
****ubuntu should be changed you user**

After we need to start daphne.service .
```bash
sudo systemctl daemon-reload

sudo systemctl start daphne.service
#If you want to check status of daphne then use.

sudo systemctl status daphne.service
```
### <span style="color:orange;">**Starting the daphne Service when Server boots**</span>
```
sudo systemctl enable daphne.service
```

# SSL
Before setup SSL, server must have domain name

```bash
sudo apt install snapd
sudo snap install --classic certbot
sudo ln -s /snap/bin/certbot /usr/bin/certbot
sudo certbot --nginx
[input email]
[y]
[n]
[enter]
```
cerboot will auto config Nginx

Refer to : https://www.youtube.com/watch?v=dYdv6pkCufk


>**Update source code all HTML from ws:// to wss://**
```bash
nano ~/aqs8server/base/ws.py
# change :
wsHypertext = 'ws://'
# to :
wsHypertext = 'wss://'
````

Reboot the server
```bash
sudo reboot
```


# Setup google reCaptcha
### <span style="color:orange;">**Use reCaptcha**</span>
Open new reCaptcha:
Create new reCaptcha on [google.com/recaptcha](https://www.google.com/recaptcha)

creat new file /etc/recaptcha_key.txt

and save the private key to the file.

Edit .\aqs\settings.py

```python
RECAPTCHA_PUBLIC_KEY = 'xxx'
with open('/etc/recaptcha_key.txt') as f:
    RECAPTCHA_PRIVATE_KEY = f.read().strip()
RECAPTCHA_REQUIRED_SCORE = 0.85
```
### <span style="color:orange;">**Enable / Disable reCaptcha**</span>

nano ~\aqs8server\aqs\views.py

> enable_captcha = False


# Setup new git repo
### <span style="color:orange;">**Create new repo on [github.com](http://github.com)**</span>

Open the web browser login github.com

New the repo named e.g. aqs8server
### <span style="color:orange;">**Local source code prepare**</span>

Download and install git: https://git-scm.com/downloads
```bash
# download git and setup
git --version
git config --global --list
git config --global user.name "xxx"
git config --global user.email "xxx.email.com"
git config --global user.password "xxx"
```
### <span style="color:orange;">**Upload your first commit:**</span>

```bash
# Create local Git repo:
cd \Projects\AQS8.0\server\
git init aqs [proj folder]
# if folder not exist, it will create new folder
# and hidden folder aqs\.git will be created
cd aqs
git add .
git commit -m "first commit"
git branch -M main
git remote add origin https://github.com/karock5345/aqs8server.git
git push -u origin main
# ! [rejected]        main -> main (fetch first)
# error: failed to push some refs to 'https://github.com/karock5345/djchannels4.git'
# hint: Updates were rejected because the remote contains work that you do
# hint: not have locally. This is usually caused by another repository pushing
# hint: to the same ref. You may want to first integrate the remote changes
# hint: (e.g., 'git pull ...') before pushing again.
# hint: See the 'Note about fast-forwards' in 'git push --help' for details.

# change 'origin' -> other remote name e.g. 'remote-rvd'
```
### <span style="color:orange;">**Commit new version to github**</span>

Open vscode -> open the project -> Source Control (Crtl + Shift + G) -> add some text on "Message" e.g. fixed bug xxx -> ... -> commit -> commit all

# Setup zsh (Oh My Zsh)
```bash
sudo apt install zsh fonts-powerline -y
chsh -s /usr/bin/zsh
sh -c "$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)"

nano ~/.zshrc
```
Edit
```bash
ZSH_THEME="agnoster"
```

### <span style="color:orange;">**Setup Putty**</span>
Download and install font on your Windows:
https://github.com/powerline/fonts/tree/master/DejaVuSansMono

Setup Putty 'Saved Sessions'
Window -> Appearance -> Change font -> Deja...Powerline
Window -> Color -> Default Blue -> Red 44 Green 123 Blue 201

# Copy file from PC to Linux server
pscp c:/music.mp3  ubuntu@192.168.1.222:/home/ubuntu/

# Copy file from Mac to Linux server
scp -rp /path/to/local/dir usrname@orgname.edu:/path/to/remote/dir

# Network (Internet) speed test
```bash
sudo apt install speedtest-cli
speedtest
```
