#!/bin/sh
set -e

export FLASK_APP=server.py
flask db upgrade
python scripts/migrate_legacy_files.py

exec gunicorn --bind 0.0.0.0:${PORT:-8083} --workers ${WEB_CONCURRENCY:-2} --threads ${WEB_THREADS:-8} --timeout 120 server:app
