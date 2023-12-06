#!/usr/bin/env bash

echo -----------------------------------------
echo deploying to $CHATMAIL_DOMAIN 
echo -----------------------------------------

#echo WARNING: in five seconds deploy to $CHATMAIL_DOMAIN starts
#sleep 5

venv/bin/python3 -m build -n --sdist chatmaild --outdir dist

venv/bin/pyinfra --ssh-user root "$CHATMAIL_DOMAIN" \
    deploy-chatmail/src/deploy_chatmail/deploy.py

rm -r dist/
