#!/usr/bin/env bash
set -e

.venv/bin/python3 manage.py migrate

exit 0