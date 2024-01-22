# Fix Branch Shutdown Issue from v8.0.0 to v8.1.1
*Fixed bug : Schedule task not run when branchs is shutdown time same. Casue by the init_branch_reset() function is remove all schedule task first.*

### base > sch > views.py


> Line 212:

```python
    # add new job
    # branchobj = Branch.objects.all()
    # for b in branchobj:
    #     if b != branch:
    #         sch.remove_job(b.bcode)
    
    # init_branch_reset()
    sch_shutdown(branch, datetime_now)
```
	
> line 62 replace all function

```python
def init_branch_reset():
    branch_count = 0    
    datetime_now = timezone.now()

    try:
        branchobj = Branch.objects.all()
        branch_count = branchobj.count()
    except:
        print ('   -SCH- init_branch_reset Error : No Branch')        
        if system_inited == True :
            SystemLog.objects.create(
                logtime=datetime_now,
                logtext ='UTC time:' + datetime_now.strftime('%H:%M:%S') + ' -SCH- init_branch_reset Error : No Branch',
                )

    if branch_count > 0:
        for branch in branchobj:
            sch_shutdown(branch, datetime_now)
```		

> Line 195 add:

```python
def sch_shutdown(branch_input, nowUTC):
    branch = Branch.objects.get(id=branch_input.id)

    now = timezone.now()
    datetime_now = nowUTC
    localtime_now = funUTCtoLocaltime(datetime_now, branch.timezone )      
    localtime = funUTCtoLocaltime( branch.officehourend, branch.timezone )
    
    slocaltime = timezone.now().strftime('%Y-%m-%d ') + localtime.strftime('%H:%M:%S')
    localtime = datetime.strptime(slocaltime, '%Y-%m-%d %H:%M:%S')
    localtime = pytz.utc.localize(localtime)

    snextreset = timezone.now().strftime('%Y-%m-%d ') + branch.officehourend.strftime('%H:%M:%S')
    nextreset = datetime.strptime(snextreset, '%Y-%m-%d %H:%M:%S')
    nextreset = pytz.utc.localize(nextreset)
    
    logtemp1 = '   -SCH- ' + nextreset.strftime('%Y-%m-%d %H:%M:%S') + ' > ' + now.strftime('%Y-%m-%d %H:%M:%S')            
    if nextreset > now :
        logtemp1 = logtemp1 + ' [Yes]'
        pass                    
    else:
        nextreset  = nextreset + timedelta(hours=24)
        logtemp1 = logtemp1 + ' [No]'

    logtemp2 =  '   -SCH- reset time: ' + branch.officehourend.strftime('%H:%M:%S') + ' Local Time: '+ localtime.strftime('%H:%M:%S') 
    
    nextreset_local = funUTCtoLocal(nextreset, branch.timezone )
    logtemp3 = ' -SCH- Next reset [' + branch.bcode + ']: ' + nextreset.strftime('%Y-%m-%d %H:%M:%S') + ' Local:' + nextreset_local.strftime('%Y-%m-%d %H:%M:%S') 
    
    print (logtemp3)
    print (logtemp2)
    print (logtemp1)

    if system_inited == True :
        SystemLog.objects.create(
            logtime = datetime_now,
            logtext = 'Local time:' + localtime_now.strftime('%H:%M:%S') + logtemp3 + '\n' + logtemp2 + '\n' + logtemp1
            )
    # before add job must check the job is exist or not
    if sch.get_job(branch.bcode) != None :
        # if exist remove it
        sch.remove_job(branch.bcode)        
    sch.add_job(job_shutdown, 'date', run_date=nextreset, id=branch.bcode, args=[branch])
```	
	
### templates > navbar.html
> Line 7:
```html
<h1>Queuing System v8.0.0.1 - TSVD</h1>
```