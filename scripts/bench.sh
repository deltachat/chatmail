#!/bin/bash
set -e

online-tests/venv/bin/pytest online-tests/benchmark.py -vrx 
