from flask import Flask, jsonify, request
import time
import os

from database import Database
from util import gen_password, get_valid_email_addr, encrypt_password
from doveauth import get_user_data


def create_app_from_db_path(db_path=None):
    db = Database(db_path)
    return create_app_from_db(db)


def create_app_from_db(db):
    app = Flask("chatmaild-http")
    app.db = db

    @app.route("/", methods=["POST"])
    def new_email():
        for i in range(10):
            addr = get_valid_email_addr()
            if not get_user_data(db, addr):
                cleartext_password = gen_password()
                encrypted_password = encrypt_password(cleartext_password)
                q = """INSERT INTO users (addr, password, last_login)
                       VALUES (?, ?, ?)"""
                with db.write_transaction() as conn:
                    conn.execute(q, (addr, encrypted_password, int(time.time())))
                return jsonify(
                    email=addr,
                    password=cleartext_password,
                )
        return jsonify(
            type="error",
            status_code=409,
            reason="all 10 email addresses we tried are taken"
        )

    return app


def main():
    """(debugging-only!) serve http account creation Web API on localhost"""
    db_path = os.getenv("CHATMAIL_DATABASE", "/home/vmail/passdb.sqlite")
    app = create_app_from_db_path(db_path)
    if __name__ == "__main__":
        app.run(debug=True, host="localhost", port=3691)
