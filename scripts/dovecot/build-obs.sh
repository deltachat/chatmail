#!/bin/bash

# this script requires wget, osc and debuild installed.

# Define path of your local OBS repository
OBS_PATH=~/obs/home:deltachat/dovecot/

# Download Debian Source Files
echo "Downloading precise files from Debian unstable repository..."
mkdir dovecot-build
cd dovecot-build

# taken May 6th 2024, from https://packages.debian.org/unstable/dovecot-core 
curl http://deb.debian.org/debian/pool/main/d/dovecot/dovecot_2.3.21+dfsg1-3.debian.tar.xz --output dovecot_2.3.21+dfsg1-3.debian.tar.xz
curl http://deb.debian.org/debian/pool/main/d/dovecot/dovecot_2.3.21+dfsg1.orig.tar.gz --output dovecot_2.3.21+dfsg1.orig.tar.gz
curl http://deb.debian.org/debian/pool/main/d/dovecot/dovecot_2.3.21+dfsg1.orig-pigeonhole.tar.gz --output dovecot_2.3.21+dfsg1.orig-pigeonhole.tar.gz

# Clone the Chatmail Dovecot Repo
echo "Cloning the Chatmail Dovecot fork..."
git clone https://github.com/chatmail/dovecot.git

# Build the Package
echo "Building the package..."
cd dovecot
debuild -us -uc
cd ..

# Copy Files to Your Local OBS Repository, TODO how to do this best?
echo "Copying files to your local OBS repository..."
cp dovecot_2.3.21+dfsg1-3.debian.tar.xz $OBS_PATH
cp dovecot_2.3.21+dfsg1.orig.tar.gz $OBS_PATH
cp dovecot_2.3.21+dfsg1.orig-pigeonhole.tar.gz $OBS_PATH

# Push Changes to OBS
echo "Pushing changes to OBS..."
cd /path/to/your/local/obs/repo/
osc add dovecot_2.3.21+dfsg1-3.debian.tar.xz
osc add 
osc add
osc commit
