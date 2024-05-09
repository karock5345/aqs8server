# Temporary bug fixed WS will be mix up when the server is serving multiple apps
  - base/consumers.py > CounterStatusConsumer > line 386 - 396
    ``` py
    self.bcode = await get_bcode()
    if self.bcode == None:
        error = 'CounterStatusConsumer: Branch not found.'

    self.room_group_name = 'cs_' + self.bcode + '_' + self.pk
    self.ws_str = 'cs'
    logger.info('connecting:' + self.room_group_name )
    ```
  - base > routing.py > line 16
    ```py
    re_path(r'ws/cs/(?P<bcode>\w+)/(?P<pk>\w+)/$', consumers.CounterStatusConsumer.as_asgi()),
    ```
  - static > js > softkey.js > line 196 - 204
  - static > js > softkey_cc.js > 247 -253
    ```js
    const CounterStatusSocket = new WebSocket(
        c_wsh
        + window.location.host
        + '/ws/cs/'
        + c_bcode
        + '/'
        + c_pk
        + '/'
    );
    ```
  - base > ws.py > wsconuterstatus > line 230
    ```py
      bcode = counterstatus.countertype.branch.bcode

      channel_layer = get_channel_layer()
      channel_group_name = 'cs_' + bcode + '_' + str(counterstatus.id)