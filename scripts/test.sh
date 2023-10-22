#!/bin/bash
tox -c chatmaild
tox -c deploy-chatmail
venv/bin/pytest tests/online -vrx --durations=5 $@
