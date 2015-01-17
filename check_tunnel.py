#!/usr/bin/python

import telnetlib
import subprocess as sp

while True:
    count = 0
    p = sp.Popen("nc -v -w 5 localhost 20101", shell=True, stdout=sp.PIPE, stderr=sp.PIPE)
    buf = p.stdout.read(10)
    if len(buf) != 10:
        count += 1
        if count >= 3:
            print "tunnel error"
    else:
        print "OK"
