## Introduction to custom Dovecot builds

Chatmail servers use a custom Debian build of the IMAP 'dovecot' server software because 

a) Dovecot developers did not yet merge a [pull request](https://github.com/dovecot/core/pull/216)
   which majorly speeds up message delivery by removing a hardcoded 0.5 second delay 
   on relaying incoming messages.  

b) Even if merged, it would take years for it to reach Debian stable,
   the distribution that chatmail deployment uses. 

c) The modified dovecot has been successfully used since December 2023 without issues
   and we see no noticeable downside (theoretically higher CPU usage but not measureable)
   but a considerable upside as the delay-removal facilitates end-to-end message 
   delivery of 200 ms in real networks. 

The modified forked dovecot code lives at 
[https://github.com/chatmail/dovecot](https://github.com/chatmail/dovecot).  
The remainder of this document describes the setup of the Debian repository 
containing the patched dovecot version. 

## Building Debian packages at build.opensuse.org 

Deltachat developers maintain a [shared account](https://build.opensuse.org/project/show/home:deltachat) 
in the [Open Build Service (OBS)](https://openbuildservice.org/), 
where the [resulting package](https://build.opensuse.org/package/show/home:deltachat/dovecot) 
is now used in deploying chatmail servers. 
   
The Open Build Service (OBS) is a platform for building and distributing software packages 
across various operating systems and architectures. 
It supports openSUSE, Fedora, Debian, Ubuntu and Arch.
It's [primary instance](https://build.opensuse.org/) is ran by the openSUSE project 
and is part of the pipeline of the creation of SUSE Linux Enterprise.

The OBS provides a mercurial-like interface to create source repositories 
that are then automatically built. 
While in theory a package can be created entirely over the web interface, 
the use of the cli-tool `osc` is more convenient
and is described in the [official documentation](https://openbuildservice.org/help/manuals/obs-user-guide/art.obs.bg#sec.obsbg.obsconfig).

### How to build the dovecot debian package on the  via our script

In scripts/dovecot/ is a shell script that prepares the required files and pushes them to build.opensuse.org.

Before using the script, you should have osc set up as described in the [official documentation](https://openbuildservice.org/help/manuals/obs-user-guide/art.obs.bg#sec.obsbg.obsconfig).

The script assumes you are on Debian. It automatically installs any needed dependencies and creates the source package. To upload the resulting source package to the OBS you need to enter the username and password for deltachat on build.opensuse.org in the last step of the script.

Use `source build-obs.sh` to run it.

### Adding the resulting OBS repository to Debian 12

Our dovecot fork is automatically installed as part of the chatmail deployment. You can see it in cmdeploy/src/cmdeploy/__init__.py. If you want to add our fork manually to a system, you can do the following:

First add our signing key to your apt keyring:

```
sudo cp cmdeploy/src/cmdeploy/obs-home-deltachat.gpg /etc/apt/keyrings/obs-home-deltachat.gpg`
```

Now add our repository and key to /etc/apt/sources.list with a text editor of your choice:

```
deb [signed-by=/etc/apt/keyrings/obs-home-deltachat.gpg] https://download.opensuse.org/repositories/home:/deltachat/Debian_12/ ./
```

You can now install dovecot like normal.

```
sudo apt update
sudo apt install dovecot-core
```

### Security concerns 

The signing of the patched dovecot package is done in the OBS and 
in theory SUSE could make changes to the package delivered.
It is probably reasonable to trust SUSE to not mess with the build
process because it would cause serious negative reputation damage for them 
if they tried and someone finds out. 

Any security vulnerability in dovecot needs to be tracked 
and also mirrored in our fork. 
