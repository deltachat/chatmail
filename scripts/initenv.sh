#!/bin/sh
set -e
python3 -m venv --upgrade-deps venv

venv/bin/pip install -e chatmaild 
venv/bin/pip install -e cmdeploy
