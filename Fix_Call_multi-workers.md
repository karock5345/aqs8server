# Upgrade Call/Get function support Multiple Workers (Not including "New Ticket" function) for version v8.2.x
- Backup base\views.py to views.py.bu
- New copy base\views.py to views.py.v830
- Backup base\api\v_softkey.py to v_softkey.py.bu
- New copy base\api\v_softkey.py to v_softkey.py.v830
- Backup base\api\v_softkey_sub.py to v_softkey_sub.py.bu
- New copy base\api\v_softkey_sub.py to v_softkey_sub.py.v830
- New base\a_global.py
```py
str_db_locked = 'DB_locked'
```

- Edit base\views.py.v830 :
	- line 190/198 edit:
	```py
        # old version no database lock may be cause double call
        # status, msg, context_get = funCounterGet('', tt.tickettype, tt.ticketnumber, request.user, counterstatus.countertype.branch, counterstatus.countertype, counterstatus, 'Get ticket from list', 'Softkey-web', softkey_version, datetime_now)
        # new version with database lock
        for i in range(0, 10):
            status, msg, context_get = funCounterGet_v830('', tt.tickettype, tt.ticketnumber, request.user, counterstatus.countertype.branch, counterstatus.countertype, counterstatus, 'Get ticket from list', 'Softkey-web', softkey_version, datetime_now)
            if status['status'] == 'OK':
                break
            else:
                error = msg['msg']
                from base.a_global import str_db_locked
                if error == str_db_locked:
                    logger.warning('Database is locked. Retry ' + str(i + 1) + ' times.')
                    time.sleep(0.05)
                else:
                    break        
        if status['status'] == 'Error':
            error = msg['msg'] + ' ' + tt.tickettype + tt.ticketnumber
	```
	- line 348/360 edit:
	```py
                    # old version no database lock may be cause double call
                    # status, msg, context_get = funCounterGet(getticket, '', '', request.user, counterstatus.countertype.branch, counterstatus.countertype, counterstatus, 'Get ticket ', 'Softkey-web', softkey_version, datetime_now)
                    # new version with database lock
                    for i in range(0, 10):
                        status, msg, context_get = funCounterGet_v830(getticket, '', '', request.user, counterstatus.countertype.branch, counterstatus.countertype, counterstatus, 'Get ticket ', 'Softkey-web', softkey_version, datetime_now)
                        if status['status'] == 'OK':
                            break
                        else:
                            error = msg['msg']
                            from base.a_global import str_db_locked
                            if error == str_db_locked:
                                logger.warning('Database is locked. Retry ' + str(i + 1) + ' times.')
                                time.sleep(0.05)
                            else:
                                break
	```
	- line 372/386 edit:
	```py
                # old version no database lock may be cause double call
                # status, msg, context_call = funCounterCall(request.user, counterstatus.countertype.branch, counterstatus.countertype, counterstatus, 'Call ticket ', 'Softkey-web', softkey_version, datetime_now)                
                # new version with database lock
                for i in range(0, 10):
                    status, msg, context_call = funCounterCall_v830(request.user, counterstatus.countertype.branch, counterstatus.countertype, counterstatus, 'Call ticket ', 'Softkey-web', softkey_version, datetime_now)
                    if status['status'] == 'OK':
                        break
                    else:
                        error = msg['msg']
                        from base.a_global import str_db_locked
                        if error == str_db_locked:
                            logger.warning('Database is locked. Retry ' + str(i + 1) + ' times.')
                            time.sleep(0.05)
                        else:
                            break
	```
	- line 667/683 edit:
	```py
        # old version no database lock may be cause double call
        # status, msg, context = funCounterCall(request.user, counterstatus.countertype.branch, counterstatus.countertype, counterstatus, 'Call ticket:', 'Softkey-web', softkey_version, datetime_now)        
        # new version with database lock
        for i in range(0, 10):
            status, msg, context = funCounterCall_v830(request.user, counterstatus.countertype.branch, counterstatus.countertype, counterstatus, 'Call ticket:', 'Softkey-web', softkey_version, datetime_now)
            if status['status'] == 'OK':
                break
            else:
                error = msg['msg']
                from base.a_global import str_db_locked
                if error == str_db_locked:
                    logger.warning('Database is locked. Retry ' + str(i + 1) + ' times.')
                    time.sleep(0.05)
                else:
                    break
	```
- Edit base\api\v_softkey_sub.py.v830 :
    - line 1  add :
    ```py
    from django.db import transaction
    import time
    ```    
	- Add "funCounterCall_v830" function at line 16 before "funCounterCall" function
	- Add "funCounterGet_v830" function at line 779 before "funCounterCall" function
	- line 1441 edit:
	```py
    # old version no database lock may be cause double call
    ############### modify funCounterCall function from only accept 'waiting' to accept 'waiting' and 'ready'
    # status, msg, context_call = funCounterCall(user, branch, countertype, counterstatus, logtext, rx_app, rx_version, datetime_now)
    # new version with database lock
    for i in range(0, 10):
        status, msg, context_call = funCounterCall_v830(user, branch, countertype, counterstatus, logtext, rx_app, rx_version, datetime_now)
        if status['status'] == 'OK':
            break
        else:
            error = msg['msg']
            from base.a_global import str_db_locked
            if error == str_db_locked:
                logger.warning('Database is locked. Retry ' + str(i + 1) + ' times.')
                time.sleep(0.05)
            else:
                break
	```
- Edit base\api\v_softkey.py.v830 :	
	- line 149 edit:
	```py
        # old version no database lock may be cause double call
        # status, msg, context = funCounterGet('', rx_ticketype, rx_ticketnumber, user, branch, countertype, counterstatus, 'Ticket Get API : ', rx_app, rx_version, datetime_now)
        # new version with database lock
        for i in range(0, 10):
            status, msg, context = funCounterGet_v830('', rx_ticketype, rx_ticketnumber, user, branch, countertype, counterstatus, 'Ticket Get API : ', rx_app, rx_version, datetime_now)
            if status['status'] == 'OK':
                break
            else:
                error = msg['msg']
                from base.a_global import str_db_locked
                if error == str_db_locked:
                    logger.warning('Database is locked. Retry ' + str(i + 1) + ' times.')
                    time.sleep(0.05)
                else:
                    break
	```
	- line 1222 edit:
	```py
        # function call ticket
        # old version no database lock may be cause double call
        # status, msg, context = funCounterCall(user, branch, countertype, counterstatus, 'Calling ticket API : ', rx_app, rx_version, datetime_now)
        # new version with database lock
        for i in range(0, 10):
            status, msg, context = funCounterCall_v830(user, branch, countertype, counterstatus, 'Calling ticket API : ', rx_app, rx_version, datetime_now)
            if status['status'] == 'OK':
                break
            else:
                error = msg['msg']
                from base.a_global import str_db_locked
                if error == str_db_locked:
                    logger.warning('Database is locked. Retry ' + str(i + 1) + ' times.')
                    time.sleep(0.05)
                else:
                    break
	```
	
- Upgrade system :
```sh
cd <project folder>
cd base\
cp views.py.v830 views.py
cd api
cp v_softkey_sub.py.v830 v_softkey_sub.py
cp v_softkey.py.v830 v_softkey.py

sudo systemctl restart gunicorn_tg2024.socket ;
sudo systemctl restart gunicorn_tg2024  ;
sudo systemctl restart celery_tg2024  ;
sudo systemctl restart daphne_tg2024

sudo systemctl status gunicorn_tg2024
```