
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

This repository has four directories:

- [cmdeploy](https://github.com/deltachat/chatmail/tree/main/cmdeploy)
  is a collection of configuration files
  and a [pyinfra](https://pyinfra.com)-based deployment script.

- [chatmaild](https://github.com/deltachat/chatmail/tree/main/chatmaild)
  is a python package containing several small services
  which handle authentication,
  trigger push notifications on new messages,
  ensure that outbound mails are encrypted,
  delete inactive users,
  and some other minor things.
  chatmaild can also be installed as a stand-alone python package.

- [www](https://github.com/deltachat/chatmail/tree/main/www)
  contains the html, css, and markdown files
  which make up a chatmail server's web page.
  Edit them before deploying to make your chatmail server stand out.

- [scripts](https://github.com/deltachat/chatmail/tree/main/scripts)
  offers two convenience tools for beginners;
  `initenv.sh` installs the necessary dependencies to a local virtual environment,
  and the `scripts/cmdeploy` script enables you
  to run the `cmdeploy` command line tool in the local virtual environment.

### cmdeploy

The `cmdeploy/src/cmdeploy/cmdeploy.py` command line tool
helps with setting up and managing the chatmail service.
`cmdeploy init` creates the `chatmail.ini` config file.
`cmdeploy run` uses a [pyinfra](https://pyinfra.com/)-based [script](`cmdeploy/src/cmdeploy/__init__.py`)
to automatically install or upgrade all chatmail components on a server,
according to the `chatmail.ini` config.

The components of chatmail are:

- [postfix smtp server](https://www.postfix.org) accepts sent messages (both from your users and from other servers)

- [dovecot imap server](https://www.dovecot.org) stores messages for your users until they download them

- [nginx](https://nginx.org/) shows the web page with your privacy policy and additional information

- [acmetool](https://hlandau.github.io/acmetool/) manages TLS certificates for dovecot, postfix, and nginx

- [opendkim](http://www.opendkim.org/) for signing messages with DKIM and rejecting inbound messages without DKIM

- [mtail](https://google.github.io/mtail/) for collecting anonymized metrics in case you have monitoring

- and the chatmaild services, explained in the next section:

### chatmaild

chatmaild offers several commands
which differentiate a *chatmail* server from a classic mail server.
If you deploy them with cmdeploy,
they are run by systemd services in the background.
A short overview:

- [`doveauth`](https://github.com/deltachat/chatmail/blob/main/chatmaild/src/chatmaild/doveauth.py) implements
  create-on-login account creation semantics and is used
  by Dovecot during login authentication and by Postfix
  which in turn uses [Dovecot SASL](https://doc.dovecot.org/configuration_manual/authentication/dict/#complete-example-for-authenticating-via-a-unix-socket)
  to authenticate users
  to send mails for them.

- [`filtermail`](https://github.com/deltachat/chatmail/blob/main/chatmaild/src/chatmaild/filtermail.py) prevents
  unencrypted e-mail from leaving the chatmail service
  and is integrated into postfix's outbound mail pipelines.

- [`chatmail-metadata`](https://github.com/deltachat/chatmail/blob/main/chatmaild/src/chatmaild/metadata.py) is contacted by a
  [dovecot lua script](https://github.com/deltachat/chatmail/blob/main/cmdeploy/src/cmdeploy/dovecot/push_notification.lua)
  to store user-specific server-side config.
  On new messages,
  it [passes the user's push notification token](https://github.com/deltachat/chatmail/blob/main/chatmaild/src/chatmaild/notifier.py)
  to [notifications.delta.chat](https://delta.chat/help#instant-delivery)
  so the push notifications on the user's phone can be triggered
  by Apple/Google.

- [`delete_inactive_users`](https://github.com/deltachat/chatmail/blob/main/chatmaild/src/chatmaild/delete_inactive_users.py)
  deletes users if they have not logged in for a very long time.
  The timeframe can be configured in `chatmail.ini`.

- [`lastlogin`](https://github.com/deltachat/chatmail/blob/main/chatmaild/src/chatmaild/lastlogin.py)
  is contacted by dovecot when a user logs in
  and stores the date of the login.

- [`echobot`](https://github.com/deltachat/chatmail/blob/main/chatmaild/src/chatmaild/echo.py)
  is a small bot for test purposes.
  It simply echoes back messages from users.

- [`chatmail-metrics`](https://github.com/deltachat/chatmail/blob/main/chatmaild/src/chatmaild/metrics.py)
  collects some metrics and displays them at `https://example.org/metrics`.

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

If you want to migrate chatmail from an old machine
to a new machine,
you can use these steps.
They were tested with a linux laptop;
you might need to adjust some of the steps to your environment.

Let's assume that your `mail_domain` is `mail.example.org`,
all involved machines run Debian 12,
your old server's IP address is `13.37.13.37`,
and your new server's IP address is `13.12.23.42`.

During the guide, you might get a warning about changed SSH Host keys;
in this case, just run `ssh-keygen -R "mail.example.org"` as recommended
to make sure you can connect with SSH.

1. First, copy `/var/lib/acme` to the new server with
   `ssh root@13.37.13.37 tar c /var/lib/acme | ssh root@13.12.23.42 tar x -C /var/lib/`.
   This transfers your TLS certificate.

2. You should also copy `/etc/dkimkeys` to the new server with
   `ssh root@13.37.13.37 tar c /etc/dkimkeys | ssh root@13.12.23.42 tar x -C /etc/`
   so the DKIM DNS record stays correct.

3. On the new server, run `chown root: -R /var/lib/acme` and `chown opendkim: -R /etc/dkimkeys` to make sure the permissions are correct.

4. Run `cmdeploy run --disable-mail --ssh-host 13.12.23.42` to install chatmail on the new machine.
   postfix and dovecot are disabled for now,
   we will enable them later.

5. Now, point DNS to the new IP addresses.

   You can already remove the old IP addresses from DNS.
   Existing Delta Chat users will still be able to connect
   to the old server, send and receive messages,
   but new users will fail to create new profiles
   with your chatmail server.

   If other servers try to deliver messages to your new server they will fail,
   but normally email servers will retry delivering messages
   for at least a week, so messages will not be lost.

6. Now you can run `cmdeploy run --disable-mail --ssh-host 13.37.13.37` to disable your old server.

   Now your users will notice the migration
   and will not be able to send or receive messages
   until the migration is completed.

7. After everything is stopped,
    you can copy the `/home/vmail/mail` directory to the new server.
    It includes all user data, messages, password hashes, etc.

    Just run: `ssh root@13.37.13.37 tar c /home/vmail/mail | ssh root@13.12.23.42 tar x -C /home/vmail/`

    After this, your new server has all the necessary files to start operating :)

8. To be sure the permissions are still fine,
    run `chown vmail: -R /home/vmail` on the new server.

9. Finally, you can run `cmdeploy run` to turn on chatmail on the new server.
    Your users can continue using the chatmail server,
    and messages which were sent after step 6. should arrive now.
    Voilà!

## Setting up a reverse proxy

A chatmail server does not depend on the client IP address
for its operation, so it can be run behind a reverse proxy.
This will not even affect incoming mail authentication
as DKIM only checks the cryptographic signature
of the message and does not use the IP address as the input.

For example, you may want to self-host your chatmail server
and only use hosted VPS to provide a public IP address
for client connections and incoming mail.
You can connect chatmail server to VPS
using a tunnel protocol
such as [WireGuard](https://www.wireguard.com/)
and setup a reverse proxy on a VPS
to forward connections to the chatmail server
over the tunnel.
You can also setup multiple reverse proxies
for your chatmail server in different networks
to ensure your server is reachable even when
one of the IPs becomes inaccessible due to
hosting or routing problems.

Note that your server still needs
to be able to make outgoing connections on port 25
to send messages outside.

To setup a reverse proxy
(or rather Destination NAT, DNAT)
for your chatmail server,
put the following configuration in `/etc/nftables.conf`:
```
#!/usr/sbin/nft -f

flush ruleset

define wan = eth0

# Which ports to proxy.
#
# Note that SSH is not proxied
# so it is possible to log into the proxy server
# and not the original one.
define ports = { smtp, http, https, imap, imaps, submission, submissions }

# The host we want to proxy to.
define ipv4_address = AAA.BBB.CCC.DDD
define ipv6_address = [XXX::1]

table ip nat {
        chain prerouting {
                type nat hook prerouting priority dstnat; policy accept;
                iif $wan tcp dport $ports dnat to $ipv4_address
        }

        chain postrouting {
                type nat hook postrouting priority 0;

                oifname $wan masquerade
        }
}

table ip6 nat {
        chain prerouting {
                type nat hook prerouting priority dstnat; policy accept;
                iif $wan tcp dport $ports dnat to $ipv6_address
        }

        chain postrouting {
                type nat hook postrouting priority 0;

                oifname $wan masquerade
        }
}

table inet filter {
        chain input {
                type filter hook input priority filter; policy drop;

                # Accept ICMP.
                # It is especially important to accept ICMPv6 ND messages,
                # otherwise IPv6 connectivity breaks.
                icmp type { echo-request } accept
                icmpv6 type { echo-request, nd-neighbor-solicit, nd-router-advert, nd-neighbor-advert } accept

                # Allow incoming SSH connections.
                tcp dport { ssh } accept

                ct state established accept
        }
        chain forward {
                type filter hook forward priority filter; policy drop;

                ct state established accept
                ip daddr $ipv4_address counter accept
                ip6 daddr $ipv6_address counter accept
        }
        chain output {
                type filter hook output priority filter;
        }
}
```

Run `systemctl enable nftables.service`
to ensure configuration is reloaded when the proxy server reboots.

Uncomment in `/etc/sysctl.conf` the following two lines:

```
net.ipv4.ip_forward=1
net.ipv6.conf.all.forwarding=1
```

Then reboot the server or do `sysctl -p` and `nft -f /etc/nftables.conf`.

Once proxy server is set up,
you can add its IP address to the DNS.
