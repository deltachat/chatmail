#!/bin/sh
set -e
python3 -m venv venv
pip=venv/bin/pip

$pip install pyinfra pytest build 'setuptools>=68' tox 
$pip install -e deploy-chatmail 
$pip install -e chatmaild 
