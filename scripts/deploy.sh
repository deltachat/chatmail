#!/usr/bin/env bash
: ${CHATMAIL_DOMAIN:=c1.testrun.org}
export CHATMAIL_DOMAIN

venv/bin/python3 -m build --sdist doveauth --outdir dist
venv/bin/python3 -m build --sdist filtermail --outdir dist

chatmail-pyinfra/venv/bin/pyinfra --ssh-user root "$CHATMAIL_DOMAIN" deploy.py

rm -r dist/
