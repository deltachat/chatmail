#!/usr/bin/env python3
import base64
import sys

if sys.argv[1] == "hexauth":
    login = base64.b16decode(sys.argv[2])
    password = base64.b16decode(sys.argv[3])
    if login == b"link2xt@instant2.testrun.org" and password == b"Ahyei6ie":
        print("status=ok")
        print("homedir=/home/vmail/link2xt")
        print("gid=vmail")
        print("uid=vmail")
    else:
        print("status=fail")
elif sys.argv[1] == "hexlookup":
    login = base64.b16decode(sys.argv[2])
    if login == b"link2xt@instant2.testrun.org":
        print("status=ok")
        print("homedir=/home/vmail/link2xt")
        print("gid=vmail")
        print("uid=vmail")
    else:
        print("status=fail")
