#!/usr/bin/env bash
: ${CHATMAIL_DOMAIN:=c1.testrun.org}
export CHATMAIL_DOMAIN
chatmail-pyinfra/venv/bin/pyinfra --ssh-user root "$CHATMAIL_DOMAIN" deploy.py
