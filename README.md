# Chatmail instances optimized for Delta Chat apps 

This repository helps to setup a ready-to-use chatmail instance
comprised of a minimal setup of the battle-tested 
[postfix smtp](https://www.postfix.org) and [dovecot imap](https://www.dovecot.org) services. 

The setup is designed and optimized for providing chatmail accounts 
for use by [Delta Chat apps](https://delta.chat).

Chatmail accounts are automatically created by a first login, 
after which the initially specified password is required for using them. 

## Getting Started deploying your own chatmail instance

1. Prepare your local (presumably Linux) system:

    scripts/init.sh 

2. Setup a domain with `A` and `AAAA` records for your chatmail server.

3. Set environment variable to the chatmail domain you want to setup:

    export CHATMAIL_DOMAIN=c1.testrun.org   # replace with your host

4. Deploy the chat mail instance to your chatmail server: 

    scripts/deploy.sh 

   This script uses `pyinfra` and `ssh` to setup packages and configure
   the chatmail instance on your remote server. 

5. Run `scripts/generate-dns-zone.sh` and 
   transfer the generated DNS records at your DNS provider

6. Start a Delta Chat app and create a new account 
   by typing an e-mail address with an arbitrary username 
   and `@<your-chatmail-domain>` appended. 
   Use an at least 10-character random password. 


### Ports

Postfix listens on ports 25 (smtp) and 587 (submission) and 465 (submissions).
Dovecot listens on ports 143(imap) and 993 (imaps).

Delta Chat will, however, discover all ports and configurations 
automatically by reading the `autoconfig.xml` file from the chatmail instance. 


## Emergency Commands to disable automatic account creation 

If you need to stop account creation,
e.g. because some script is wildly creating accounts, run:

    touch /etc/chatmail-nocreate

While this file is present, account creation will be blocked. 


## Running tests and benchmarks (offline and online) 

1. Set `CHATMAIL_SSH` so that `ssh root@$CHATMAIL_SSH` allows 
   to login to the chatmail instance server. 

2. To run local and online tests: 

    scripts/test.sh 

3. To run benchmarks against your chatmail instance: 

    scripts/bench.sh 


## Development Background for chatmail instances 

This repository drives the development of "chatmail instances", 
comprised of minimal setups of 

- [postfix smtp server](https://www.postfix.org) 
- [dovecot imap server](https://www.dovecot.org) 

as well as two custom services that are integrated with these two: 

- `chatmaild/src/chatmaild/doveauth.py` implements
  create-on-login account creation semantics and is used
  by Dovecot during login authentication and by Postfix
  which in turn uses [Dovecot SASL](https://doc.dovecot.org/configuration_manual/authentication/dict/#complete-example-for-authenticating-via-a-unix-socket)
  to authenticate users
  to send mails for them. 

- `chatmaild/src/chatmaild/filtermail.py` prevents 
  unencrypted e-mail from leaving the chatmail instance
  and is integrated into postfix's outbound mail pipelines. 



