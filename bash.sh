#! /bin/bash

source /home/hurricane/.virtualenvs/LAN-Debug-Server/bin/activate
cd /home/hurricane/Program/LAN-Debug-Server || exit
gunicorn -c gunicorncfg.py app:app
