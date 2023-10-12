# Chat Mail server configuration

This package deploys Postfix and Dovecot servers, including OpenDKIM for DKIM signing.

Postfix uses Dovecot for authentication as described in <https://www.postfix.org/SASL_README.html#server_dovecot>

## Ports

Postfix listens on ports 25 (smtp) and 587 (submission) and 465 (submissions).
Dovecot listens on ports 143(imap) and 993 (imaps).

## DNS

For DKIM you must add a DNS entry as in /etc/opendkim/selector.txt (where selector is the opendkim_selector configured in the chatmail inventory).

## Run with pyinfra

```
CHATMAIL_DOMAIN=c1.testrun.org pyinfra c1.testrun.org deploy.py
```
