#!/bin/sh
set -e

: ${CHATMAIL_DOMAIN:=c1.testrun.org}
: ${CHATMAIL_SSH:=$CHATMAIL_DOMAIN}

rsync -avz . "root@$CHATMAIL_SSH:/root/chatmail" --exclude='/.git' --filter="dir-merge,- .gitignore"
ssh "root@$CHATMAIL_SSH" "cd /root/chatmail; apt install -y python3-venv; python3 -m venv venv; venv/bin/pip install pyinfra build; venv/bin/python3 -m build -n --sdist chatmaild --outdir dist; venv/bin/pip install -e ./deploy-chatmail -e ./chatmaild; export CHATMAIL_DOMAIN=$CHATMAIL_DOMAIN; venv/bin/pyinfra @local deploy.py"
