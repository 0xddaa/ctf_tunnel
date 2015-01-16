import subprocess as sp

def make_tunnel():
    s_ports = [10001, 10002, 10003]
    for i in range(0, 20):
        for j in range(0, 20):
           for k in range(0, 3):
               f_ip = sp.Popen("ip route get 10.217.%s.201| awk 'NR==1 {print $NF}'" % (i+1), shell=True, stdout=sp.PIPE).stdout.read().strip("\n")
               t_ip = "10.217.%d.201" % (j+1)
               dport = s_ports[k]
               tport = str(k+1)
               tmp = str(i+1)
               if len(tmp) < 2:
                   tmp = "0"+tmp 
               tport += tmp
               tmp = str(j+1)
               if len(tmp) < 2:
                   tmp = "0"+tmp 
               tport += tmp
               tunnel = "ncat -vc \"nc -s %s %s %s\" -kl %s > /dev/null 2>&1" % (f_ip, t_ip, dport, tport)
               print tunnel
               t = sp.Popen(tunnel, shell=True)

make_tunnel()


