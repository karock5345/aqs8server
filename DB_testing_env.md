## Setup testing DB in Postresql 14

- DB IP 192.168.85.128 (VM)

```bash
sudo apt-get install -y libpq-dev postgresql 
sudo apt-get install -y unixodbc unixodbc-dev

sudo systemctl reload postgresql.service
sudo su -l postgres
psql
```
PostgreSQL command:
```sql
CREATE DATABASE aqsdb8_test1;
CREATE USER aqsdbuser WITH PASSWORD 'dbpassword-Dlcg1dwMOXSKIAIM';
ALTER ROLE aqsdbuser SET client_encoding TO 'utf8';
ALTER ROLE aqsdbuser SET default_transaction_isolation TO 'read committed';
SHOW TIMEZONE;
SET TIMEZONE='UTC';
SHOW TIMEZONE;
ALTER ROLE aqsdbuser SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE aqsdb8_test1 TO aqsdbuser;
\q
exit
```

- Allow Django Server access DB server
```
# PostgreSQL
sudo -u postgres psql -c 'SHOW config_file'
sudo nano /etc/postgresql/14/main/postgresql.conf
# edit:
listen_addresses = '*'

sudo find / -name pg_hba.conf
sudo nano /etc/postgresql/14/main/pg_hba.conf
# edit:
host    all     aqsdbuser    192.168.1.22/32    md5
host    all     aqsdbuser    192.168.85.1/32    md5
# Laptop IP address
host    all     aqsdbuser    192.168.1.155/32    md5
```
> Please note that IP 192.168.85.1 for VM

```bash
exit
sudo systemctl reload postgresql.service
```

## Setup Django 
- Change Django settings.py 

```bash
sudo nano ~/aqs8server/aqs/settings.py
```
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'aqsdb8_test1',
        'USER': 'aqsdbuser',
        'PASSWORD': 'dbpassword-Dlcg1dwMOXSKIAIM',
        'HOST': '192.168.85.128',
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
- Django SU
tim /// asdf

## Init the DB

Login at 127.0.0.1:8000/admin

create settings : Name=global, Branch=---, disabled API log

create user groups : api web admin support manager frontline 

create branch (bcode=WTT, SCP, HHT)

create admin user : elton /// asdf2206

create user : userapi /// asdf2206 (group:api)

create user : userweb /// asdf2206 (group:web, set:in-active)

create user profile for superuser, userapi, userweb , admin user (elton)

create counter type (c)

create counter (CounterStatus) 1-4

create ticket type (TicketFormat)

create TicketRoute

create admin, api user for our customer
admin : elton /// asdf2206

