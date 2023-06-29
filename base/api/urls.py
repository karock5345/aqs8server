from django.urls import path

from base.api import v_display
from . import views
from . import v_touch
from . import v_printer
from . import v_softkey
from . import v_roche

urlpatterns = [
    path('', views.getRoutes),
    path('branchs/', views.getBranchs),
    path('ticketkey/', v_touch.postTicket),  # http://127.0.0.1:8000/api/ticketkey/?username=userapi&password=asdf2206&token=jgd764Pf607qjK2NJFqbh96seg&branchcode=KB&tickettype=A&printernumber=<pno>1</pno>&remark=test&app=web&version=8
    path('touchkeys/', v_touch.postTouchKeys),
    path('firstprint/', v_printer.getFirstPrint),  # http://127.0.0.1:8000/api/firstprint/?username=userapi&password=asdf2206&token=jgd764Pf607qjK2NJFqbh96seg&branchcode=KB&app=web&version=8
    path('printed/', v_printer.postTicketPrinted),  # http://127.0.0.1:8000/api/printed/?username=userapi&password=asdf2206&token=jgd764Pf607qjK2NJFqbh96seg&app=web&version=8&branchcode=KB&tickettype=A&ticketnumber=074
    path('updateprinter/', v_printer.postUpdatePrinter),
    path('printerstatus/', v_printer.getPrinterStatus),  
    path('counterlogin/', v_softkey.postCounterLogin), 
    path('counterlogout/', v_softkey.postCounterLogout), 
    path('waiting/', v_softkey.getCounterWaitingList), 
    path('call/', v_softkey.postCounterCall), 
    path('recall/', v_softkey.postCounterRecall), 
    path('miss/', v_softkey.postCounterMiss), 
    path('void/', v_softkey.postCounterVoid), 
    path('process/', v_softkey.postCounterProcess), 
    path('done/', v_softkey.postCounterDone), 
    path('get/', v_softkey.postCounterGet), 

    path('display/', v_display.getDisplay), 
    path('displaywait/', v_display.getWaiting), 
    path('displaylast/', v_display.getLastDisplay), 

    path('voice/', v_display.getVoice), 


    # path('applogin/', v_roche.postRocheLogin),
    # path('applist/', v_roche.getRocheFirstPrint),
    # path('applisttest/', v_roche.getRocheFirstPrintTest),
]








