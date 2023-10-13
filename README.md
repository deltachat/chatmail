# Chat Mail server configuration

This package deploys Postfix and Dovecot servers, including OpenDKIM for DKIM signing.

Postfix uses Dovecot for authentication as described in <https://www.postfix.org/SASL_README.html#server_dovecot>

## Structure (wip)

```

# package doveauth tool and deploy chatmail server to a envvar-specified ssh-reachable host 
deploy.py 

# chatmail pyinfra deploy package 
pyinfra-src
    pyproject.toml
    chatmail/__init__ ...

    # tests against the deployed system 
    tests/test_online_test.py

# doveauth tool used by dovecot's auth mechanism on the host system 
doveauth-src 
    README.md
    pyproject.toml
    doveauth.py
    doveauth.lua
    test_doveauth.py
```

## Ports

Postfix listens on ports 25 (smtp) and 587 (submission) and 465 (submissions).
Dovecot listens on ports 143(imap) and 993 (imaps).

## DNS

For DKIM you must add a DNS entry as in /etc/opendkim/selector.txt (where selector is the opendkim_selector configured in the chatmail inventory).

## Run with pyinfra

```
CHATMAIL_DOMAIN=c1.testrun.org pyinfra --ssh-user root c1.testrun.org deploy.py
```
