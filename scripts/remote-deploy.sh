#!/bin/sh
set -e

: ${CHATMAIL_DOMAIN:=c1.testrun.org}
: ${CHATMAIL_SSH_HOST:=$CHATMAIL_DOMAIN}

rsync -avz . "root@$CHATMAIL_SSH_HOST:/root/chatmail" --exclude='/.git' --filter="dir-merge,- .gitignore"
ssh "root@$CHATMAIL_SSH_HOST" "cd /root/chatmail; apt install -y python3-venv; python3 -m venv venv; venv/bin/pip install pyinfra build; venv/bin/python3 -m build -n --sdist doveauth --outdir dist; venv/bin/python3 -m build -n --sdist filtermail --outdir dist; venv/bin/pip install -e ./deploy-chatmail -e ./doveauth; export CHATMAIL_DOMAIN=$CHATMAIL_DOMAIN; venv/bin/pyinfra @local deploy.py"
