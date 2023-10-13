#!/bin/sh
chatmail-pyinfra/venv/bin/pytest chatmail-pyinfra/tests
cd doveauth/src/doveauth
../../venv/bin/pytest
