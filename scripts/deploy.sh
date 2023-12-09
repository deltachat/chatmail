#!/usr/bin/env bash

echo -----------------------------------------
echo deploying to $CHATMAIL_DOMAIN 
echo -----------------------------------------


venv/bin/pyinfra --ssh-user root "$CHATMAIL_DOMAIN" \
    deploy-chatmail/src/deploy_chatmail/deploy.py run chatmail.ini
