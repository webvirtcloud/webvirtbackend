#!/usr/bin/env bash
set -e

.venv/bin/python3 manage.py migrate
.venv/bin/python3 manage.py loaddata */fixtures/*.json

exit 0