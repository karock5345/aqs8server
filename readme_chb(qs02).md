# QS02 AWS server
- Debian User admin
- IP: 43.199.68.139
- Google Recaptcha
- Public 6Lek1QUqAAAAAHURN0IzsU1KNr2HOnYdlq6iDFOr
- Private 6Lek1QUqAAAAADLWyaFRyYFV7Umpr9lmO6y1Wywg
- DB: aqsdb8_chb  /// aqsdbuser_chb /// dbpassword-chUsplw0hltricispamu
- Django superuser: supertim /// ylthECLde5iflsplThAy
- APP_NAME : aqs_app_chb
- DOMAIN : https://chb.tsvd.com.hk

# AQS version 8.3.2

<h3 style="color:orange;">Version 8.3.2</h3>

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
- New 5 standard reports : Queue summary per day, Number of queue per timeslot, Staff performance report, Ticket type report, Ticket type report per day

<h3 style="color:orange;">Version 8.3.1</h3>

- Bug fixed : User update HTML js error (base/templates/base/user_update.html -> line 147)
  ```js
  // check tickettype do not have character "," then set to ""
    if (tickettype == null) {
        tickettype = "";
    }
    if ((tickettype.indexOf(",") == -1 || tickettype == "")) {
        tickettype = "";
        document.getElementById('id_a_tickettype').innerHTML = "No ticket type";
        document.getElementById('id_text_tickettype').value = "";
    }
  ```
- Bug fixed : /base/views -> line 289, in SoftkeyView : l_userttype = userttype.split(',') Error : AttributeError: 'NoneType' object has no attribute 'split' **Details : When Superuser no Branch and no TT db TicketType is None**

- Effect sound for voice announcement
- Display Panel add show counter and show latest ticket number on API aqs\api\v_display.py -> getDisplay5
- Bug fixed Web-softkey base/views.py line 305 and base/api/v_softkey.py line 1317 (add .order_by('tickettime')) ticket list is not order by TicketTime
- Add disable Admin page, for production  set ADMIN_ENABLED = False on change the aqs/settings.py
- Add Voice volume cmd to VoiceComp via ws
- Temporary bug fixed WS will be mix up when the server is serving multiple apps
  - Details see [Fix_temp_ws_mixup.md]
- Instruction for upgrade Call/Get function support Multiple Workers (Not including "New Ticket" function) for version v8.2.x
  - Details refer to [Fix_Call_multi-workers.md]
- Move enable_captcha = True from base/views.py to settings.py
- Touch API: api/ticketkey/ parameter 'printernumber' data changed from <PNO>P1</PNO> -> P1,P2, ... support multiple printers
- Function : newticket_v830() change to no print ticket (websocket), it will be printed by new function
- Mobile APP for Member API specification version 1.1
  - API 2. Member info API (Member APP), added 'member_qr' field return
- New function Timeslot Template manager for Booking

<h3 style="color:orange;">Version 8.3.0</h3>

- Booking to Queue Function
- Support multiple workers for Gunicorn (@transaction.atomic)
- New WS for Voice 8.3.0 (/ws/voice830/) 
- All WS links added APP_NAME to avoid conflict with other apps e.g. /ws/sms/<BCODE>/ -> /ws/<APP_NAME>/sms/<BCODE>/ 

<h3 style="color:orange;">Version 8.2.2</h3>

- Secure Flashlight (Control Box) Websocket connection protect use the session Cookie
- Vertical Display panel add show counter and show latest ticket number on API aqs\api\v_display.py -> getDisplay
- Display Panel add show counter and show latest ticket number on API aqs\api\v_display.py -> getDisplay
- Only 1 raw data report aqs/temp/r-main.html
   - backup to r-main3.html then remove other 2 reports from r-main.html
   - replace 3 to 1 on aqs/temp/menu-list.html
- Bug fixed manager, support, supervisor, reporter, counter can see API user
   - Detail see tg2024 Branch
   - /aqs/views.py -> auth_data (line 3725) add : 
- Bug fixed add user step 2 (User authority) is not correct
   - Detail see tg2024 Branch
   - edit /base/views.py line 3352   
   - and line 3326 :
   - and line 3159 :
   - edit /base/forms.py line 275 to 340

<h3 style="color:orange;">Version 8.2.1</h3>

- Fixed bug : base > v_softkey_sub.py > cc_aux : Counter can not call ticket when counter is hold a ticket > ACW > AUX > Ready
- gUnicorn workers = 1 for production (because of the call Ticket function is not work when workers > 1)
- Web Softkey (include Call Centre) waiting list can be hide by Admin, Support, Manager
- Fixed bug : web User -> click 'Show All' only one hiden user per click
- Disable Roche send SMS function (Send SMS to staff when new ticket issued)
- Reset SMS quota per month
- Booking Management
- Bug fixed base\forms.py frontline -> counter

<h3 style="color:orange;">Version 8.2.0</h3>

- CRM System (Customer Relationship Management) Initial
- Booking System (Appointment system) Initial

<h3 style="color:orange;">Version 8.1.6</h3>

- Upgrade Django to 4.2.x
- Run sch_shutdown() (Schudule task) when the branch settings is saved, so the branch will be update and schedule task time.
- Secure all existing Websocket connection protect use the session Cookie
- Change webtv Websocket for Web and client software, using 2 routes to separate public (ws/wtv/<bcode>/<ct>) and internal (ws/webtv/<bcode>/<ct>)
- Keep My E-ticket public Websocket for Web
- Others websocket is internal only protect by session cookie
- Modify the HTMLs for SVG image (e.g. branch settings, ticket format, ticket route, etc.)
- Fixed bug : Softkey web version, the queue list update by Websocket no "Call" button and fixed the ticket time format
- User Groups merged from PCCW2023 (Group : support, supervisor, manager, reporter and counter)
  - admin (TS use only) : all branchs, (Group: all, including "api" and "web") all user, Softkey, Supervisor, Report and Admin settings
  - support (TS use only) : all branchs, (Group : support, supervisor, manager, reporter and counter) users, Softkey, Supervisor, Report and Advanced settings
  - supervisor (TS use only) : all branchs, (Group : supervisor, manager, reporter and counter) users, Softkey, Supervisor, Report and Basic settings
  - ~~(remove) frontline : own branchs, Softkey~~
  - manager : own branchs, (Group : manager, reporter and counter) users, Softkey, Supervisor, Report and Advanced settings
  - reporter : own branchs, (Group : reporter and counter) users, Softkey, Supervisor, Report and basic settings
  - counter : own branchs, Softkey
- Settings page will be split to 3 pages for different user auth (Settings, Advanced settings, Admin settings)
- Fixed bug : Web Touch panel can not redirect to e-ticket page
- Fixed bug : Softkey_cc WS queue list update not correct
- APIs for Memberships (CRM) APP
- Fixed bug : Raw data report No data (aqs -> tasks.py -> export_raw) line 78, in export_raw bcode = table[0].branch.bcode 1. remove line 78, 2. modify line 39 def export_raw(quesrystr, reporttitle1, reporttitle2, reporttitle3, reporttitle4, reporttitle5, bcode ): 3. modify (base -> views.py ) line 1367 : task = export_raw.apply_async(args=[querystr,report_result1,report_result2,report_result3,report_result4,report_result5], countdown=0)


<h3 style="color:orange;">Version 8.1.5</h3>

- Romove API function for migrate DB for HHT 
- Fixed bug : deploy to production server, the static_deploy folder is not correct 
for download CSV file (aqs/tasks.py -> export_raw)

<h3 style="color:orange;">Version 8.1.4</h3>

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

<h3 style="color:orange;">Version 8.1.3</h3>

- Report function (1. Staff performance report, 2. Total ticket report)
- Add new API function for migrate 2 branchs (SCP, WTT) old DB to new server (http://127.0.0.1:8000/api/db2/?app=postman&version=8.1)

<h3 style="color:orange;">Version 8.1.2</h3>

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

<h3 style="color:orange;">Version 8.1.1</h3>

- Fixed bug : Counter can not logout and Counter status is not correct (waiting) in Call Centre mode when reset branch, if counter still login then.

<h3 style="color:orange;">Version 8.1.1 for PCCW 2023</h3>

- New Ticket Format, Ticket Type should be 2 letters and should be uppercase
- User group 'frontline' 'support' 'admin' 'manager' for PCCW 2023

<h3 style="color:orange;">Version 8.1.0</h3>

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

<h3 style="color:orange;">Version 8.0.3</h3>

- fixed Print replaced by Django Log for debug on server

<h3 style="color:orange;">Version 8.0.2</h3>

- Support SMS Module
- Softkey web version

<h3 style="color:orange;">Version 8.0.1</h3>

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

<h3 style="color:orange;">Version 8.0.0</h3>

- First Django version for Queuing Server

# Run development server:
1. Docker Desktop install and run 'redis:latest' Or Run redis server (vmware / 192.168.1.4)
2. Start virtual env
3. Run celery
4. Run django server
```bash
# Start virtual env (Windows)
.\env\Scripts\activate
# Start virtual env (Linux or Mac)
source ./env/bin/activate
# run celery
celery -A aqs.celery:app worker --loglevel=info --pool=solo
# open new terminal
python manage.py runserver 0.0.0.0:8000
```

# Development env setup
<h3 style="color:orange;">Setup python :</h3>

install python for all users

find the python path
> python -c 'import os, sys;print(os.path.dirname(sys.executable))'

Windows add PATH for exe

Right click on My Computer ->Properties ->Advanced System setting ->Environment Variable ->New

<h3 style="color:orange;">New Django project with Virtual Env setup:</h3>

```sh
pip install virtualenv
# New virtual Env:
cd \Projects\
python -m virtualenv env
# or
virtualenv env
# activate virtual env:
.\env\scripts\activate
# or
source ./env/bin/activate
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

<h3 style="color:orange;">Setup Redis server for development</h3>

#### Docker or VM
#### Docker
- Install Docker Desktop
- Add Redis Image (redis:latest)
- Run it and set the port 6379


#### MV
>Windows install VMware

>Download Debian ISO and install on VMware

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

Install PostgreSQL version 14 image
```sh
sudo docker run -p 5432:5432 -e POSTGRES_PASSWORD=asdf -d postgres:14
# or latest version
sudo docker run -p 5432:5432 -e POSTGRES_PASSWORD=asdf -d postgres
```

# Production Linux server setup 
### For example : chb.tsvd.com.hk

<h3 style="color:orange;">AWS vm</h3>

AWS EC2 : AQS8_Server_RVD, key=aws_rvd_server_key, Security Group = aqs_security

AWS Route53 : add sub domain chb.tsvd.com.hk

### AWS cost:
RVD + Test + CF = $2.02 

QS1 $???
- Launch on 2024-03-12
- t4g.small
- vCPUs-2
- HD-30G
- RAM 2G
- us-east-1b

RVD $1.46    
- Launch on 2024-03-12
- t2.medium 
- vCPUs-2 
- HD-50G 
- RAM 4G
- us-east-1b

Test $0.28 (cloesd)
- t2.micro
- vCPUs-1
- HD-30G 
- us-east-1e

CF $0.28
- Launch on 2023-5-2
- t2.micro
- vCPUs-1
- HD-24G 
- RAM 1G
- us-east-1e

<h3 style="color:orange;">Local server (Debian Linux server)</h3>

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
edit (Optional db server): 
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
2. Install bashtop or htop
```sh
sudo apt-get install -y bashtop btop
```
```sh
sudo apt-get install -y htop
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

### Auto power off script (for Debian Desktop / Raspberry Pi Window OS):
```bash
sudo nano /home/admin/.config/autostart/autooff.desktop
```
```ini
  [Desktop Entry]
  Type=Application
  Name=Auto Power Off at 23:55
  Exec=sh -c "shutdown -h 23:55"
```
- Restart Pi:

```bash
sudo reboot
```

### Auto power off script (for Linux server)
```bash
sudo nano  /etc/systemd/system/autorun.service
```
- add line:
```ini
[Unit]
Description=Autorun
After=network.target

[Service]
ExecStart=/bin/bash /home/admin/autorun.sh

[Install]
WantedBy=default.target
```
- Save and exit

```bash
sudo systemctl enable autorun.service
sudo systemctl start autorun.service
```

```bash
nano /home/admin/autorun.sh
```

```bash
# Auto shutdown at 00:30
shutdown -h 00:30
# Auto reboot at 02:30
shutdown -r 02:30
# Change the COM Port permission for Control Box
sudo chmod 666 /dev/ttyS0
# auto run Control box program
cd /home/admin/cb
./cb
```

```bash
sudo chmod +x /home/admin/autorun.sh
```
- Save and exit

## Make Linux Use Local Time (On linux system BIOS time is UTC time)
- Please note that: Auto power on (In BIOS setting) will not work.

- Please note that the hardware clock is always stored as UTC time, and Linux converts it to local time when displaying it to the user. So 2 times seem to be different, but they are actually the same time.
```bash
sudo timedatectl set-local-rtc 1 --adjust-system-clock
```

<h3 style="color:orange;">Locate PuTTY setup (for AWS):</h3>

Download the key (aws_rvd_server_key) from AWS

Open PuTTYgen -> Type of key to generate -> choose **RSA** or **SSH-2 RSA** -> Load the downloaded key -> Save private key

Open PuTTY -> Host Name (rvd.tsvd.com.hk or IP) -> Saved Sessions (RVD) -> Category -> Connection -> SSH -> Auth -> Browse (your gen private key)

PuTTY -> Data -> Auto-login username (admin) -> Session -> Save

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
>(no need, use AWS firewall so Debian firewall can be disabled)




# SETUP SOURCE CODE
<h3 style="color:orange;">Copy / git source code to home dir</h3>

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
mv ~/aqs8server ~/chb
sudo apt-get install -y virtualenv
cd ~/chb
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


# SETUP DB (PostgreSQL)
```bash
sudo systemctl reload postgresql.service
sudo su -l postgres
psql
```
PostgreSQL command:
```sql
CREATE DATABASE aqsdb8_chb;
CREATE USER aqsdbuser_chb WITH PASSWORD 'dbpassword-chUsplw0hltricispamu';
ALTER ROLE aqsdbuser_chb SET client_encoding TO 'utf8';
ALTER ROLE aqsdbuser_chb SET default_transaction_isolation TO 'read committed';
SHOW TIMEZONE;
SET TIMEZONE='UTC';
SHOW TIMEZONE;
ALTER ROLE aqsdbuser_chb SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE aqsdb8_chb TO aqsdbuser_chb;
-- For Postgresql version 16
ALTER DATABASE aqsdb8_chb OWNER TO aqsdbuser_chb;
\q
exit
```
If DB server is independence, Allow remote access to PostgreSQL server
```bash
nano /etc/postgresql/15/main/postgresql.conf
# Edit: search (CTRL + W) listen_addresses
listen_addresses = '*'
```
```bash
sudo find / -name pg_hba.conf
sudo nano /path/to/pg_hba.conf
# this case:
sudo nano /etc/postgresql/14/main/pg_hba.conf
# add line:
host    aqsdb8_chb    aqsdbuser_chb    10.95.157.237/32    md5
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
        'NAME': 'aqsdb8_chb',
        'USER': 'aqsdbuser_chb',
        'PASSWORD': 'dbpassword-chUsplw0hltricispamu',
    'HOST': '127.0.0.1',
    # or Independence DB server
        'HOST': '192.168.1.173',
        'PORT': '5432',
    }
}
```

```bash
source ./env/bin/activate
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
```
qs02 superuser : supertim /// ylthECLde5iflsplThAy

Test the Postgres DB:
```bash
python manage.py runserver 0.0.0.0:8000
```

# SECRET KEY

<h3 style="color:orange;">Django secret key</h3>

Save the SECRET_KEY from settings.py to text file (e.g. : django-DRu!8A4o2OpePep9dR5c&p&Ayaw-bupHOPR05oDru!u39clChLWRu2UspadR?**E):

```bash
sudo touch /etc/secret_key_chb.txt
sudo nano /etc/secret_key_chb.txt
```

Remove SECRET_KEY in settings.py and change to load file
```
with open('/etc/secret_key_chb.txt') as f:
    SECRET_KEY = f.read().strip()
```
<h3 style="color:orange;">ReCaptcha secret key</h3>

Save the RECAPTCHA_PRIVATE_KEY to text file (6LflOq0iAAAAAFAKsEWvj1ZY_JFKihRaxUR_vlqG):
```bash
sudo touch /etc/recaptcha_key_chb.txt
sudo nano /etc/recaptcha_key_chb.txt
```
Remove RECAPTCHA_PRIVATE_KEY in settings.py and change to load file
```
with open('/etc/recaptcha_key_chb.txt') as f:
    RECAPTCHA_PRIVATE_KEY = f.read().strip()
```
close and save

> Disable Recaptcha for debug / test
```bash
nano ~/chb/aqs/settings.py    
 ```   
>RECAPTCHA_ENABLED = False

# INIT AND SETUP the AQS8

<h3 style="color:orange;">Please note that, new version is skip this:</h3>

~~If use sql lite should disable 'SCH' function:~~

~~remark base/sch/urls.py ->~~
```bash
# init_branch_reset()
```
<h3 style="color:orange;">Change the Member.email at crm/models.py</h3>

```py
email = models.EmailField(null=False, blank=False, unique=True) # unique=True for production
```

<h3 style="color:orange;">Change the token_api at base/api/views.py</h3>

```bash
sudo nano base/api/views.py 
token_api = 'WrE-1t7IdrU2iB3a0e'
```


<h3 style="color:orange;">SETUP nginx + gunicorn</h3>

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
nano ./aqs/settings.py
```
Edit:
```python
STATIC_URL = '/static/'
STATICFILES_DIRS =[
    BASE_DIR / 'static_deploy'
]
STATIC_ROOT = BASE_DIR / 'static_deploy'
```
exit and save


```bash
python3 manage.py collectstatic
mkdir /home/admin/chb/static_deploy/download
# for upload new files to static_deploy/
# python3 manage.py collectstatic --clear
```
If can not show files in static/

Nginx operates within the directory, so if you can't cd to that directory from the nginx user 

then it will fail (as does the stat command in your log). Make sure the www-data can 

cd all the way to the /username/test/static. You can confirm that the stat will fail or succeed by running

>sudo -u www-data stat /home/admin/chb/static_deploy will fail
```bash
# try this:
sudo gpasswd -a www-data admin
sudo chmod g+x /home/admin/chb/ && chmod g+x /home/admin/chb/static_deploy
sudo nginx -s reload
```

Try Gunicorn. The only difference is we are not doing startserver command from Django, instead Gunicorn will take care of that.
```bash
gunicorn --bind 0.0.0.0:8000 aqs.wsgi
```

```bash
deactivate
sudo touch /etc/systemd/system/gunicorn_chb.socket
sudo nano /etc/systemd/system/gunicorn_chb.socket
```

edit :
```bash
[Unit]
Description=gunicorn_chb socket

[Socket]
ListenStream=/run/gunicorn_chb.sock
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
sudo nano /etc/systemd/system/gunicorn_chb.service
```
edit:
```bash
[Unit]
Description=gunicorn_chb daemon
Requires=gunicorn_chb.socket
After=network.target

[Service]
Type=notify
# the specific user that our service will run as
User=admin
# Group=someuser
# another option for an even more restricted service is
# DynamicUser=yes
# see http://0pointer.net/blog/dynamic-users-with-systemd.html
RuntimeDirectory=gunicorn_chb
WorkingDirectory=/home/admin/chb
ExecStart=/home/admin/chb/env/bin/gunicorn \
  --workers 3 \
  --bind unix:/run/gunicorn_chb.sock \
  aqs.wsgi:application
ExecReload=/bin/kill -s HUP $MAINPID
KillMode=mixed
TimeoutStopSec=5
PrivateTmp=true

[Install]
WantedBy=multi-user.target
```
****Debian should be changed you user**
```bash
sudo systemctl start gunicorn_chb.socket
sudo systemctl enable gunicorn_chb.socket
sudo systemctl status gunicorn_chb.socket
file /run/gunicorn_chb.sock
# Output: /run/gunicorn_chb.sock: socket
sudo systemctl status gunicorn_chb
#Output :
● gunicorn_chb.service - gunicorn daemon
   Loaded: loaded (/etc/systemd/system/gunicorn_chb.service; disabled; vendor preset: enabled)
   Active: inactive (dead)
curl --unix-socket /run/gunicorn_chb.sock localhost
#You should see the HTML output (have not output)
#If the output from curl or the output of systemctl status indicates that a problem occurred, check the logs for additional details:
#and Check the /etc/systemd/system/gunicorn.service file for problems.
sudo journalctl -u gunicorn_chb
sudo systemctl daemon-reload
sudo systemctl restart gunicorn_chb
```
Uninstall Apache 
```bash
sudo systemctl stop apache2 ; sudo systemctl disable apache2 ; sudo apt remove apache2
```
<h3 style="color:orange;">NGINX</h3>

```bash
sudo touch /etc/nginx/sites-available/chb
sudo nano /etc/nginx/sites-available/chb
```
edit:
```python
server {
    server_name localhost 127.0.0.1 chb.tsvd.com.hk;

    location = /favicon.ico { access_log off; log_not_found off; }
    location /static/ {
        autoindex on;
        alias /home/admin/chb/static_deploy/;
    }

    location / {
        include proxy_params;
        proxy_pass http://unix:/run/gunicorn_chb.sock;
    }
}
```
****admin should be changed you user**
```bash
sudo ln -s /etc/nginx/sites-available/chb /etc/nginx/sites-enabled
# Test the Nginx configuration for syntax errors by using the following command
sudo nginx -t
sudo systemctl restart nginx
# sudo ufw delete allow 8000
sudo ufw allow 'Nginx Full'
# sudo systemctl restart ufw
# Using AWS firewall, so no need enable Linux firewall
```




```bash
sudo gpasswd -a www-data admin
sudo chmod g+x /home/admin && chmod g+x /home/admin/chb/ && chmod g+x /home/admin/chb/static_deploy
sudo nginx -s reload
```
<h3 style="color:orange;">Init DB</h3>

```bash
source env/bin/activate
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
```
Superuser: supertim /// ylthECLde5iflsplThAy

Open web browser http://[ip address]/admin

create settings : Name=global, Branch=---, disabled API log

create user groups : api web admin support supervisor manager reporter and counter

create user : userapi /// asdf2206 (group:api)

create user : userweb /// asdf2206 (group:web, set:in-active)

create branch (bcode=KB)

create counter type (c)

create counter (CounterStatus) 1-4

create ticket type (TicketFormat)

create TicketRoute

create admin, api user for our customer
admin : elton /// asdf2206


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
\c aqsdb8_chb
INSERT INTO base_testingModel(name, des) VALUES ('David','is good guy');
```
View data from postgres
```
sudo su -l postgres
psql
\c aqsdb8_chb
\dt
TABLE base_userprofile;
TABLE base_testingModel;
INSERT INTO base_testingModel(name, des) VALUES ('David','is good guy');
\q
logout
```

<h3 style="color:orange;">Check the server stat</h3>

```
sudo su -l postgres
psql
\x
select * from pg_stat_replication;
```
<h3 style="color:orange;">check slot at main server</h3>

```
select * from pg_replication_slots;
```

remove slot from main server

```
select pg_drop_replication_slot('some_name');
\x
```
<h3 style="color:orange;">Troubleshoot:</h3>

Check error : Django code run on Gunicorn
```
sudo systemctl status gunicorn_chb
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

<h3 style="color:orange;">Change Redis server IP</h3>

> edit settings.py
```bash
nano ~/chb/aqs/settings.py
```
```python
REDIS_HOST = '127.0.0.1'
```
sudo nano /etc/nginx/sites-available/chb

```sh
server {
    listen 80;
    server_name localhost 127.0.0.1 chb.tsvd.com.hk;

    location = /favicon.ico { access_log off; log_not_found off; }
    location /static/ {
        autoindex on;
        alias /home/admin/chb/static_deploy/;
    }

    location / {
        include proxy_params;
        proxy_pass http://unix:/run/gunicorn_chb.sock;
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
****Debian should be changed you user**

****port should be changed for different application start from 8001 -> 8xxx**

Restart nginx and allow the changes to take place
```bash
sudo systemctl restart nginx
```
Test your Nginx configuration for syntax errors by typing
```bash
sudo nginx -t
```

<h3 style="color:orange;">Install Redis Server</h3>

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
nano ~/chb/aqs/asgi.py
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
source ~/chb/env/bin/activate
pip3 install daphne
deactivate
sudo nano /etc/systemd/system/daphne_chb.service
```
```nano
[Unit]
Description=Daphne_chb service
After=network.target

[Service]
Type=simple
User=admin
WorkingDirectory=/home/admin/chb
ExecStart=/home/admin/chb/env/bin/python /home/admin/chb/env/bin/daphne -b 0.0.0.0 -p 8001 aqs.asgi:application
Restart=always
StartLimitBurst=2

#StartLimitInterval=600
# Restart, but not more than once every 30s (for testing purposes)
StartLimitInterval=30

[Install]
WantedBy=multi-user.target
```
****Debian should be changed you user**

****port should be changed for different application start from 8001 -> 8xxx**

After we need to start daphne_chb.service .
```bash
sudo systemctl daemon-reload

sudo systemctl start daphne_chb.service
#If you want to check status of daphne then use.

sudo systemctl status daphne_chb.service
```
<h3 style="color:orange;">Starting the daphne Service when Server boots</h3>

```
sudo systemctl enable daphne_chb.service
```


# Run Celery worker on the server
### Using Systemd (Process Manager):
### Step 1: Create the dedicated user and group
```bash
sudo groupadd celery ;
sudo useradd -g celery celery ;
sudo mkdir /var/run/celery_chb ;
sudo chown -R celery:celery /var/run/celery_chb/ ;
sudo chmod o+w /var/run/celery_chb ;
sudo mkdir /var/log/celery_chb ;
sudo chown -R celery:celery /var/log/celery_chb/ ;
sudo chmod o+w /var/log/celery_chb
```
### Step 2: Create the Celery Worker Configuration File

Create a Celery configuration file (e.g., `celeryd`) in the `/etc/default/` directory:

```bash
sudo nano /etc/default/celeryd_chb
```

Add the following content to the `celeryd` file. Modify the values for your specific setup:

```ini
# /etc/default/celeryd_chb
#   most people will only start one node:
CELERYD_NODES="worker1"
#   but you can also start multiple and configure settings
#   for each in CELERYD_OPTS
#CELERYD_NODES="worker1 worker2 worker3"
#   alternatively, you can specify the number of nodes to start:
#CELERYD_NODES=10

# Absolute or relative path to the 'celery' command:
CELERY_BIN="/home/admin/chb/env/bin/celery"
#CELERY_BIN="/virtualenvs/def/bin/celery"

# App instance to use
# comment out this line if you don't use an app
CELERY_APP="aqs.celery:app"
# or fully qualified:
#CELERY_APP="proj.tasks:app"

# Where to chdir at start.
CELERYD_CHDIR="/home/admin/chb"

# Extra command-line arguments to the worker
CELERYD_OPTS="--time-limit=300 --concurrency=8"
# Configure node-specific settings by appending node name to arguments:
#CELERYD_OPTS="--time-limit=300 -c 8 -c:worker2 4 -c:worker3 2 -Ofair:worker1"

# Set logging level to DEBUG
#CELERYD_LOG_LEVEL="DEBUG"

# %n will be replaced with the first part of the node name.
CELERYD_LOG_FILE="/var/log/celery_chb/%n%I.log"
CELERYD_PID_FILE="/var/run/celery_chb/%n.pid"

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
sudo nano /etc/systemd/system/celery_chb.service
```

Add the following content to the `celery_chb.service` file:

```ini
# /etc/systemd/system/celery_chb.service
[Unit]
Description=Celery_chb Service
After=network.target

[Service]
Type=forking
User=admin
Group=admin

EnvironmentFile=/etc/default/celeryd_chb
WorkingDirectory=/home/admin/chb
ExecStart=/home/admin/chb/env/bin/celery multi start ${CELERYD_NODES} \
  -A ${CELERY_APP} --pidfile=${CELERYD_PID_FILE} \
  --logfile=${CELERYD_LOG_FILE} --loglevel=${CELERYD_LOG_LEVEL} ${CELERYD_OPTS}
ExecStop=/home/admin/chb/env/bin/celery multi stopwait ${CELERYD_NODES} \
  --pidfile=${CELERYD_PID_FILE}
ExecReload=/home/admin/chb/env/bin/celery multi restart ${CELERYD_NODES} \
  -A ${CELERY_APP} --pidfile=${CELERYD_PID_FILE} \
  --logfile=${CELERYD_LOG_FILE} --loglevel=${CELERYD_LOG_LEVEL} ${CELERYD_OPTS}

[Install]
WantedBy=multi-user.target

```

### Step 4: Enable and Start the Celery Service

Now that you have created the configuration and service files, enable and start the Celery service:

```bash
sudo systemctl enable celery_chb
sudo systemctl start celery_chb
```

The `enable` command ensures that the Celery service starts automatically during server startup.

### Step 5: Add autorun script for auto shutdown
```bash
sudo nano /home/admin/autorun.sh
```
Add following script:
```bash
# For Celery
# The dir will auto deleted when every time reboot.
mkdir /var/run/celery_chb
chown -R celery:celery /var/run/celery_chb/
chmod o+w /var/run/celery_chb
```
### Auto power off script (for Linux server)
```bash
sudo nano  /etc/systemd/system/autorun.service
```
- add line:
```ini
[Unit]
Description=Autorun
After=network.target

[Service]
ExecStart=/bin/bash /home/admin/autorun.sh

[Install]
WantedBy=default.target
```
- Save and exit

```bash
sudo systemctl enable autorun.service
sudo systemctl start autorun.service
```

```bash
sudo chmod +x /home/admin/autorun.sh
```
- Save and exit

### Step 6: Check the Celery Service Status

You can check the status of the Celery service to ensure it is running:

```bash
sudo systemctl status celery_chb
```

This command will display the current status and any logs related to the Celery service.

### Step 7: Monitor Celery Worker Logs

You can monitor the Celery worker logs at the location specified in the `CELERYD_LOG_FILE` configuration (e.g., `/var/log/celery/%N.log`). These logs will contain information about the Celery worker's activities and task execution.

That's it! Your Celery worker is now set up as a Systemd service and will start automatically during server startup. It will continue to run in the background, processing your asynchronous tasks as needed.



# SSL
### First domain
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
nano ~/chb/base/ws.py
# change :
wsHypertext = 'ws://'
# to :
wsHypertext = 'wss://'
````

Reboot the server
```bash
sudo reboot
```
### Second domain
```sh
sudo certbot --nginx --expand -d second.domain.com
```

# Setup google reCaptcha
<h3 style="color:orange;">Use reCaptcha</h3>

Open new reCaptcha:
Create new reCaptcha on [google.com/recaptcha](https://www.google.com/recaptcha)

create new file /etc/recaptcha_key_chb.txt

and save the private key to the file.

Edit .\aqs\settings.py

```python
RECAPTCHA_PUBLIC_KEY = 'xxx'
with open('/etc/recaptcha_key_chb.txt') as f:
    RECAPTCHA_PRIVATE_KEY = f.read().strip()
RECAPTCHA_REQUIRED_SCORE = 0.85
```
<h3 style="color:orange;">Enable / Disable reCaptcha</h3>

nano ~\chb\aqs\settings.py

> RECAPTCHA_ENABLED = False

# Setup email
<h3 style="color:orange;">Setup email sender</h3>

create new file /etc/emailpw_chb.txt

and save the email password key to the file.

Edit .\aqs\settings.py

```python
# SMTP email settings
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.mail.us-east-1.awsapps.com'
EMAIL_PORT = 465
EMAIL_USE_SSL = True
EMAIL_HOST_USER = 'tim@tsvd.com.hk'
with open('/etc/emailpw_chb.txt') as f:
    EMAIL_HOST_PASSWORD = f.read().strip()
```

# Setup SMS
<h3 style="color:orange;">Setup SMS</h3>

create new file /etc/sms_key_chb.txt

and save the api key to the file.

Edit .\aqs\settings.py

```python
# SMS settings
SMS_ACCOUNT_NAME = 'tsvd@u3.ufosend.com'
SMS_SENDER = 'TSVD'
with open('/etc/sms_key_chb.txt') as f:
    SMS_API_KEY = f.read().strip()
```

# Setup new git repo
<h3 style="color:orange;">Create new repo on [github.com](http://github.com)</h3>

Open the web browser login github.com

New the repo named e.g. aqs8server
<h3 style="color:orange;">Local source code prepare</h3>

Download and install git: https://git-scm.com/downloads
```bash
# download git and setup
git --version
git config --global --list
git config --global user.name "xxx"
git config --global user.email "xxx.email.com"
git config --global user.password "xxx"
```
<h3 style="color:orange;">Upload your first commit:</h3>

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
<h3 style="color:orange;">Commit new version to github</h3>

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

<h3 style="color:orange;">Setup Putty</h3>

Download and install font on your Windows:
https://github.com/powerline/fonts/tree/master/DejaVuSansMono

Setup Putty 'Saved Sessions'
Window -> Appearance -> Change font -> Deja...Powerline
Window -> Color -> Default Blue -> Red 44 Green 123 Blue 201

# Copy file from PC to Linux server
pscp c:/music.mp3  admin@192.168.1.222:/home/admin/
pscp -r your/folder/aqs8server/* admin@10.95.157.237:/home/admin/aqs8server/
# then change owner
sudo chown admin ~/aqs8server -R

# Network (Internet) speed test
```bash
sudo apt install speedtest-cli
speedtest
```
# Switch to new server (4 steps)
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
        'USER': 'aqsdbuser_chb',
        'PASSWORD': 'dbpassword-chUsplw0hltricispamu',
        'HOST': '10.95.157.236',
        'PORT': '5432',
    }
}
```
### `Step 4` : Change Q.Server SU password
```bash
sudo passwd admin
> wert2206EDC5345
```
### `Done` for switch to new server ------------------

# Copy source from USB drive :
```bash
# find out your usb drive my case is sdb1
lsblk
```
```bash
sudo mkdir /mnt/usb
sudo mount /dev/sdb1 /mnt/usb
cd /mnt/usb
sudo cp aqs8server /home/admin/aqs8server/ -r
# change owner
sudo chown admin ~/aqs8server -R
```
```bash
# Unmount USB drive
sudo umount /mnt/usb
```

# Install python lib offline
```bash
# Download python lib to local PC
pip download django-crequest -d ./lib/
pip download celery[redis] -d ./lib/

# new dir on server
mkdir ~/aqs8server/lib
pscp -r ./lib/* admin@10.95.157.237:/home/admin/aqs8server/lib/

# change owner
sudo chown admin ~/aqs8server -R

# Install python lib on liunx server
cd /home/admin/aqs8server
source ./env/bin/activate
pip3 install django-crequest --no-index --find-links=/home/admin/aqs8server/lib/
pip3 install celery[redis] --no-index --find-links=/home/admin/aqs8server/lib/
```
