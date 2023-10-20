#!/bin/sh
set -e
python3 -m venv deploy-chatmail/venv
deploy-chatmail/venv/bin/pip install pyinfra pytest
deploy-chatmail/venv/bin/pip install -e deploy-chatmail
deploy-chatmail/venv/bin/pip install -e chatmaild

python3 -m venv chatmaild/venv
chatmaild/venv/bin/pip install --upgrade pytest build 'setuptools>=68'
chatmaild/venv/bin/pip install -e chatmaild

python3 -m venv online-tests/venv
online-tests/venv/bin/pip install pytest pytest-timeout pdbpp deltachat 
