#!/bin/bash
set -e
python3 -m venv venv

venv/bin/pip install -e deploy-chatmail 
venv/bin/pip install -e chatmaild 

source venv/bin/activate
echo activated 'venv' python virtualenv environment containing "cmdeploy" tool
