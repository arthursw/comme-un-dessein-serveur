# Socketio Fix

## Fix gevent-socketio

gevent-socketio is a bit out-of-date:

Replace

from django.utils.importlib import import_module

by



or 

from importlib import import_module

in

lib/python2.7/site-packages/socketio/sdjango.py (line 6)

## Docker

Docker will just copy the file in static/socketio-fix/sdjango.py at the proper location with the following command:

RUN mv CommeUnDessein/static/socketio-fix/sdjango.py $(python -c "import socketio.sdjango as _; print(_.__file__).replace('.pyc', '.py')")