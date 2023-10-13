#!/bin/sh
python3 -m venv chatmail-pyinfra/venv
chatmail-pyinfra/venv/bin/pip install pyinfra
chatmail-pyinfra/venv/bin/pip install -e chatmail-pyinfra
python3 -m venv doveauth/venv
doveauth/venv/bin/pip install -e doveauth
