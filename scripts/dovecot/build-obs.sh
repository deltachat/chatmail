#!/bin/bash

# this script requires curl, osc and debuild installed.
# on debian you need to run: apt install devscripts build-essential osc curl

# Install dependencies
echo "Installing dependencies for this script:"
sudo apt install devscripts build-essential osc curl git debhelper-compat

echo "Installing build dependencies"
sudo apt install default-libmysqlclient-dev krb5-multidev libapparmor-dev libbz2-dev libcap-dev libdb-dev libexpat-dev libexttextcat-dev libicu-dev libldap2-dev liblua5.4-dev liblz4-dev liblzma-dev libpam0g-dev libpq-dev libsasl2-dev libsodium-dev libsqlite3-dev libssl-dev libstemmer-dev libsystemd-dev libunwind-dev libwrap0-dev libzstd-dev pkg-config zlib1g-dev

# Define path of your local OBS repository
REPO_PATH=$OBS_PATH/home:deltachat/dovecot/
SCRIPT_DIR=$PWD
OBS_PATH=$SCRIPT_DIR/obs

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
# debuild -us -uc

# Setting up OSC
cd $OBS_PATH
mkdir $OBS_PATH
rm -rf home:deltachat/dovecot
osc checkout home:deltachat/dovecot

# Copy Files to Your Local OBS Repository,
echo "Copying files to your local OBS repository..."
cd $SCRIPT_DIR/dovecot-build
cp -rf dovecot_2.3.21+dfsg1-3.debian.tar.xz $REPO_PATH
cp -rf dovecot_2.3.21+dfsg1.orig.tar.gz $REPO_PATH
cp -rf dovecot_2.3.21+dfsg1.orig-pigeonhole.tar.gz $REPO_PATH
cp -rf dovecot_2.3.21+dfsg1-3.dsc $REPO_PATH

# Push Changes to OBS
echo "Pushing changes to OBS..."
cd $REPO_PATH

osc up
osc add dovecot_2.3.21+dfsg1-3.debian.tar.xz
osc add dovecot_2.3.21+dfsg1.orig.tar.gz
osc add dovecot_2.3.21+dfsg1.orig-pigeonhole.tar.gz
osc add dovecot_2.3.21+dfsg1-3.dsc

osc commit
