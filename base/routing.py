from django.urls import re_path
from . import consumers

websocket_urlpatterns = [    
    re_path(r'ws/webtv/(?P<bcode>\w+)/(?P<ct>\w+)/$', consumers.WebTVConsumer.as_asgi()),
    re_path(r'ws/ql/(?P<bcode>\w+)/(?P<ct>\w+)/$', consumers.QLConsumer.as_asgi()),
    re_path(r'ws/pstatus/(?P<bcode>\w+)/$', consumers.PrinterStatusConsumer.as_asgi()),
    re_path(r'ws/print/(?P<bcode>\w+)/$', consumers.PrintConsumer.as_asgi()),
    re_path(r'ws/tstatus/(?P<bcode>\w+)/(?P<ttype>\w+)/(?P<tno>\w+)/(?P<sc>\w+)/$', consumers.TicketStatusConsumer.as_asgi()),
    re_path(r'ws/voice/(?P<bcode>\w+)/(?P<ct>\w+)/$', consumers.VoiceConsumer.as_asgi()),
    re_path(r'ws/sms/(?P<bcode>\w+)/$', consumers.SMSConsumer.as_asgi()),
]