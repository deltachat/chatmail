# Changelog for chatmail deployment 

## untagged

- cmdeploy dns: offer alternative DKIM record format for some web interfaces
  ([#470](https://github.com/deltachat/chatmail/pull/470))

- migration guide: let opendkim own the DKIM keys directory
  ([#468](https://github.com/deltachat/chatmail/pull/468))

- improve secure-join message detection
  ([#473](https://github.com/deltachat/chatmail/pull/473))

## 1.5.0 2024-12-20

- cmdeploy dns: always show recommended DNS records
  ([#463](https://github.com/deltachat/chatmail/pull/463))

- add `--all` to `cmdeploy dns`
  ([#462](https://github.com/deltachat/chatmail/pull/462))

- fix `_mta-sts` TXT DNS record
  ([#461](https://github.com/deltachat/chatmail/pull/461)

- deploy `iroh-relay` and also update "realtime relay services" in privacy policy. 
  ([#434](https://github.com/deltachat/chatmail/pull/434))
  ([#451](https://github.com/deltachat/chatmail/pull/451))

- add guide to migrate chatmail to a new server
  ([#429](https://github.com/deltachat/chatmail/pull/429))

- disable anvil authentication penalty
  ([#414](https://github.com/deltachat/chatmail/pull/444)

- increase `request_queue_size` for UNIX sockets to 1000.
  ([#437](https://github.com/deltachat/chatmail/pull/437))

- add argument to `cmdeploy run` for specifying
  a different SSH host than `mail_domain`
  ([#439](https://github.com/deltachat/chatmail/pull/439))

- query autoritative nameserver to bypass DNS cache
  ([#424](https://github.com/deltachat/chatmail/pull/424))

- add mtail support (new optional `mtail_address` ini value)
  This defines the address on which [`mtail`](https://google.github.io/mtail/)
  exposes its metrics collected from the logs.
  If you want to collect the metrics with Prometheus,
  setup a private network (e.g. WireGuard interface)
  and assign an IP address from this network to the host.
  If you do not plan to collect metrics,
  keep this setting unset.
  ([#388](https://github.com/deltachat/chatmail/pull/388))

- fix checking for required DNS records
  ([#412](https://github.com/deltachat/chatmail/pull/412))

- add support for specifying whole domains for recipient passthrough list
  ([#408](https://github.com/deltachat/chatmail/pull/408))

- add a paragraph about "account deletion" to info page 
  ([#405](https://github.com/deltachat/chatmail/pull/405))

- avoid nginx listening on ipv6 if v6 is dsiabled 
  ([#402](https://github.com/deltachat/chatmail/pull/402))

- refactor ssh-based execution to allow organizing remote functions in
  modules. 
  ([#396](https://github.com/deltachat/chatmail/pull/396))

- trigger "apt upgrade" during "cmdeploy run" 
  ([#398](https://github.com/deltachat/chatmail/pull/398))

- drop hispanilandia passthrough address
  ([#401](https://github.com/deltachat/chatmail/pull/401))

- set CAA record flags to 0

- add IMAP capabilities instead of overwriting them
  ([#413](https://github.com/deltachat/chatmail/pull/413))

- fix OpenPGP payload check
  ([#435](https://github.com/deltachat/chatmail/pull/435))

- fix Dovecot quota_max_mail_size to use max_message_size config value
  ([#438](https://github.com/deltachat/chatmail/pull/438))


## 1.4.1 2024-07-31

- fix metadata dictproxy which would confuse transactions
  resulting in missed notifications and other issues. 
  ([#393](https://github.com/deltachat/chatmail/pull/393))
  ([#394](https://github.com/deltachat/chatmail/pull/394))

- add optional "imap_rawlog" config option. If true, 
  .in/.out files are created in user home dirs 
  containing the imap protocol messages. 
  ([#389](https://github.com/deltachat/chatmail/pull/389))

## 1.4.0 2024-07-28

- Add `disable_ipv6` config option to chatmail.ini.
  Required if the server doesn't have IPv6 connectivity.
  ([#312](https://github.com/deltachat/chatmail/pull/312))

- allow current K9/Thunderbird-mail releases to send encrypted messages
  outside by accepting their localized "encrypted subject" strings. 
  ([#370](https://github.com/deltachat/chatmail/pull/370))

- Migrate and remove sqlite database in favor of password/lastlogin tracking 
  in a user's maildir.  
  ([#379](https://github.com/deltachat/chatmail/pull/379))

- Require pyinfra V3 installed on the client side,
  run `./scripts/initenv.sh` to upgrade locally.
  ([#378](https://github.com/deltachat/chatmail/pull/378))

- don't hardcode "/home/vmail" paths but rather set them 
  once in the config object and use it everywhere else, 
  thereby also improving testability.  
  ([#351](https://github.com/deltachat/chatmail/pull/351))
  temporarily introduced obligatory "passdb_path" and "mailboxes_dir" 
  settings but they were removed/obsoleted in 
  ([#380](https://github.com/deltachat/chatmail/pull/380))

- BREAKING: new required chatmail.ini value 'delete_inactive_users_after = 100'
  which removes users from database and mails after 100 days without any login. 
  ([#350](https://github.com/deltachat/chatmail/pull/350))

- Refine DNS checking to distinguish between "required" and "recommended" settings 
  ([#372](https://github.com/deltachat/chatmail/pull/372))

- reload nginx in the acmetool cronjob
  ([#360](https://github.com/deltachat/chatmail/pull/360))

- remove checking of reverse-DNS PTR records.  Chatmail-servers don't
  depend on it and even in the wider e-mail system it's not common anymore. 
  If it's an issue, a chatmail operator can still care to properly set reverse DNS. 
  ([#348](https://github.com/deltachat/chatmail/pull/348))

- Make DNS-checking faster and more interactive, run it fully during "cmdeploy run",
  also introducing a generic mechanism for rapid remote ssh-based python function execution. 
  ([#346](https://github.com/deltachat/chatmail/pull/346))

- Don't fix file owner ship of /home/vmail 
  ([#345](https://github.com/deltachat/chatmail/pull/345))

- Support iterating over all users with doveadm commands 
  ([#344](https://github.com/deltachat/chatmail/pull/344))

- Test and fix for attempts to create inadmissible accounts 
  ([#333](https://github.com/deltachat/chatmail/pull/321))

- check that OpenPGP has only PKESK, SKESK and SEIPD packets
  ([#323](https://github.com/deltachat/chatmail/pull/323),
   [#324](https://github.com/deltachat/chatmail/pull/324))

- improve filtermail checks for encrypted messages and drop support for unencrypted MDNs
  ([#320](https://github.com/deltachat/chatmail/pull/320))

- replace `bash` with `/bin/sh`
  ([#334](https://github.com/deltachat/chatmail/pull/334))

- Increase number of logged in IMAP sessions to 50000
  ([#335](https://github.com/deltachat/chatmail/pull/335))

- filtermail: do not allow ASCII armor without actual payload
  ([#325](https://github.com/deltachat/chatmail/pull/325))

- Remove sieve to enable hardlink deduplication in LMTP
  ([#343](https://github.com/deltachat/chatmail/pull/343))

- dovecot: enable gzip compression on disk
  ([#341](https://github.com/deltachat/chatmail/pull/341))

- DKIM-sign Content-Type and oversign all signed headers
  ([#296](https://github.com/deltachat/chatmail/pull/296))

- Add nonci_accounts metric
  ([#347](https://github.com/deltachat/chatmail/pull/347))

- doveauth: log when a new account is created
  ([#349](https://github.com/deltachat/chatmail/pull/349))

- Multiplex HTTPS, IMAP and SMTP on port 443
  ([#357](https://github.com/deltachat/chatmail/pull/357))

## 1.3.0 - 2024-06-06

- don't check necessary DNS records on cmdeploy init anymore
  ([#316](https://github.com/deltachat/chatmail/pull/316))

- ensure cron and acl are installed
  ([#293](https://github.com/deltachat/chatmail/pull/293),
  [#310](https://github.com/deltachat/chatmail/pull/310))

- change default for delete_mails_after from 40 to 20 days
  ([#300](https://github.com/deltachat/chatmail/pull/300))

- save journald logs only to memory and save nginx logs to journald instead of file
  ([#299](https://github.com/deltachat/chatmail/pull/299))

- fix writing of multiple obs repositories in `/etc/apt/sources.list`
  ([#290](https://github.com/deltachat/chatmail/pull/290))

- metadata: add support for `/shared/vendor/deltachat/irohrelay`
  ([#284](https://github.com/deltachat/chatmail/pull/284))

- Emit "XCHATMAIL" capability from IMAP server 
  ([#278](https://github.com/deltachat/chatmail/pull/278))

- Move echobot `into /var/lib/echobot`
  ([#281](https://github.com/deltachat/chatmail/pull/281))

- Accept Let's Encrypt's new Terms of Services
  ([#275](https://github.com/deltachat/chatmail/pull/276))

- Reload Dovecot and Postfix when TLS certificate updates
  ([#271](https://github.com/deltachat/chatmail/pull/271))

- Use forked version of dovecot without hardcoded delays
  ([#270](https://github.com/deltachat/chatmail/pull/270))

## 1.2.0 - 2024-04-04

- Install dig on the server to resolve DNS records
  ([#267](https://github.com/deltachat/chatmail/pull/267))

- preserve notification order and exponentially backoff with 
  retries for tokens where we didn't get a successful return
  ([#265](https://github.com/deltachat/chatmail/pull/263))

- Run chatmail-metadata and doveauth as vmail
  ([#261](https://github.com/deltachat/chatmail/pull/261))

- Apply systemd restrictions to echobot
  ([#259](https://github.com/deltachat/chatmail/pull/259))

- re-enable running the CI in pull requests, but not concurrently 
  ([#258](https://github.com/deltachat/chatmail/pull/258))


## 1.1.0 - 2024-03-28

### The changelog starts to record changes from March 15th, 2024 

- Move systemd unit templates to cmdeploy package 
  ([#255](https://github.com/deltachat/chatmail/pull/255))

- Persist push tokens and support multiple device per address 
  ([#254](https://github.com/deltachat/chatmail/pull/254))

- Avoid warning for regular doveauth protocol's hello message. 
  ([#250](https://github.com/deltachat/chatmail/pull/250))

- Fix various tests to pass again with "cmdeploy test". 
  ([#245](https://github.com/deltachat/chatmail/pull/245),
  [#242](https://github.com/deltachat/chatmail/pull/242)

- Ensure lets-encrypt certificates are reloaded after renewal 
  ([#244]) https://github.com/deltachat/chatmail/pull/244

- Persist tokens to avoid iOS users loosing push-notifications when the
  chatmail metadata service is restarted (happens regularly during deploys)
  ([#238](https://github.com/deltachat/chatmail/pull/239)

- Fix failing sieve-script compile errors on incoming messages
  ([#237](https://github.com/deltachat/chatmail/pull/239)

- Fix quota reporting after expunging of old mails
  ([#233](https://github.com/deltachat/chatmail/pull/239)
