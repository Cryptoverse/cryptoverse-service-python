#!/bin/bash
# Make sure environmental variables are set before running this script.
redis-server &
celery -A tasks worker --loglevel=INFO &
python app.py