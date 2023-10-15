#!/bin/sh
python3 -m venv deploy-chatmail/venv
deploy-chatmail/venv/bin/pip install pyinfra pytest
deploy-chatmail/venv/bin/pip install -e deploy-chatmail
deploy-chatmail/venv/bin/pip install -e doveauth

python3 -m venv doveauth/venv
doveauth/venv/bin/pip install pytest
doveauth/venv/bin/pip install -e doveauth

python3 -m venv online-tests/venv
online-tests/venv/bin/pip install pytest pytest-timeout pdbpp deltachat

python3 -m venv venv
venv/bin/pip install build
