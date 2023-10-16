#!/bin/bash
set -e
pushd chatmaild/src/chatmaild
../../venv/bin/pytest
popd

online-tests/venv/bin/pytest online-tests/ -vrx --durations=5
