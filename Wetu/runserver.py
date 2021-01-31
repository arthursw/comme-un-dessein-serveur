#!/usr/bin/env python

from gevent import monkey
monkey.patch_all()

import os
import sys
from psycogreen.gevent import patch_psycopg


dir = os.path.dirname(__file__)
sys.path.insert(0, os.path.join(dir, 'Wetu'))

try:
    import settings
except ImportError:
    sys.stderr.write("Error: Can't find the file 'settings.py' in the directory containing %r. It appears you've customized things.\nYou'll have to run django-admin.py, passing it your settings module.\n(If the file settings.py does indeed exist, it's causing an ImportError somehow.)\n" % __file__)
    sys.exit(1)

sys.path.insert(0, os.path.join(settings.PROJECT_ROOT, "draw")) # should not be necessary

PORT = 8000

os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'

patch_psycopg()

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()


if __name__ == '__main__':
    from socketio.server import SocketIOServer
    server = SocketIOServer(('', PORT), application, resource="socket.io")
    server.serve_forever()