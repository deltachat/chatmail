
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

To deploy chatmail on your own server, you must have set-up ssh authentication and need to use an ed25519 key, due to an [upstream bug in paramiko](https://github.com/paramiko/paramiko/issues/2191). You also need to add your private key to the local ssh-agent, because you can't type in your password during deployment.

We use `chat.example.org` as the chatmail domain in the following steps. 
Please substitute it with your own domain. 

1. Install the `cmdeploy` command in a virtualenv

   ```
    git clone https://github.com/deltachat/chatmail
    cd chatmail
    scripts/initenv.sh
   ```

2. Create chatmail configuration file `chatmail.ini`:

   ```
    scripts/cmdeploy init chat.example.org  # <-- use your domain 
   ```

3. Point your domain to the server's IP address,
   if you haven't done so already.
   Verify that SSH root login works:

   ```
    ssh root@chat.example.org   # <-- use your domain 
   ```

4. Deploy to the remote chatmail server:

   ```
    scripts/cmdeploy run
   ```
   This script will check that you have all necessary DNS records.
   If DNS records are missing, it will recommend
   which you should configure at your DNS provider
   (it can take some time until they are public).

### Other helpful commands:

To check the status of your remotely running chatmail service:

```
scripts/cmdeploy status
```

To display and check all recommended DNS records:

```
scripts/cmdeploy dns
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

This repository drives the development of chatmail services, 
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
  unencrypted e-mail from leaving the chatmail service
  and is integrated into postfix's outbound mail pipelines.

There is also the `cmdeploy/src/cmdeploy/cmdeploy.py` command line tool
which helps with setting up and managing the chatmail service.
`cmdeploy run` uses [pyinfra-based scripting](https://pyinfra.com/)
in `cmdeploy/src/cmdeploy/__init__.py`
to automatically install all chatmail components on a server.


### Home page and getting started for users

`cmdeploy run` also creates default static Web pages and deploys them
to a nginx web server with: 

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

[Postfix](http://www.postfix.org/) listens on ports 25 (smtp) and 587 (submission) and 465 (submissions).
[Dovecot](https://www.dovecot.org/) listens on ports 143 (imap) and 993 (imaps).
[nginx](https://www.nginx.com/) listens on port 8443 (https-alt) and 443 (https).
Port 443 multiplexes HTTPS, IMAP and SMTP using ALPN to redirect connections to ports 8443, 465 or 993.
[acmetool](https://hlandau.github.io/acmetool/) listens on port 80 (http).

Delta Chat apps will, however, discover all ports and configurations
automatically by reading the [autoconfig XML file](https://www.ietf.org/archive/id/draft-bucksch-autoconfig-00.html) from the chatmail service.

## Email authentication

chatmail servers rely on [DKIM](https://www.rfc-editor.org/rfc/rfc6376)
to authenticate incoming emails.
Incoming emails must have a valid DKIM signature with
Signing Domain Identifier (SDID, `d=` parameter in the DKIM-Signature header)
equal to the `From:` header domain.
This property is checked by OpenDKIM screen policy script
before validating the signatures.
This correpsonds to strict [DMARC](https://www.rfc-editor.org/rfc/rfc7489) alignment (`adkim=s`),
but chatmail does not rely on DMARC and does not consult the sender policy published in DMARC records.
Other legacy authentication mechanisms such as [iprev](https://www.rfc-editor.org/rfc/rfc8601#section-2.7.3)
and [SPF](https://www.rfc-editor.org/rfc/rfc7208) are also not taken into account.
If there is no valid DKIM signature on the incoming email,
the sender receives a "5.7.1 No valid DKIM signature found" error.

Outgoing emails must be sent over authenticated connection
with envelope MAIL FROM (return path) corresponding to the login.
This is ensured by Postfix which maps login username
to MAIL FROM with
[`smtpd_sender_login_maps`](https://www.postfix.org/postconf.5.html#smtpd_sender_login_maps)
and rejects incorrectly authenticated emails with [`reject_sender_login_mismatch`](reject_sender_login_mismatch) policy.
`From:` header must correspond to envelope MAIL FROM,
this is ensured by `filtermail` proxy.

## Migrating chatmail server to a new host

If you want to migrate your chatmail server to a new host,
follow these steps:

1. Block all ports except 80 and 22 with firewall on a new server.

   To do this, add the following config to `/etc/nftables.conf`:
```
#!/usr/sbin/nft -f

flush ruleset

table inet filter {
    chain input {
        type filter hook input priority filter; policy drop;

        # Accept ICMP.
        # It is especially important to accept ICMPv6 ND messages,
        # otherwise IPv6 connectivity breaks.
        icmp type { echo-request } accept
        icmpv6 type { echo-request, nd-neighbor-solicit, nd-router-advert, nd-neighbor-advert } accept

        tcp dport { ssh, http } accept

        ct state established accept
    }
    chain forward {
        type filter hook forward priority filter;
    }
    chain output {
        type filter hook output priority filter;
    }
}
```
   Then execute `nft -f /etc/nftables.conf` as root.

   This will ensure users will not connect to the new server
   and mails will not be delivered to the new server
   before you finish the setup.

   Port 22 is needed for SSH access
   and port 80 is needed to get a TLS certificate.
   They are not used by Delta Chat
   or by other email servers trying to deliver the messages.

2. Point DNS to the new IP addresses.

   You can already remove the old IP addresses from DNS.
   Existing Delta Chat users will still be able to connect
   to the old server, send and receive messages,
   but new users will fail to create new profiles
   with your chatmail server.

3. Setup the new server with `cmdeploy`.

   This step is similar to initial setup.
   However, because ports Delta Chat uses are blocked,
   new server will not become usable immediately.
   If other servers try to deliver messages to your new server they will fail,
   but normally email servers will retry delivering messages
   for at least a week, so messages will not be lost.

4. Firewall all ports except `ssh` (22) on the old server.
   Existing users will not be able to connect from now on
   and no more messages will be delivered to your old chatmail server.

   Blocking users from connecting to the new server
   until mailboxes are migrated is needed to avoid UID validity change.
   If Delta Chat connects to the new server before it is fully set up,
   it will lose track of the IMAP message UID
   and miss messages that arrived during migration.

   Same for SMTP port 25, you want it blocked during migration so no new mails arrive
   while the server is moving.

5. Use `rsync -avz` over SSH to copy /home/vmail/mail from the old server to the new one
   preserving file permissions and timestamps.

6. Unblock ports used by Delta Chat and SMTP message exchange.
   For that you can modify `/etc/nftables.conf` as follows:
```
#!/usr/sbin/nft -f

flush ruleset

table inet filter {
    chain input {
        type filter hook input priority filter; policy drop;

        # Accept ICMP.
        # It is especially important to accept ICMPv6 ND messages,
        # otherwise IPv6 connectivity breaks.
        icmp type { echo-request } accept
        icmpv6 type { echo-request, nd-neighbor-solicit, nd-router-advert, nd-neighbor-advert } accept

        tcp dport { ssh, smtp, http, https, imap, imaps, submission, submissions } accept

        ct state established accept
    }
    chain forward {
        type filter hook forward priority filter;
    }
    chain output {
        type filter hook output priority filter;
    }
}
```
Execute `nft -f /etc/nftables.conf` as root to apply the changes.
