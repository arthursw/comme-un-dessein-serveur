# --- CommeUnDessein --- #

CommeUnDessein/Espero are collaborative apps.

# development

Requirements:

virtualenv CommeUnDesseinProject

pip install ...

 - Django==1.9.13
 - django-allauth
 - django-paypal
 - gevent==1.1b4 
 - gevent-socketio 			# !!! check that it did not replace gevent with `pip show gevent` (should be version 1.1b4)
 - mongoengine


## Fix gevent-socketio

gevent-socketio is a bit out-of-date:

Replace

from django.utils.importlib import import_module

by



or 

from importlib import import_module

in

lib/python2.7/site-packages/socketio/sdjango.py (line 6)

## Get js libraries

 - bootstrap
 - bootstrap-colorpickersliders
 - bootstrap-modal.min.js
 - bootstrap-modalmanager.min.js
 - bootstrap-slider.js
 - dat.gui.js
 - domReady.js
 - FileSaver.min.js
 - flashsocket
 - jqtree
 - jquery-2.1.3.min.js
 - jquery-transform
 - jquery-ui.min.js
 - jquery.mCustomScrollbar.min.js
 - jquery.mousewheel.min.js
 - jquery.nanoscroller.js
 - jquery.oembed.js
 - jQueryUI
 - js.cookie.js
 - jszip
 - live.js
 - paper-full.js
 - perfect-scrollbar
 - pinit.js
 - RequestAnimationFrame.js
 - require.js
 - sb-1.4.1.min.js
 - socket.io.js
 - spin.js
 - bootstrap-table
 - tinycolor.js
 - tween.min.js
 - typeahead.bundle.js
 - underscore-min.js
 - video-js.css
 - ZeroClipboard

## Migrate

`python manage.py migrate`


## Creating an admin user

`python manage.py createsuperuser`

## Create site

If the site does not exists, you will have the following error: `Site matching query does not exist`

in python shell:

`python manage.py shell`


`from django.contrib.sites.models import Site`

`new_site = Site.objects.create(domain='localhost:8000', name='localhost:8000')`
`print new_site.id`

Now set that site ID in your settings.py to SITE_ID

http://stackoverflow.com/questions/11814059/site-matching-query-does-not-exist


## Client:

Copy comme-un-dessein-client in `comme-un-dessein-server/CommeUnDessein/static/`

`git clone https://github.com/arthursw/comme-un-dessein-client.git`

beside CommeUnDessein root directory

## Collect static files

`python manage.py collectstatic`

This will move django admin static files AND comme-un-dessein static files into comme-un-dessein-server/CommeUnDessein/CommeUnDessein/static/

## Add social apps

Add Github, Facebook, Google keys at http://comme-un-dessein.space/admin/socialaccount/socialapp/

Update IDs:

https://console.developers.google.com/

## Create drawings directory

Create the directory comme-un-dessein-server/CommeUnDessein/CommeUnDessein/static/drawings/
where the images (.png and .svg) will be saved, otherwise the server won't find the path and throw an error.

## Note to fix websocket

A bug in gevent can be fixed by reinstalling gevent version 1.1b4

sudo pip uninstall gevent
sudo pip install gevent==1.1b4

## Running in production

activate your virtualenv with `source bin/activate`
The goal is to run `python run.py` so that it does not stop when leaving ssh session.

### Simple but unpractical solution with nohup

 - run: `nohup python run.py &`
 - stop: 
    - find process id with: `ps -ef | grep "python run.py"` (it will be listed like `idlv     14137 14056  0 13:56 pts/3    00:00:09 python run.py`, the second number is the PID)
    - kill process by id with: `kill -9 PID`

### Better solution with screen

 - *Only the first time*: create a *commeundessein* session: `screen -S commeundessein`
 - go to previous *commeundessein* session: `screen -r commeundessein`
 - then you can use the terminal normally to activate your virtualenv: `source bin/activate` then `cd CommeUnDessein`
 - then run: `python run.py`
 - to stop: press `ctrl a then d`
 - to exit session (should not be necessary): (in a session) `exit`

## Warnings when using multiple users (am & idlv)

You can clone the repo multiple times on the server to manage different users.
Just keep in mind that static files will always be served from the same repo, so pulling and using `collectstatic` will have effect only on the served files.

## SSL config - Let's Encrypt

SSL config https://www.digitalocean.com/community/tutorials/how-to-secure-nginx-with-let-s-encrypt-on-ubuntu-16-04