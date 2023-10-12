#!/usr/bin/env python3
import base64
import sys


def get_user_data(user):
    if user == b"link2xt@instant2.testrun.org":
        return dict(
            homedir="/home/vmail/link2xt",
            uid="vmail",
            gid="vmail",
            password=b"Ahyei6ie"
        )
    return {}


def verify_user(user, password):
    userdata = get_user_data(user)
    if userdata.get("password") == password:
        userdata["status"] = "ok"
        return userdata
    return dict(status="fail")


def lookup_user(user):
    userdata = get_user_data(user)
    if userdata:
        userdata["status"] = "ok"
    else:
        userdata["status"] = "fail"
    return userdata


def dump_result(res):
    for key, value in res.items():
        print(f"{key}={value}")


if sys.argv[1] == "hexauth":
    login = base64.b16decode(sys.argv[2])
    password = base64.b16decode(sys.argv[3])
    res = verify_user(login, password)
    dump_result(res)
elif sys.argv[1] == "hexlookup":
    login = base64.b16decode(sys.argv[2])
    res = lookup_user(login)
    dump_result(res)

