
<img width="800px" src="www/src/collage-top.png"/>

# Chatmail services optimized for Delta Chat apps 

This repository helps to setup a ready-to-use chatmail server
comprised of a minimal setup of the battle-tested 
[postfix smtp](https://www.postfix.org) and [dovecot imap](https://www.dovecot.org) services. 

The setup is designed and optimized for providing chatmail accounts 
for use by [Delta Chat apps](https://delta.chat).

Chatmail accounts are automatically created by a first login, 
after which the initially specified password is required for using them. 

## Deploying your own chatmail server 

We subsequently use `CHATMAIL_DOMAIN` as a placeholder for your fully qualified 
DNS domain name (FQDN), for example `chat.example.org`.

1. Install the `cmdeploy` command in a virtualenv

   ```
    git clone https://github.com/deltachat/chatmail
    cd chatmail
    scripts/initenv.sh
   ```
  
2. Create chatmail configuration file `chatmail.ini`:

   ```
    scripts/cmdeploy init CHATMAIL_DOMAIN
   ```

3. Setup first DNS records for your `CHATMAIL_DOMAIN`,
   according to the hints provided by `cmdeploy init`.
   Verify that SSH root login works:

   ```
        ssh root@CHATMAIL_DOMAIN
   ```

4. Deploy to the remote chatmail server:

   ```
    scripts/cmdeploy run
   ```

5. To output a DNS zone file from which you can transfer DNS records 
   to your DNS provider:

   ```
    scripts/cmdeploy dns
   ```

### Other helpful commands:

To check the status of your remotely running chatmail service:

```
scripts/cmdeploy status
```

To test whether your chatmail service is working correctly:

```
scripts/cmdeploy test
```

To measure the performance of your chatmail service:

```
scripts/cmdeploy bench
```

## Overview of this repository

This repository drives the development of "chatmail instances",
comprised of minimal setups of

- [postfix smtp server](https://www.postfix.org)
- [dovecot imap server](https://www.dovecot.org)

as well as custom services that are integrated with these two:

- `chatmaild/src/chatmaild/doveauth.py` implements
  create-on-login account creation semantics and is used
  by Dovecot during login authentication and by Postfix
  which in turn uses [Dovecot SASL](https://doc.dovecot.org/configuration_manual/authentication/dict/#complete-example-for-authenticating-via-a-unix-socket)
  to authenticate users
  to send mails for them.

- `chatmaild/src/chatmaild/filtermail.py` prevents
  unencrypted e-mail from leaving the chatmail instance
  and is integrated into postfix's outbound mail pipelines.

There is also the `cmdeploy/src/cmdeploy/cmdeploy.py` command line tool
which helps with setting up and managing the chatmail service.
`cmdeploy run` uses [pyinfra-based scripting](https://pyinfra.com/)
in `cmdeploy/src/cmdeploy/__init__.py`
to automatically install all chatmail components on a server.


### Home page and getting started for users

`cmdeploy run` also creates default static Web pages and deploys them
to an nginx web server under `https://CHATMAIL_DOMAIN`.

- a default `index.html` along with a QR code that users can click to
  create accounts on your chatmail provider,

- a default `info.html` that is linked from the home page,

- a default `policy.html` that is linked from the home page.

All `.html` files are generated
by the according markdown `.md` file in the `www/src` directory.


### Refining the web pages


```
scripts/cmdeploy webdev
```

This starts a local live development cycle for chatmail Web pages:

- uses the `www/src/page-layout.html` file for producing static
  HTML pages from `www/src/*.md` files

- continously builds the web presence reading files from `www/src` directory
  and generating html files and copying assets to the `www/build` directory.

- Starts a browser window automatically where you can "refresh" as needed.


## Emergency Commands to disable automatic account creation

If you need to stop account creation,
e.g. because some script is wildly creating accounts,
login to the server with ssh and run:

```
    touch /etc/chatmail-nocreate
```

While this file is present, account creation will be blocked.

### Ports

Postfix listens on ports 25 (smtp) and 587 (submission) and 465 (submissions).
Dovecot listens on ports 143(imap) and 993 (imaps).

Delta Chat apps will, however, discover all ports and configurations
automatically by reading the `autoconfig.xml` file from the chatmail service.


