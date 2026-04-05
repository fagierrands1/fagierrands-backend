#!/bin/bash
set -e

echo "Starting gunicorn..."
exec gunicorn fagierrandsbackup.wsgi --log-file -
