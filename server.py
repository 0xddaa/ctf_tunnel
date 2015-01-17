#!/usr/bin/python3
# coding=utf-8

import socket, sys
import subprocess as sp
import time
import json
import datetime
import concurrent.futures

whitelist = ["10.218.0.3", "10.218.254.1"]

def tostr(buf):
    return buf.decode("utf-8")

def tobyte(s):
    return s.encode("utf-8")

def readline(s):
    buf = ""
    try:
        buf = s.recv(1024)
        return tostr(buf)
    except e:
        sys.exit(0)

def threadWork(csock):
    s_ports = [443, 21025, 3650]
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
    except Exception as e:
#        print(e.args)
        csock.send(tobyte("json format error\n"))
        csock.close()
        sys.exit(0)

    # build tunnel and return tunnel port
    f_ip = sp.Popen("ip route get 10.217.%s.201| awk 'NR==1 {print $NF}'" % (tinfo_json["fake_team"]), shell=True, stdout=sp.PIPE).stdout.read()
    f_ip = tostr(f_ip).strip("\n")
    t_ip = gameboxs[int(tinfo_json["target_team"])-1]
    dport = s_ports[int(tinfo_json["service_id"])-1]
    tunnel = "ncat -vc \"nc -s %s %s %s\" -kl %s > /dev/null 2>&1" % (f_ip, t_ip, dport, tport)
    msg = "tunnel: "+ tunnel + "\n"
    tport_json = [{"tunnel_port":tport}]
    csock.send(tobyte(json.dumps(tport_json) + "\n"))
    
    # get service status
    try:
        buf = readline(csock).strip("\n")
        status_json = json.loads(buf)
    
        logfile = "log/%s" % (tport)
        if "Fail" in status_json["status"]:
            check = "curl -d \"ip=%s&port=%s&state=2&comment='From %s'\" 10.218.0.100/admin/update_service_state" % (t_ip, dport, f_ip)
        else:
            check = "curl -d \"ip=%s&port=%s&state=0&comment='From %s'\" 10.218.0.100/admin/update_service_state" % (t_ip, dport, f_ip)
        
        p = sp.Popen(check, shell=True, stdout=sp.PIPE, stderr=sp.PIPE)
        msg += p.stdout.read()
        print(msg)
        print(check)
        csock.send(tobyte("update service status to [%s]\n" % (status_json["status"])))
        csock.close()
    except Exception as e:
        #print(e.args)
        sys.exit(1)
    return



with concurrent.futures.ThreadPoolExecutor(max_workers=100) as executor:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(('', 1234))
        sock.listen(5)

        while True:
            (csock, addr) = sock.accept()
            src = addr[0]
            for i in whitelist:
                if src == i:
                    executor.submit(threadWork, csock)


sock.close()
