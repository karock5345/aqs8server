from django.urls import re_path 
from . import consumers

websocket_urlpatterns = [    
    re_path(r'ws/webtv/(?P<bcode>\w+)/(?P<ct>\w+)/$', consumers.ChatConsumer.as_asgi()),
]