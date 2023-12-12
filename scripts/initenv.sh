#!/bin/bash
set -e
python3 -m venv venv

venv/bin/pip install -e chatmaild 
venv/bin/pip install -e cmdeploy
