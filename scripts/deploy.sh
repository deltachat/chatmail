#!/usr/bin/env bash
: ${CHATMAIL_DOMAIN:=c1.testrun.org}
export CHATMAIL_DOMAIN

venv/bin/python3 -m build -n --sdist doveauth --outdir dist
venv/bin/python3 -m build -n --sdist filtermail --outdir dist

deploy-chatmail/venv/bin/pyinfra --ssh-user root "$CHATMAIL_DOMAIN" deploy.py

rm -r dist/
