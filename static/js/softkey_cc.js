        const c_app_name = JSON.parse(document.getElementById('js-app_name').textContent);
        const c_waitinglist_show = JSON.parse(document.getElementById('js-waitinglist_show').textContent);
        const c_wsh = JSON.parse(document.getElementById('js-wsh').textContent);
        const c_pk = JSON.parse(document.getElementById('js-pk').textContent);
        const c_bcode = JSON.parse(document.getElementById('js-bcode').textContent);
        const c_ct = JSON.parse(document.getElementById('js-countertype').textContent);
        const c_counterstatus = JSON.parse(document.getElementById('js-counterstatus').textContent);
        const c_ttype = JSON.parse(document.getElementById('js-tickettype').textContent);
        const c_tno = JSON.parse(document.getElementById('js-ticketnumber').textContent);
        var btn_ready = document.getElementById('id_btn_ready');
        var btn_busy = document.getElementById('id_btn_busy');
        var btn_cancel = document.getElementById('id_btn_cancel');
        var btn_acw = document.getElementById('id_btn_acw');
        var btn_aux = document.getElementById('id_btn_aux');
        var btn_logout = document.getElementById('id_btn_logout');
        var btn_on = document.getElementById('id_btn_on');
        var btn_off = document.getElementById('id_btn_off');
        var btn_flash = document.getElementById('id_btn_flash');

        // var btn_get = document.getElementById('get_btn');
        // var get_back = document.getElementById('get_back');
        // var get_area_html = document.getElementById('get_area').innerHTML;
        var hidden = true;
        var listshow = null;
        var btn_listshow = document.getElementById('qlistshow_btn');
        var btn_listhide = document.getElementById('qlisthide_btn');
        var btn_max = document.getElementById('btn_max');
        var maxwin = null;
        var html_m_menu = document.getElementById('id_mobile-menu').innerHTML;
        var html_menu = document.getElementById('id_menu').innerHTML;
        // 
        maxwin = localStorage.getItem("key_maxwin");
        if (maxwin == null) {
          maxwin = "normal";
        }
        maxwinfunc();

        function maxwinfunc(){
          
          if (maxwin == "max") {
            btn_max.innerHTML = "Back";
            document.getElementById('id_menu').setAttribute("hidden", "hidden")
            document.getElementById('id_mobile-menu').innerHTML = "";
            document.getElementById('id_navbar').style.display = "none";
            document.getElementById('id_main').classList.remove("layout--2");
            document.getElementById('id_main').classList.add("layout--1");
          } else {
            btn_max.innerHTML = "Max";
            document.getElementById('id_menu').removeAttribute("hidden")
            document.getElementById('id_mobile-menu').innerHTML = html_m_menu;
            document.getElementById('id_navbar').style.display = "block";
            document.getElementById('id_main').classList.remove("layout--1");
            document.getElementById('id_main').classList.add("layout--2");
          }
          localStorage.setItem("key_maxwin", maxwin);
        }

        btn_max.addEventListener('click', function() {
          maxwin = localStorage.getItem("key_maxwin");
          if (maxwin == "normal") {
            maxwin = "max";
          } else {
            maxwin = "normal";
          }
          maxwinfunc();
        });



        // var can hold data when refresh page
        listshow = localStorage.getItem("key_listshow");
        if (listshow == null) {
          listshow = "show";
        }
        showorhideqlist();

        btn_listhide.addEventListener('click', function() {
          listshow = "hide";
          showorhideqlist();
        });
        btn_listshow.addEventListener('click', function() {
          listshow = "show";
          showorhideqlist();
        });
  
        function showorhideqlist(){
          if (listshow == "hide") {
            document.getElementById('qlist_area').style.display = "none";
            document.getElementById('qlhide_header').style.display = "none";
            document.getElementById('qlshow_header').style.display = "block";
            // document.getElementById('qlshow_header').hidden = false; why not work?

          } else {
            document.getElementById('qlist_area').style.display = "block";
            document.getElementById('qlhide_header').style.display = "block";
            document.getElementById('qlshow_header').style.display = "none";
          }
          localStorage.setItem("key_listshow", listshow);
        }


        // new funcition to change the status (input status, ticket type, ticket number)
        function changeStatus(status, ttype, tno, loged) {
          if (loged == false) {
            // redirect to home page
            window.location.href = "{% url 'home' %}";
          }

          if (status == 'AUX') {
            btn_ready.disabled = false;
            btn_busy.disabled = true;
            btn_cancel.disabled = true;

            btn_acw.disabled = false;
            btn_aux.disabled = true;
            btn_logout.disabled = false;

            document.getElementById('status_text').innerHTML = 'Status : AUX';
          } else if (status == 'ready') {
            btn_ready.disabled = true;
            btn_busy.disabled = true;
            btn_cancel.disabled = true;

            btn_acw.disabled = false;
            btn_aux.disabled = false;
            btn_logout.disabled = false;

            document.getElementById('status_text').innerHTML = 'Status : Ready';

          } else if (status == 'calling') {
            document.getElementById('status_text').innerHTML = 'Status : Calling ' + ttype + tno;


            btn_ready.disabled = true;
            btn_busy.disabled = false;
            btn_cancel.disabled = false;

            btn_acw.disabled = true;
            btn_aux.disabled = true;
            btn_logout.disabled = true;
          } else if (status == 'processing') {
            document.getElementById('status_text').innerHTML = 'Status : Processing ' + ttype + tno;
            btn_ready.disabled = false;
            btn_busy.disabled = true;
            btn_cancel.disabled = true;

            btn_acw.disabled = false;
            btn_aux.disabled = false;
            btn_logout.disabled = true;

          } else if (status == 'ACW') {
            document.getElementById('status_text').innerHTML = 'Status : ACW ' + ttype + tno;
            btn_ready.disabled = false;
            btn_busy.disabled = true;
            btn_cancel.disabled = true;

            btn_acw.disabled = true;
            btn_aux.disabled = false;
            btn_logout.disabled = false;
          } else {
            document.getElementById('status_text').innerHTML = 'Status : ' + status;
          }
        }

        //  call function changeStatus
        changeStatus(c_counterstatus, c_ttype, c_tno, true);

        // //  javascript Button "Get" show or hidden html id="get_area" 
        // document.getElementById('get_area').innerHTML = '';

        // btn_get.addEventListener('click', function() {
        //   if (hidden) {
        //     document.getElementById('get_area').innerHTML = get_area_html;
        //     hidden = false;
        //   } else {
        //     document.getElementById('get_area').innerHTML = '';
        //     hidden = true;
        //   }
        // });

        // get_back.addEventListener('click', function() {
        //   document.getElementById('get_area').innerHTML = '';
        //   hidden = true;
        // });

        // websocket for printer status
        const PrintStatusSocket = new WebSocket(
            c_wsh
            + window.location.host
            + '/ws/' 
            + c_app_name
            + '/pstatus/'
            + c_bcode
            + '/'
        );
        PrintStatusSocket.onmessage = function(e) {
            // # {
            // #    "cmd":"ps",
            // #    "lastupdate":"2020-05-20 11:00:00",
            // #    "data":[
            // #       {
            // #          "printernumber":"P1",
            // #          "statustext":"good",
            // #          "status":"<P_FINE>"
            // #       },
            // #       {
            // #          "printernumber":"P2",
            // #          "statustext":"Paper out",
            // #          "status":"<P_FINE>"
            // #       }
            // #    ]
            // # }
            // console.log('Received data:', e.data);
            const rxdata = JSON.parse(e.data);
            // console.log('Parsed data:', data);
            // document.querySelectorAll(".status > .vertical-center")[0].innerHTML = data.lastupdate;
            var last = rxdata.lastupdate;
            document.getElementById("lastupdate").innerHTML = 'Last update : ' + last;

            var cmd = rxdata.cmd;
            if (cmd == 'ps') {
                const data = rxdata.data;

                for (var i = 0; i < data.length; i++) {
                    var obj = data[i];
                    var pno = obj.printernumber;
                    var statustext = obj.statustext;
                    var status = obj.status;

                    if (status == "<P_FINE>") {
                        document.getElementById("Printer_" + pno).innerHTML = '';
                    } else if (status == "<P_NEAREND>") {
                        document.getElementById("Printer_" + pno).innerHTML = '<div class="softkey_status_text printer_nearend_text anibackcolorred">' + pno + ' : ' + statustext + '</div>';
                    } else if (status == "<P_END>") {
                        document.getElementById("Printer_" + pno).innerHTML = '<div class="softkey_status_text printer_end_text anibackcolorred">' + pno + ' : ' + statustext + '</div>';
                    } else if (status == "<OPEN>") {
                        document.getElementById("Printer_" + pno).innerHTML = '<div class="softkey_status_text printer_open_text anibackcolorred">' + pno + ' : ' + statustext + '</div>';
                    } else {
                        document.getElementById("Printer_" + pno).innerHTML = '<div class="softkey_status_text printer_ready_text anibackcolorred">' + pno + ' : ' + statustext + '</div>';
                    }
                }
            }        
        };
        PrintStatusSocket.onclose = function(e) {
            console.error('PrinterStatus socket closed unexpectedly');
        };


        // websocket for Counter status
        const CounterStatusSocket = new WebSocket(
            c_wsh
            + window.location.host
            + '/ws/'
            + c_app_name
            + '/cs/'
            + c_bcode
            + '/'
            + c_pk
            + '/'            
        );
        CounterStatusSocket.onmessage = function(e) {
            // # {
            // #    "cmd":"cs",
            // #    "lastupdate":"2020-05-20 11:00:00",
            // #    "data":
            // #    {
            // #     "status": "waiting",", 
            // #     "tickettype": "A",
            // #     "ticketnumber": "012",
            // #     }
            // # }
            // console.log('Received data:', e.data);
            const rxdata = JSON.parse(e.data);
            // console.log('Parsed data:', data);
            // document.querySelectorAll(".status > .vertical-center")[0].innerHTML = data.lastupdate;
            var last = rxdata.lastupdate;
            document.getElementById("lastupdate").innerHTML = 'Last update : ' + last;

            var cmd = rxdata.cmd;
            if (cmd == 'cs') {
                const data = rxdata.data;
                var status = data.status;
                var ttype = data.tickettype;
                var tno = data.ticketnumber;
                var loged = data.login;

                changeStatus(status, ttype, tno, loged);
            }        
        };
        CounterStatusSocket.onclose = function(e) {
            console.error('CounterStatus socket closed unexpectedly');
        };


        // websocket for Q list        
        const QListSocket = new WebSocket(
          c_wsh
          + window.location.host
          + '/ws/'
          + c_app_name
          + '/ql/'
          + c_bcode
          + '/'
          + c_ct
          + '/'
        );
        QListSocket.onmessage = function(e) {
            // # {"cmd":"add",
            // #  "lastupdate":now,
            // #  "data":
            // #    {
            // #     "tickettype": "A", 
            // #     "ticketnumber": "012",
            // #     "tickettime": "2023-03-17T15:06:53.337639Z",
            // #     "tickettime": "2023-03-17T15:06:53.337639Z",
            // #     "tickettime_local": "23:06:53 2023-03-17",
            // #     "tickettime_local_short": "23:06:53 03-17",
            // #     "ttid": 1,
            // #     }
            // # }
            // console.log('Received data:', e.data);
            const rxdata = JSON.parse(e.data);
            // console.log('Parsed data:', data);
            // document.querySelectorAll(".status > .vertical-center")[0].innerHTML = data.lastupdate;
            var last = rxdata.lastupdate;
            document.getElementById("lastupdate").innerHTML = 'Last update : ' + last;

            var cmd = rxdata.cmd;
            if (cmd == 'add' || cmd == 'del'); {
                const data = rxdata.data;                
                var ttype = data.tickettype;
                var tno = data.ticketnumber;
                var ttime = data.tickettime;
                var ttime_local = data.tickettime_local;
                var ttime_local_short = data.tickettime_local_short;
                var ttid = data.ttid;

                // check cmd add or del
                var subtotal = 0;
                if (cmd == 'add') {
                  // 
                  subtotal = 1;
                  // add to list
                  if (c_waitinglist_show == true) {
                    document.getElementById("qlist_area").innerHTML = document.getElementById("qlist_area").innerHTML + 
                    `
                    <div id="ticket_` + ttype + tno + ttime + `" class="qlist_item">
                      <div class="qlist_ticketnumber">` + ttype + tno + `</div>
                      <div class="qlist_tickettime">` + ttime_local_short + `</div>
                      <a class="btn btn--del" href=` + 
                      `/softkey_void/` +
                      c_pk + 
                      `/` +
                      ttid + `/` +
                      `>Void</a>
                    </div>
                    `
                  };
                } else if (cmd == 'del') {
                  subtotal = -1;
                  // remove from list
                  if (c_waitinglist_show == true) {
                    document.getElementById("ticket_" + ttype + tno + ttime).outerHTML = '';
                  };
                }
                
                // update subtotal
                var s_sub = document.getElementById("subtotal_" + ttype).innerHTML;
                var i_sub = parseInt(s_sub);
                i_sub = i_sub + subtotal;
                document.getElementById("subtotal_" + ttype).innerHTML = i_sub;
              }
            
        };
        QListSocket.onclose = function(e) {
            console.error('Q List socket closed unexpectedly');
        };
        
        

