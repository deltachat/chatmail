# Chat Mail server configuration

This package deploys Postfix and Dovecot servers, including OpenDKIM for DKIM signing.

Postfix uses Dovecot for authentication as described in <https://www.postfix.org/SASL_README.html#server_dovecot>

## Getting started 

prepare:

    pip install -e chatmail-infra


then run with pyinfra command line tool: 

    CHATMAIL_DOMAIN=c1.testrun.org pyinfra --ssh-user root c1.testrun.org deploy.py


## Structure (wip)
```

# package doveauth tool and deploy chatmail server to a envvar-specified ssh-reachable host 
deploy.py 

# chatmail pyinfra deploy package 
chatmail-pyinfra 
    pyproject.toml
    chatmail/__init__ ...

# doveauth tool used by dovecot's auth mechanism on the host system 
doveauth
    README.md
    pyproject.toml
    doveauth.py
    test_doveauth.py

# lmtp server to block (outgoing) unencrypted messages 
filtermail 
    README.md
    pyproject.toml
    .... 

# online tests (after deploy)

online-tests  # runnable via pytest 



# scripts for setup/development/deployment 

scripts/
    init.sh  # create venv/other perequires
    deploy.sh  # run pyinfra based deploy of everything
    test.sh # run all local and online tests 
    bench.sh # run performance benchmark tests

```

## Dovecot/Postfix configuration

### Ports

Postfix listens on ports 25 (smtp) and 587 (submission) and 465 (submissions).
Dovecot listens on ports 143(imap) and 993 (imaps).

## DNS

For DKIM you must add a DNS entry as in /etc/opendkim/selector.txt (where selector is the opendkim_selector configured in the chatmail inventory).
