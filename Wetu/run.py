#!/usr/bin/env python

# from gevent import monkey
# from socketio.server import SocketIOServer
# import django.core.handlers.wsgi
# import os
# import sys

# monkey.patch_all()
import mongoengine
import os
import sys


from gevent import monkey

monkey.patch_all()
import threading

from socketio.server import SocketIOServer
import django.core.handlers.wsgi


dir = os.path.dirname(__file__)
sys.path.insert(0, os.path.join(dir, 'Wetu'))

try:
    import settings
except ImportError:
    sys.stderr.write("Error: Can't find the file 'settings.py' in the directory containing %r. It appears you've customized things.\nYou'll have to run django-admin.py, passing it your settings module.\n(If the file settings.py does indeed exist, it's causing an ImportError somehow.)\n" % __file__)
    sys.exit(1)


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "Wetu.settings")

import django
django.setup()

PORT = 8000

os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'

application = django.core.handlers.wsgi.WSGIHandler()

# sys.path.insert(0, os.path.join(settings.PROJECT_ROOT, "apps"))
sys.path.insert(0, os.path.join(settings.PROJECT_ROOT, "draw"))

if __name__ == '__main__':
    print 'Listening on http://127.0.0.1:%s and on port 10843 (flash policy server)' % PORT
    SocketIOServer(('', PORT), application, resource="socket.io").serve_forever()
