
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

1. Setup DNS `A` and `AAAA` records for your `CHATMAIL_DOMAIN`. 
   Verify that DNS is set and SSH root login works:

   ```
        ssh root@CHATMAIL_DOMAIN 
   ```

2. Install the `cmdeploy` command in a virtualenv

   ```
    scripts/initenv.sh
   ```
  
3. Create chatmail configuration file `chatmail.ini`:

   ```
    scripts/cmdeploy init CHATMAIL_DOMAIN
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

6. To check status of your remotely running chatmail service: 

   ```
    scripts/cmdeploy status
   ```

7. To test your chatmail service: 

   ```
    scripts/cmdeploy test
   ```

8. To benchmark your chatmail service: 

   ```
    scripts/cmdeploy bench
   ```

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


### Home page and getting started for users 

`cmdeploy run` sets up mail services,
and also creates default static Web pages and deploys them: 

- a default `index.html` along with a QR code that users can click to 
  create accounts on your chatmail provider,

- a default `info.html` that is linked from the home page,

- a default `policy.html` that is linked from the home page. 

All `.html` files are generated 
by the according markdown `.md` file in the `www/src` directory.


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



