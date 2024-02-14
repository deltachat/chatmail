#!/bin/bash
set -e
python3 -m venv --upgrade-deps venv

if [ -z ${SOCKS5_PROXY+x} ]; then
    venv/bin/pip install -e chatmaild
    venv/bin/pip install -e cmdeploy
else
    venv/bin/pip install --proxy socks5://$SOCKS5_PROXY -e chatmaild
    venv/bin/pip install --proxy socks5://$SOCKS5_PROXY -e cmdeploy
fi
