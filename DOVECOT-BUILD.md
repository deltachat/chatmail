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

### How to built the dovecot debian package for all platforms 

XXX As is, i am not sure i understand the instructions and how the patches are actually applied
XXX during building. 
XXX I'd prefer we have a full github repository with our dovecot-fork as submodule
XXX and then execute "osc" commands there, if possible. 

On a Debian machine (for exampe [distrobox](https://distrobox.it/)),
clone the [chatmail dovecot fork](https://github.com/chatmail/dovecot). 
In the directory above it, put the source code tar balls from 
[upstream debian unstable](https://packages.debian.org/unstable/dovecot-core). 
These are the two files ending in .tar.gz. 

Now run the command `debuild -us -uc` in the dovecot repo we cloned. 
This creates the files needed for the OBS.

Now copy the two .tar.gz. archives from before, 
the tar.xz archive and the .dsc file into your local OBS repository. 

With `osc add *` (don't add .osc) and `osc commit` the state is pushed to build.opensuse.org. 
The OBS will now build the deb files for aarch64, armv7l, i586 and x86_64.

### Adding the resulting OBS repository to Debian

XXX maybe better link to the deployment code adding the key (https://github.com/deltachat/chatmail/blob/main/cmdeploy/src/cmdeploy/__init__.py) and not spell out the download links here 

XXX is there no standard "apt-add-repository" possible? 

To add the OBS-managed signing key to your local install: 

    https://build.opensuse.org/projects/home:deltachat/signing_keys/download?kind=gpg | sudo gpg --dearmor -o /etc/apt/keyrings/obs-home-deltachat.gpg`

Add to /etc/apt/sources.list:

`deb [signed-by=/etc/apt/keyrings/obs-home-deltachat.gpg] https://download.opensuse.org/repositories/home:/deltachat/Debian_12/ ./`

Install dovecot 🥳

`sudo apt update
sudo apt install dovecot-core`

### Security concerns 

The signing of the patched dovecot package is done in the OBS and 
in theory SUSE could make changes to the package delivered.
It is probably reasonable to trust SUSE to not mess with the build
process because it would cause serious negative reputation damage for them 
if they tried and someone finds out. 

Any security vulnerability in dovecot needs to be tracked 
and also mirrored in our fork. 
