# AQS version 8 For PCCW 2023

## Update Server v8.1.7 (pccw2023_v6)
- navbar.html line 7 : v8.1.7
- ws.py
- consumers.py
- settings.py 
  - line 18 : v8.1.7
  - New file: aqs/custom_handlers.py
  - line 214 (remove "LOGGING"), add :
  ```py
      import os
      LOGGING = {
        'version': 1,
        'disable_existing_loggers': False,    
        'formatters': {
            'verbose': {
                'format':  '{levelname} {asctime} {module}>{funcName} {message}',
                'style': '{',
            },
        },

        'handlers': {
            'file': {
                'level': 'INFO',  # Set to INFO to avoid logging DEBUG messages            
                'class': 'aqs.custom_handlers.CustomRotatingFileHandler',            
                'filename': os.path.join(BASE_DIR, 'logs', 'aqs.log'),
                'maxBytes': 10 * 1024 * 1024,  # 10 MB
                'backupCount': 5,
                'max_log_files': 20,  # Keep only the latest 20 log files
                'formatter': 'verbose',
            },
            'console': {
                'level': 'INFO',  # Set to INFO to avoid logging DEBUG messages
                'class': 'logging.StreamHandler',
                'formatter': 'verbose',
            },     
        },
        'root': {
            'handlers': ['file', 'console'],
            'level': 'INFO',  # Set to INFO to avoid logging DEBUG messages
        },  
      }
  ```
- Bug fixed : APScheduler some time the system is busy will cause the sch job missed - "Run time of job "xxx" was missed by"
   ```py
   # base/sch/views.py line 25
  job_defaults = {
      'coalesce': True,
      'misfire_grace_time': None,
      'daemon': True,
      'max_instances': 50,
  }
  sch = BackgroundScheduler(job_defaults=job_defaults)
  # sch = BackgroundScheduler(daemon=True)
   ```

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

