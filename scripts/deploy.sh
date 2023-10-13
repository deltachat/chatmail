#!/usr/bin/env bash
: ${CHATMAIL_DOMAIN:=c1.testrun.org}
export CHATMAIL_DOMAIN

pushd doveauth
venv/bin/python3 -m build
popd

pushd filtermail
venv/bin/python3 -m build
popd

chatmail-pyinfra/venv/bin/pyinfra --ssh-user root "$CHATMAIL_DOMAIN" deploy.py

#rm -r doveauth/dist/
#rm -r filtermail/dist/
