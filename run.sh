#!/bin/bash
# Make sure environmental variables are set before running this script.
if [ $NO_GATEWAY == '1' ]; then
	python app.py
else
	gunicorn -w 4 -b 127.0.0.1:5000 app:app
fi