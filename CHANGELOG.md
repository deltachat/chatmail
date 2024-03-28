# Changelog for chatmail deployment 

## unreleased 

- XXX

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
