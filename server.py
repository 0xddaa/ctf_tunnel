#!/usr/bin/python
# coding=utf-8

import socket, sys
from thread import *
import subprocess as sp
import time
import json
import datetime

whitelist = ["10.218.0.3", "10.218.254.1"]

def readline(s):
    buf = ""
    try:
        while True:
            buf += s.recv(1)
            if "\n" in buf:
                return buf
    except:
        sys.exit(1)

def threadWork(csock):
    s_ports = [10001, 10002]
    gameboxs = []
    for i in range(20):
        gameboxs.append("10.217.%d.201" % (i+1))

    # parse tunnel info
    try:
        buf = readline(csock)
        tinfo_json = json.loads(buf.strip("\n"))
        tport = str(tinfo_json["service_id"])
        tmp = str(tinfo_json["fake_team"])
        if len(tmp) < 2:
            tmp = "0"+tmp 
        tport += tmp
        tmp = str(tinfo_json["target_team"])
        if len(tmp) < 2:
            tmp = "0"+tmp 
        tport += tmp
    except:
       csock.send("json format error\n")
       csock.close()
       sys.exit(1)

    # build tunnel and return tunnel port
    f_ip = sp.Popen("ip route get 10.217.%s.201| awk 'NR==1 {print $NF}'" % (tinfo_json["fake_team"]), shell=True, stdout=sp.PIPE).stdout.read().strip("\n")
    t_ip = gameboxs[int(tinfo_json["target_team"])-1]
    dport = s_ports[int(tinfo_json["service_id"])-1]
#    tunnel = "ncat -vc \"nc -s %s %s %s\" -kl %s > /dev/null 2>&1" % (f_ip, t_ip, dport, tport)
    tunnel = "ncat -vc \"nc -s %s %s %s\" -kl %s" % (f_ip, t_ip, dport, tport)
    print "tunnel: "+ tunnel
    tport_json = [{"tunnel_port":tport}]
    csock.send(json.dumps(tport_json) + "\n")

    # get service status
    status_json = json.loads(readline(csock).strip("\n"))

    logfile = "log/%s" % (tport)
    if "Fail" in status_json["status"]:
        check = "curl -d \"ip=%s&port=%s&state=2&comment='From %s'\" 10.218.0.100/admin/update_service_state" % (t_ip, dport, f_ip)
    else:
        check = "curl -d \"ip=%s&port=%s&state=0&comment='From %s'\" 10.218.0.100/admin/update_service_state" % (t_ip, dport, f_ip)

    p = sp.Popen(check, shell=True, stdout=sp.PIPE, stderr=sp.PIPE)
    print p.stdout.read()
    csock.send("update service status to [%s]\n" % (status_json["status"]))
    csock.close()
    sys.exit(1)



try:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
except socket.error, msg:
    sys.stderr.write("[ERROR] %s\n" % msg[1])
    sys.exit(1)

sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
sock.bind(('', 1234))
sock.listen(5)

while True:
    (csock, addr) = sock.accept()
    src = addr[0]
    for i in whitelist:
        if src == i:
            start_new_thread(threadWork, (csock,))


sock.close()
