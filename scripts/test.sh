#!/bin/bash

pushd chatmaild
tox
popd 

pushd deploy-chatmail
tox
popd 

venv/bin/pytest tests/online -vrx --durations=5 $@
