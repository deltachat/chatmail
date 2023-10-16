#!/bin/sh
set -e
python3 -m venv deploy-chatmail/venv
deploy-chatmail/venv/bin/pip install pyinfra pytest
deploy-chatmail/venv/bin/pip install -e deploy-chatmail
deploy-chatmail/venv/bin/pip install -e chatmaild

python3 -m venv chatmaild/venv
chatmaild/venv/bin/pip install pytest
chatmaild/venv/bin/pip install -e chatmaild

python3 -m venv online-tests/venv
online-tests/venv/bin/pip install pytest pytest-timeout pdbpp deltachat pytest-benchmark

python3 -m venv venv
venv/bin/pip install build
venv/bin/pip install 'setuptools>=68'
