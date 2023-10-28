#!/bin/bash
set -e

venv/bin/pytest online-tests/benchmark.py -vrx 
