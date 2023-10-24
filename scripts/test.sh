#!/bin/bash
venv/bin/tox -c chatmaild
venv/bin/tox -c deploy-chatmail
venv/bin/pytest tests/online -vrx --durations=5 $@
