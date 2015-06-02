#!/usr/bin/python
import sys

if (len(sys.argv) < 1):
    print "Filename required"
    sys.exit(-1)

infile = open(sys.argv[1], "r")
timeout = 119
for line in infile.readlines():
    parts = line.split(";")
    parts = map(lambda x: x.strip(), parts)
    time = float(parts[2])
    if (time >= timeout):
        if ("UNREAL" in parts[0] or "unrael" in parts[0]):
            print parts[0] + "\t $UNREAL"
        else:
            print parts[0] + "\t $REAL"
