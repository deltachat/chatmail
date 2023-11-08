#!/bin/bash
set -e

venv/bin/pytest tests/online/benchmark.py -vrx
