import logging
import datetime
import json
import re
import ast

# from django.utils import simplejson
from django.core import serializers
from django.contrib.auth.models import User
from django.db.models import F
from models import Drawing
from ajax import TIPIBOT_PASSWORD, drawingChanged
from pprint import pprint
from django.contrib.auth import authenticate, login, logout
from paypal.standard.ipn.signals import payment_was_successful, payment_was_flagged, payment_was_refunded, payment_was_reversed
from math import *

from django.core.validators import URLValidator
from django.core.exceptions import ValidationError

from django.dispatch import receiver

from socketio.namespace import BaseNamespace
from socketio.mixins import RoomsMixin, BroadcastMixin
from socketio.sdjango import namespace

from django.utils.html import escape

# from pprint import pprint
# pprint(vars(object))
# import pdb; pdb.set_trace()
# import pudb; pu.db

chatNamespace = None

# --- Receive signals from ajax --- #

# @receiver(drawingValidated)
# def on_drawing_validated(sender, **kwargs):
#     if kwargs is not None and 'clientId' in kwargs and 'status' in kwargs:
#         print "drawing change: " + str(kwargs['clientId']) + ", " + str(kwargs['status'])
#         # chatNamespace.emit_to_room(chatNamespace.room, 'drawing change', {'type': 'status', 'clientId': kwargs['clientId'], 'status': kwargs['status']})
#         chatNamespace.broadcast_event('drawing change', {'type': 'status', 'clientId': kwargs['clientId'], 'status': kwargs['status']})


@receiver(drawingChanged)
def on_drawing_changed(sender, **kwargs):
    if kwargs is not None and 'clientId' in kwargs and 'type' in kwargs:
        print "drawing change: " + str(kwargs['type']) + ", " + str(kwargs['clientId'])

        kwargs.pop('signal', None)
        chatNamespace.broadcast_event('drawing change', kwargs)

@namespace('/chat')
class ChatNamespace(BaseNamespace, RoomsMixin, BroadcastMixin):
    nicknames = []
    validate = URLValidator()
    print("chat namespace")

    def initialize(self):
        print("initialize chat namespace")
        self.logger = logging.getLogger("socketio.chat")
        self.log("Socketio chat session started")
        global chatNamespace
        chatNamespace = self


    def log(self, message):
        self.logger.info(u"[{0}] {1}".format(self.socket.sessid, message))

    def on_join(self, room):
        print("chat namespace on_join")

        if hasattr(self, 'room'):
            self.leave(self.room)
        self.room = room
        self.log(u'Join room: {0}'.format(room))
        self.join(room)

    def on_nickname(self, nickname):
        print("chat namespace on_nickname")
        
        nickname = escape(nickname)
        self.log(u'Nickname: {0}'.format(nickname))
        if 'nickname' in self.socket.session:
            self.nicknames.remove(nickname)
        self.nicknames.append(nickname)
        self.socket.session['nickname'] = nickname
        self.broadcast_event('announcement', '%s has connected' % nickname)
        self.broadcast_event('nicknames', self.nicknames)
        return True, nickname

    # def on_getNextValidatedDrawing(self):
    #     drawings = Drawing.objects(status='drawing')

    #     # get all path of the first drawing
    #     paths = []
    #     for path in drawings.paths:
    #         paths.append(path.to_json())

    #     return json.dumps( {'state': 'success', 'pk': drawing.pk, 'paths': paths } )

    # def on_setDrawingStatusDrawn(self, pk):
    #     if secret != TIPIBOT_PASSWORD:
    #         return json.dumps({'state': 'error', 'message': 'Secret invalid.'})

    #     try:
    #         drawing = Drawing.objects.get(pk=pk)
    #     except Drawing.DoesNotExist:
    #         return json.dumps({'state': 'error', 'message': 'Drawing does not exist.', 'pk': pk})
        
    #     drawing.status = 'drawn'
    #     drawing.save()

    #     return json.dumps( {'state': 'success', 'message': 'Drawing status successfully updated.' } )

    def recv_disconnect(self):
        # Remove nickname from the list.
        if 'nickname' in self.socket.session:
            nickname = self.socket.session['nickname']
            self.log(u'Disconnect: {0}'.format(nickname))
            self.nicknames.remove(nickname)
            self.broadcast_event('announcement', '%s has disconnected' % nickname)
            self.broadcast_event('nicknames', self.nicknames)
            self.disconnect(silent=True)

    def on_user_message(self, msg):
        msg = escape(msg)
        self.log(u'User message: {0}, in room: {1}, {2}'.format(msg, self.room, 'nickname' in self.socket.session))

        # room_name = self._get_room_name(self.room)
        # for sessid, socket in self.socket.server.sockets.iteritems():
        #     if 'rooms' not in socket.session:
        #         continue
        #     if room_name in socket.session['rooms'] and self.socket != socket and 'nickname' in socket.session:
        #        self.log(u'--- {0}'.format(socket.session['nickname']))

        if 'nickname' in self.socket.session:
            self.emit_to_room(self.room, 'msg_to_room', self.socket.session['nickname'], msg)

    # todo: add:
    # if not hasattr(self,room):
    #         return
    # each time self.room is used
    # --- Tools --- #

    # def on_begin(self, user, event, tool, data):
    #     self.emit_to_room(self.room, 'begin', user, event, tool, data)

    # def on_update(self, user, event, tool):
    #     self.emit_to_room(self.room, 'update', user, event, tool)

    # def on_end(self, user, event, tool):
    #     self.emit_to_room(self.room, 'end', user, event, tool)

    # # --- update --- #

    # def on_select_begin(self, user, pk, event):
    #     self.emit_to_room(self.room, 'beginSelect', user, pk, event)

    # def on_select_update(self, user, pk, event):
    #     self.emit_to_room(self.room, 'updateSelect', user, pk, event)

    # def on_select_end(self, user, pk, event):
    #     self.emit_to_room(self.room, 'endSelect', user, pk, event)

    # def  on_double_click(self, user, pk, event):
    #     self.emit_to_room(self.room, 'doubleClick', user, pk, event)

    # def on_parameter_change(self, user, pk, name, value, type=None):
    #     print "parameter change"
    #     self.emit_to_room(self.room, 'parameterChange', user, pk, name, value, type)

    # --- Save and load --- #
    # todo: change user to something like socket.sessionid

    # def on_setPathPK(self, user, pid, pk):
    #     self.emit_to_room(self.room, 'setPathPK', user, pid, pk)

    # def on_delete_path(self, pk):
    #     self.emit_to_room(self.room, 'deletePath', pk)

    # def on_createDiv(self, data):
    #     self.log(u'{0} create div')
    #     self.emit_to_room(self.room, 'createDiv', data)

    # def on_delete_div(self, pk):
    #     self.emit_to_room(self.room, 'deleteDiv', pk)

    def on_car_move(self, user, position, rotation, speed):
        if not hasattr(self, 'room'):
            return
        self.log(u'Car move: {0}, {1}'.format(position['x'], position['y']))
        self.emit_to_room(self.room, 'car move', user, position, rotation, speed)

    # --- Bounce --- #

    def on_bounce(self, data):
        print "bounce: " + str(data)
        # self.emit_to_room(self.room, 'bounce', data)

    def on_drawing_change(self, data):
        print "drawing change: " + str(data)
        self.emit_to_room(self.room, 'drawing change', data)

    def on_draw_begin(self, user, point):
        self.emit_to_room(self.room, 'draw begin', user, point)
    
    def on_draw_update(self, user, point):
        self.emit_to_room(self.room, 'draw update', user, point)

    def on_draw_end(self, user, point):
        self.emit_to_room(self.room, 'draw end', user, point)

    # def on_beginDiv(self, user, p):
    #     self.log(u'{0} begin div: {1}'.format(user, p))
    #     self.emit_to_room(self.room, 'beginDiv', user, p)
    #     return True

    # def on_beginUpdateDiv(self, user, p):
    #     self.log(u'{0} update div: {1}'.format(user, p))
    #     self.emit_to_room(self.room, 'beginUpdateDiv', user, p)
    #     return True

    # def on_createDiv(self, data):
    #     self.log(u'{0} create div')
    #     self.emit_to_room(self.room, 'createDiv', data)

    # def on_updateDiv(self, user, pk, tl, br, name, message, url, fillColor, strokeColor, strokeWidth):
    #     self.log(u'{0} update div {1}'.format(user, pk))
    #     self.emit_to_room(self.room, 'updateDiv', user, pk, tl, br, name, message, url, fillColor, strokeColor, strokeWidth)

    # def on_deleteDiv(self, pk):
    #     self.log(u'Delete div: {0}'.format(pk))
    #     self.emit_to_room(self.room, 'deleteDiv', pk)


    # def on_updatePath(self, user, pk, points, planet, data):
    #     self.log(u'{0} update path: {1} - {2}'.format(user, pk, points))

    #     self.emit_to_room(self.room, 'updatePath', user, pk, points, fillColor, strokeColor, strokeWidth)
    #     return True



    # def makeBox(tlX, tlY, brX, brY):
    #     return { "type": "Polygon", "coordinates": [ [ [tlX, tlY], [brX, tlY], [brX, brY], [tlX, brY], [tlX, tlY] ] ] }

    # def validateURL(url=""):
    #     if url != "":
    #         try:
    #             self.validate(url)
    #         except ValidationError, e:
    #             print e
    #             return False, {'state': 'error', 'message': 'invalid_url'}
    #     else:
    #         return False, {'state': 'system_error', 'message': 'invalid_data'}
    #     return True, None

    # def on_load(self, user, areasToLoad):

    #     paths = []
    #     divs = []
    #     boxes = []

    #     for area in areasToLoad:

    #         tlX = area['pos']['x']
    #         tlY = area['pos']['y']

    #         planetX = area['planet']['x']
    #         planetY = area['planet']['y']

    #         p = Path.objects(planetX=planetX, planetY=planetY, points__geo_intersects=makeBox(tlX, tlY, tlX+1, tlY+1) )
    #         b = Box.objects(planetX=planetX, planetY=planetY, box__geo_intersects=makeBox(tlX, tlY, tlX+1, tlY+1) )
    #         d = Div.objects(planetX=planetX, planetY=planetY, box__geo_intersects=makeBox(tlX, tlY, tlX+1, tlY+1) )

    #         paths.append(p.to_json())
    #         boxes.append(b.to_json())
    #         divs.append(d.to_json())

    #     user = user
    #     if not user:
    #         user = self.socket.sessid
    #     return { 'paths': paths, 'boxes': boxes, 'divs': divs, 'user': user }

    # def on_save_path(self, user, points, planet, object_type, data):
    #     planetX = planet['x']
    #     planetY = planet['y']

    #     lockedAreas = Box.objects(planetX=planetX, planetY=planetY, box__geo_intersects={"type": "LineString", "coordinates": points } )

    #     if lockedAreas.count()>0:
    #         return {'state': 'error', 'message': 'Your drawing intersects with a locked area'}

    #     p = Path(planetX=planetX, planetY=planetY, points=points, owner=user, object_type=object_type, data=data )
    #     p.save()

    #     return {'state': 'success', 'pID': pID, 'pk': str(p.pk)}

    # def on_update_path(self, user, pk, points=None, planet=None, data=None):

    #     try:
    #         p = Path.objects.get(pk=pk)
    #     except Path.DoesNotExist:
    #         return {'state': 'error', 'message': 'Element does not exist for this user'}

    #     if p.locked and user != p.owner:
    #         return json.dumps({'state': 'error', 'message': 'Not owner of path'})

    #     if points:
    #         p.points = points
    #     if planet:
    #         p.planetX = planet['x']
    #         p.planetY = planet['y']
    #     if data:
    #         p.data = data

    #     p.save()

    #     return {'state': 'success'}

    # def on_delete_path(self, user, pk):

    #     p = Path.objects.get(pk=pk)

    #     if not p:
    #         return json.dumps({'state': 'error', 'message': 'Element does not exist for this user'})

    #     if p.locked and user != p.owner:
    #         return json.dumps({'state': 'error', 'message': 'Not owner of path'})

    #     p.delete()

    #     return { 'state': 'success', 'pk': pk }

    # def on_save_box(request, box, object_type, message, name="", url=""):
    #     if not request.user.is_authenticated():
    #         return json.dumps({'state': 'not_logged_in'})

    #     if object_type=='link':
    #         valid, errorMessage = validateURL(url)
    #         if not valid:
    #             return errorMessage

    #     points = box['points']
    #     planetX = box['planet']['x']
    #     planetY = box['planet']['y']

    #     geometry = makeBox(points[0][0], points[0][1], points[2][0], points[2][1])
    #     lockedAreas = Box.objects(planetX=planetX, planetY=planetY, box__geo_intersects=geometry )
    #     if lockedAreas.count()>0:
    #         return json.dumps( {'state': 'error', 'message': 'This area was already locked'} )

    #     b = Box(planetX=planetX, planetY=planetY, box=[points], owner=request.user.username, object_type=object_type, url=url, message=message, name=name)
    #     b.save()

    #     # pathsToLock = Path.objects(planetX=planetX, planetY=planetY, box__geo_within=geometry)
    #     # for path in pathsToLock:
    #     #   path.locked = True
    #     #   path.save()

    #     Path.objects(planetX=planetX, planetY=planetY, points__geo_within=geometry).update(set__locked=True)
    #     Div.objects(planetX=planetX, planetY=planetY, box__geo_within=geometry).update(set__locked=True)

    #     return json.dumps( {'state': 'success', 'object_type':object_type, 'message': message, 'name': name, 'url': url, 'owner': request.user.username, 'pk':str(b.pk), 'box':box } )

