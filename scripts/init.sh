#!/bin/sh
python3 -m venv chatmail-pyinfra/venv
chatmail-pyinfra/venv/bin/pip install pyinfra pytest
chatmail-pyinfra/venv/bin/pip install -e chatmail-pyinfra
chatmail-pyinfra/venv/bin/pip install -e doveauth

python3 -m venv doveauth/venv
doveauth/venv/bin/pip install pytest build
doveauth/venv/bin/pip install -e doveauth

python3 -m venv online-tests/venv
online-tests/venv/bin/pip install pytest pytest-timeout pdbpp deltachat
