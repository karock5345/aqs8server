# AQS version 8
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
pip install django
# or
python -m pip install django
# or
pip install -r requirements.txt
# new project: 
django-admin startproject newproj
# [update package] 
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

python manage.py runserver
```
try http://127.0.0.1:8000/





# Linux server setup
### <span style="color:orange;">**AWS vm**</span>
AWS EC2 : AQS8_Server_RVD, key=aws_rvd_server_key, Security Group = aqs_security

AWS Route53 : add sub domain rvd.tsvd.com.hk, www.rvd.tsvd.com.hk

### <span style="color:orange;">**Ubuntu Linux server**</span>
network:

show ip address :
```bash
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
edit: 
```sh
# This is the network config written by 'subiquity'
network:
  ethernets:
    enxf01e3411f0f8:
      dhcp4: no
      addresses:
        - 192.168.1.222/24
      routes:
        - to: default
          via: 192.168.1.1
      nameservers:
        addresses: [8.8.8.8, 1.1.1.1]
  version: 2
```
OR

```sh
network:
  version: 2
  renderer: networkd
  ethernets:
    ens3:
      dhcp4: no
      addresses:
        - 192.168.121.221/24
      gateway4: 192.168.121.1
      nameservers:
          addresses: [8.8.8.8, 1.1.1.1]
```
exit and save
```sh
sudo netplan apply
```

### <span style="color:orange;">**Locate PuTTY setup (for AWS):**</span>

Download the key (aws_rvd_server_key) from AWS

Open PuTTYgen -> Type of key to generate -> choose **RSA** or **SSH-2 RSA** -> Load the downloaded key -> Save private key

Open PuTTY -> Host Name (rvd.tsvd.com.hk or IP) -> Saved Sessions (RVD) -> Category -> Connection -> SSH -> Auth -> Browse (your gen private key)

PuTTY -> Data -> Auto-login username (ubuntu) -> Session -> Save

```sh
sudo timedatectl set-timezone Asia/Hong_Kong
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
sudo ufw allow 8000
# (no need, when the firewall is disabled)
```

# SETUP SOURCE CODE
### <span style="color:orange;">**Copy / git source code to home dir**</span>

Before install packages (python -m pip freeze > requirements.txt) 

```bash
git clone https://github.com/karock5345/rvd.git
sudo apt-get install -y virtualenv
cd to project folder
virtualenv env
source env/bin/activate
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


# SETUP DB (PostgreSQL)
```bash
sudo systemctl reload postgresql.service
sudo su -l postgres
psql
```
PostgreSQL command:
```sql
CREATE DATABASE aqsdb8;
CREATE USER aqsdbuser WITH PASSWORD 'dbpassword';
ALTER ROLE aqsdbuser SET client_encoding TO 'utf8';
ALTER ROLE aqsdbuser SET default_transaction_isolation TO 'read committed';
SHOW TIMEZONE;
SET TIMEZONE='UTC';
SHOW TIMEZONE;
ALTER ROLE aqsdbuser SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE aqsdb8 TO aqsdbuser;
\q
```
```bash
exit
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
        'PASSWORD': 'dbpassword',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
```

```bash
source env/bin/activate
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
```
tim /// asdf

Test the Postgres DB:
```bash
python manage.py runserver 0.0.0.0:8000
```

# SECRET KEY



### <span style="color:orange;">**Django secret key**</span>






Save the SECRET_KEY from settings.py to text file (e.g. : django-insecure-9e^jTw&jk-@-^5u45=*m^el@@$$!7#gav!y=8r8e*&l64^@*v#):
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
```bash
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'static'
# STATICFILES_DIRS =[
#     BASE_DIR / 'static'
# ]
```
exit and save
```bash
python3 manage.py collectstatic
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
User=**ubuntu
# Group=someuser
# another option for an even more restricted service is
# DynamicUser=yes
# see http://0pointer.net/blog/dynamic-users-with-systemd.html
RuntimeDirectory=gunicorn
WorkingDirectory=/home/**ubuntu/aqs8server
ExecStart=/home/**ubuntu/aqs8server/env/bin/gunicorn aqs.wsgi
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
```bash
server {
    server_name localhost 127.0.0.1 rvd.tsvd.com.hk www.rvd.tsvd.com.hk;

    location = /favicon.ico { access_log off; log_not_found off; }
    location /static/ {
        autoindex on;
        alias /home/**ubuntu/aqs8server/static/;
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

>sudo -u www-data stat /home/tim/aqs8server/static will fail
```bash
sudo gpasswd -a www-data ubuntu
sudo chmod g+x /home/ubuntu && chmod g+x /home/ubuntu/aqs8server/ && chmod g+x /home/ubuntu/aqs8server/static
sudo nginx -s reload
```
### <span style="color:orange;">**Init the DB**</span>
```bash
source env/bin/activate
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
```
Superuser: tim /// asdf

Open web browser http://[ip address]/admin

create settings : Name=global, Branch=---, disabled API log

create user groups : api admin report counter web

create user : userapi /// asdf2206 (group:api)

create user : userweb /// asdf2206 (group:web, set:in-active)

create branch (bcode='KB')

create counter type (Counter)

create counter (CounterStatus) 1-4

create ticket type (TicketFormat)

create TicketRoute

create admin, apiuser user for our customer



# Troubleshooting
check the logs for additional details:
```bash
sudo nano /var/log/nginx/error.log

# check folder permissions
ls -ltr ./static/
# list all users
cut -d: -f1 /etc/passwd
# list all groups
less /etc/group
```

# DB replication Setup (Master)
```bash
sudo su -l postgres
psql
CREATE USER repuser REPLICATION LOGIN ENCRYPTED PASSWORD 'reppass';
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
Refer to : https://www.youtube.com/watch?v=dYdv6pkCufk

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
### <span style="color:orange;">**Disable reCaptcha**</span>

Edit base\login_register.html

del / remark :
```html
  <!-- {% for field in captcha_form %}
  <div class="form__group">
      {% if field.label == "Captcha" %}
          <label for="profile_pic">{{field}}</label>                         
      {% else %}
          <label for="profile_pic">{{field.label}} : {{field}}</label>                    
      {% endif %}
  </div>
  {% endfor %} -->
```

Edit base\views.py -> function UserLoginView()

Remark :
```python
  # captchaform = CaptchaForm(request.POST)
  # if captchaform.is_valid():
  #     human = True
  #     # print ('Is human.')
  # else:
  #     # print('Is NOT human.')
  #     messages.error(request, 'User is NOT human.')
  #     return redirect('home')
```
```python
  # captchaform = CaptchaForm()
```
```python
  # context = context | {'captcha_form':captchaform} 
```
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