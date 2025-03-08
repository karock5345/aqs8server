# Version 8.3.0 all WS links added APP_NAME to avoid conflict with other apps 
#  e.g. /ws/webtv/[bcode]/[ct] -> /ws/APP_NAME/webtv/[bcode]/[ct]
from django.urls import re_path
from . import consumers
from aqs.settings import APP_NAME

websocket_urlpatterns = [
    # /ws/APP_NAME/webtv/[bcode]/[ct] for internal
    re_path(r'ws/{}/webtv/(?P<bcode>\w+)/(?P<ct>\w+)/$'.format(APP_NAME), consumers.WebTVConsumer.as_asgi()),    
    # /ws/APP_NAME/wtv/[bcode]/[ct] for public    
    re_path(r'ws/{}/wtv/(?P<bcode>\w+)/(?P<ct>\w+)/$'.format(APP_NAME), consumers.WebTVConsumer.as_asgi()),
    re_path(r'ws/{}/ql/(?P<bcode>\w+)/(?P<ct>\w+)/$'.format(APP_NAME), consumers.QLConsumer.as_asgi()),
    re_path(r'ws/{}/pstatus/(?P<bcode>\w+)/$'.format(APP_NAME), consumers.PrinterStatusConsumer.as_asgi()),
    re_path(r'ws/{}/print_v840/(?P<bcode>\w+)/$'.format(APP_NAME), consumers.PrintConsumer_v840.as_asgi()),
    re_path(r'ws/{}/tstatus/(?P<bcode>\w+)/(?P<ttype>\w+)/(?P<tno>\w+)/(?P<sc>\w+)/$'.format(APP_NAME), consumers.TicketStatusConsumer.as_asgi()),
    # re_path(r'ws/{}/voice/(?P<bcode>\w+)/(?P<ct>\w+)/$'.format(APP_NAME), consumers.VoiceConsumer.as_asgi()),
    # re_path(r'ws/{}/voice830/(?P<bcode>\w+)/(?P<ct>\w+)/$'.format(APP_NAME), consumers.Voice830Consumer.as_asgi()),
    re_path(r'ws/{}/voice_v840/(?P<bcode>\w+)/(?P<ct>\w+)/$'.format(APP_NAME), consumers.VoiceConsumer_v840.as_asgi()),
    re_path(r'ws/{}/sms/(?P<bcode>\w+)/$'.format(APP_NAME), consumers.SMSConsumer.as_asgi()),
    re_path(r'ws/{}/cs/(?P<bcode>\w+)/(?P<pk>\w+)/$'.format(APP_NAME), consumers.CounterStatusConsumer.as_asgi()),
    re_path(r'ws/{}/flashlight/(?P<bcode>\w+)/$'.format(APP_NAME), consumers.FlashLightConsumer.as_asgi()),
    re_path(r'ws/{}/disp_v840/(?P<bcode>\w+)/(?P<ct>\w+)/$'.format(APP_NAME), consumers.DispPanelConsumer_v840.as_asgi()),
    re_path(r'ws/{}/dispmute/(?P<bcode>\w+)/(?P<ct>\w+)/$'.format(APP_NAME), consumers.DispPanelMuteConsumer.as_asgi()),
    re_path(r'ws/{}/progress/(?P<task_id>\w+)/$'.format(APP_NAME), consumers.ReportRaw_ProgressConsumer.as_asgi()),
    # re_path(r'ws/{}/progress_process/(?P<task_id>\w+)/$'.format(APP_NAME), consumers.Report_ProgressProcessConsumer.as_asgi()),    
]
