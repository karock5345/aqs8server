from django.urls import re_path
from . import consumers

websocket_urlpatterns = [    
    re_path(r'ws/webtv/(?P<bcode>\w+)/(?P<ct>\w+)/$', consumers.WebTVConsumer.as_asgi()),
    re_path(r'ws/ql/(?P<bcode>\w+)/(?P<ct>\w+)/$', consumers.QLConsumer.as_asgi()),
    re_path(r'ws/pstatus/(?P<bcode>\w+)/$', consumers.PrinterStatusConsumer.as_asgi()),

]