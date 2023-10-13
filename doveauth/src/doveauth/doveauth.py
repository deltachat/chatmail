#!/usr/bin/env python3
import base64
import sys


def get_user_data(user):
    if user.startswith("link2xt@"):
        return dict(
            uid="vmail",
            gid="vmail",
            password="Ahyei6ie",
        )
    return {}


def create_user(user, password):
    return dict(home=f"/home/vmail/{user}", uid="vmail", gid="vmail", password=password)


def verify_user(user, password):
    userdata = get_user_data(user)
    if userdata:
        if userdata.get("password") == password:
            userdata["status"] = "ok"
        else:
            userdata["status"] = "fail"
    else:
        userdata = create_user(user, password)
        userdata["status"] = "ok"

    return userdata


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


def main():
    if sys.argv[1] == "hexauth":
        login = base64.b16decode(sys.argv[2]).decode()
        password = base64.b16decode(sys.argv[3]).decode()
        res = verify_user(login, password)
        dump_result(res)
    elif sys.argv[1] == "hexlookup":
        login = base64.b16decode(sys.argv[2]).decode()
        res = lookup_user(login)
        dump_result(res)


if __name__ == "__main__":
    main()
