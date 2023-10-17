#!/bin/bash
chatmaild/venv/bin/pytest chatmaild/ $@
online-tests/venv/bin/pytest online-tests/ -vrx --durations=5 $@
