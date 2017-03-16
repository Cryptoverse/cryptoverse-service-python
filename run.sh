#!/bin/bash
# Make sure environmental variables are set before running this script.
redis-server &
celery -A tasks worker --loglevel=INFO &
gunicorn -w 4 -b 127.0.0.1:5000 app:app