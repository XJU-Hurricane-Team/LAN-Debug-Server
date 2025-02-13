#! /bin/bash

source /home/hurricane/.virtualenvs/JlinkSite/bin/activate
cd /home/hurricane/Program/JlinkSite || exit
gunicorn -c gunicorncfg.py app:app
