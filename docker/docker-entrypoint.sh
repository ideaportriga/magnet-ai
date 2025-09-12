#!/bin/sh
python update_web_configs.py

# Start app
exec "$@"
