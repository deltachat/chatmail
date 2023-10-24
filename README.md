# Chat Mail server configuration

This repository setups a ready-to-go chatmail instance
comprised of a minimal setup of the battle-tested 
[postfix smtp server](https://www.postfix.org) and [dovecot imap server](https://www.dovecot.org).

## Getting started 

1. prepare your local system:

    scripts/init.sh 

2. setup a domain with `A` and `AAAA` records for your chatmail server

3. set environment variable to the chatmail domain you want to setup:

    export CHATMAIL_DOMAIN=c1.testrun.org   # replace with your host

4. run the deploy of the chat mail instance: 

    scripts/deploy.sh 

5. run `scripts/generate-dns-zone.sh` and create the generated DNS records at your DNS provider

## Running tests and benchmarks (offline and online) 

1. Set `CHATMAIL_SSH` so that `ssh root@$CHATMAIL_SSH` allows 
   to login to the chatmail instance server. 

2. To run local and online tests: 

    scripts/test.sh 

3. To run benchmarks against your chatmail instance: 

    scripts/bench.sh 

## Running tests (offline and online) 

```
## Dovecot/Postfix configuration

### Ports

Postfix listens on ports 25 (smtp) and 587 (submission) and 465 (submissions).
Dovecot listens on ports 143(imap) and 993 (imaps).

## DNS

For DKIM you must add a DNS entry as found in /etc/opendkim/selector.txt on your chatmail instance.
The above `scripts/deploy.sh` prints out the DKIM selector and DNS entry you
need to setup with your DNS provider. 

## Emergency Commands

If you need to stop account creation,
e.g. because some script is wildly creating accounts,
just run `touch /tmp/nocreate`.
You can remove the file
as soon as the attacker was banned
by different means.

