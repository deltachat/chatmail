#!/bin/bash
set -e
python3 -m venv venv

venv/bin/pip install -e chatmaild 
venv/bin/pip install -e cmdeploy

source venv/bin/activate
echo activated 'venv' python virtualenv environment containing "cmdeploy" tool
