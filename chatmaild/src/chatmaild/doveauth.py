#!/usr/bin/env python3
import base64
import sys

from .database import Database


def get_user_data(db, user):
    with db.read_connection() as conn:
        result = conn.get_user(user)
    if result:
        result["uid"] = "vmail"
        result["gid"] = "vmail"
    return result


def create_user(db, user, password):
    with db.write_transaction() as conn:
        conn.create_user(user, password)
    return dict(home=f"/home/vmail/{user}", uid="vmail", gid="vmail", password=password)


def verify_user(db, user, password):
    userdata = get_user_data(db, user)
    if userdata:
        if userdata.get("password") == password:
            userdata["status"] = "ok"
        else:
            userdata["status"] = "fail"
    else:
        userdata = create_user(db, user, password)
        userdata["status"] = "ok"

    return userdata


def lookup_user(db, user):
    userdata = get_user_data(db, user)
    if userdata:
        userdata["status"] = "ok"
    else:
        userdata["status"] = "fail"
    return userdata


def dump_result(res):
    for key, value in res.items():
        print(f"{key}={value}")


def main():
    db = Database("/home/vmail/passdb.sqlite")
    if sys.argv[1] == "hexauth":
        login = base64.b16decode(sys.argv[2]).decode()
        password = base64.b16decode(sys.argv[3]).decode()
        res = verify_user(db, login, password)
        dump_result(res)
    elif sys.argv[1] == "hexlookup":
        login = base64.b16decode(sys.argv[2]).decode()
        res = lookup_user(db, login)
        dump_result(res)


if __name__ == "__main__":
    main()
