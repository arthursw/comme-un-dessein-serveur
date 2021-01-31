#!/usr/bin/env python
import os
import sys

# added to fit gevent socketio tutorial: http://www.pixeldonor.com/2014/jan/10/django-gevent-and-socketio/
# but hot reload does not work
# from gevent import monkey
# monkey.patch_all()

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "Wetu.settings")

    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)
