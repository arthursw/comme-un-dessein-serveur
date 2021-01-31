# -*- coding: utf-8 -*-

from binascii import a2b_base64
from threading import Timer, Thread
import datetime
import logging
import os
import shutil
import os.path
import errno
import json
import urllib
import urllib2

# from django.utils import json
# from dajaxice.decorators import dajaxice_register
from django.core import serializers
# from dajaxice.core import dajaxice_functions
from django.contrib.auth.models import User
from django.contrib.sites import shortcuts
from django.db.models import F
from django.core.mail import send_mail
from models import *
import ast
from pprint import pprint
from django.contrib.auth import authenticate, login, logout
from paypal.standard.ipn.signals import payment_was_successful, payment_was_flagged, payment_was_refunded, payment_was_reversed
from math import *
import random
import re
from django.core.validators import URLValidator
from django.core.exceptions import ValidationError
import django.dispatch

from mongoengine import ValidationError
from mongoengine.queryset import Q
import time

from PIL import Image, ImageFilter
import colorsys
import cStringIO
import StringIO
import traceback
import requests
from Wetu import settings
from allauth.socialaccount.models import SocialToken
# import collaboration

from allauth.account.signals import email_confirmed, email_confirmation_sent

import base64
import subprocess
import numpy as np

# from github3 import authorize

# from wand.image import Image

import functools

debugMode = False
simulateSlowResponsesMode = False
# positiveVoteThreshold = 10
# negativeVoteThreshold = 3
# positiveVoteThresholdTile = 5
# negativeVoteThresholdTile = 3
# voteValidationDelay = datetime.timedelta(minutes=1) 		# once the drawing gets positiveVoteThreshold votes, the duration before the drawing gets validated (the drawing is not immediately validated in case the user wants to cancel its vote)
# voteMinDuration = datetime.timedelta(hours=1)				# the minimum duration the vote will last (to make sure a good moderation happens)
drawingMaxSize = 1000

drawingModes = ['free', 'ortho', 'orthoDiag', 'pixel', 'image']

# drawingValidated = django.dispatch.Signal(providing_args=["clientId", "status"])
drawingChanged = django.dispatch.Signal(providing_args=["clientId", "status", "type", "city", "votes", "pk", "title", "description", "svg", "itemType", "photoURL"])


def sendEmails():
	friday = datetime.datetime.today().weekday() == 4
	firstOfMonth = datetime.datetime.today().day == 1
	users = UserProfile.objects.all().only('username', 'emailFrequency', 'emailNotifications')
	for user in users:
		try:
			owner = User.objects.get(username=user.username)
		except User.DoesNotExist:
			print("Owner not found")
		if user.disableEmail:
			continue
		if user.emailFrequency == 'daily' or user.emailFrequency == 'weekly' and friday or user.emailFrequency == 'monthly' and firstOfMonth:
			
			if len(user.emailNotifications) > 0:
				applicationName = 'Comme un dessein' if settings.APPLICATION == 'COMME_UN_DESSEIN' else 'Espero'
				message = 'Bonjour, \n\nVoici les dernières notifications de ' + applicationName + ' :\n\n'
				message += '<ul>\n'
				for emailNotification in user.emailNotifications:
					message += '<li>' + emailNotification + '</li>\n'

				message += '</ul>\n\n'
				siteDomain = shortcuts.get_current_site(request).domain
				message += 'Merci d\'avoir participé à Comme un Dessein,\n\n'
				message += 'Pour ne plus recevoir de notifications, allez sur ' + siteDomain + '/email/desactivation/\n\n'
				message += 'Le collectif Indien dans la ville\n'
				message += 'http://idlv.co/\n'
				message += 'idlv.contact@gmail.com'

				title = applicationName + ' - ' + 'Notifications'
				fromMail = 'contact@commeundessein.co'
				send_mail(title, message, fromMail, [owner.email], fail_silently=True)

				user.emailNotifications = []
				user.save()

	sendEmailsTimer = Timer(datetime.timedelta(days=1).total_seconds(), sendEmails)
	sendEmailsTimer.start()
	return

sendEmailsTimer = Timer(datetime.timedelta(days=1).total_seconds(), sendEmails)
sendEmailsTimer.start()

def queueEmail(user, message):
	user.emailNotifications.append(message)
	user.save()
	return

def userAllowed(request, owner):
	return request.user.username == owner or isAdmin(request.user)

if settings.DEBUG:
	import pdb

	def checkDebug(func):
		@functools.wraps(func)
		def wrapper(*args, **kwargs):
			if debugMode:
				import pdb; pdb.Pdb(skip=['django.*', 'gevent.*']).set_trace()
			return func(*args, **kwargs)
		return wrapper

	def checkSimulateSlowResponse(func):
		@functools.wraps(func)
		def wrapper(*args, **kwargs):
			if simulateSlowResponsesMode:
				time.sleep(2)
			return func(*args, **kwargs)
		return wrapper
else:
	def checkDebug(func):
	    return func
	def checkSimulateSlowResponse(func):
	    return func

def isAdmin(user):
	try:
		profile = UserProfile.objects.get(username=user.username)
		return profile.admin
	except UserProfile.DoesNotExist:
		return False
	return False

logger = logging.getLogger(__name__)

try:
	commeUnDesseinCity = City.objects.get(name='Wetu', owner='WetuOrg', public=True)
except City.DoesNotExist:
	commeUnDesseinCity = City(name='Wetu', owner='WetuOrg', public=True)
	commeUnDesseinCity.save()


logger = logging.getLogger(__name__)

with open(settings.DATA_DIR + '/wetu/secret_github.txt') as f:
	PASSWORD = base64.b64decode(f.read().strip())

with open(settings.DATA_DIR + '/wetu/secret_tipibot.txt') as f:
	TIPIBOT_PASSWORD = f.read().strip()

with open(settings.DATA_DIR + '/wetu/client_secret_github.txt') as f:
	CLIENT_SECRET = f.read().strip()

with open(settings.DATA_DIR + '/wetu/accesstoken_github.txt') as f:
	ACCESS_TOKEN = f.read().strip()

with open(settings.DATA_DIR + '/wetu/openaccesstoken_github.txt') as f:
	OPEN_ACCESS_TOKEN = f.read().strip()

with open(settings.DATA_DIR + '/wetu/settings.json') as f:
    localSettings = json.loads(f.read().strip())

# pprint(vars(object))
# import pdb; pdb.set_trace()
# import pudb; pu.db

import datetime

def unix_time(dt):
	epoch = datetime.datetime.utcfromtimestamp(0)
	delta = dt - epoch
	return delta.total_seconds()

def unix_time_millis(dt):
	return unix_time(dt) * 1000.0

planetWidth = 180
planetHeight = 90

def projectToGeoJSON(city, bounds):
	x = planetWidth * bounds['x'] / float(city.width)
	y = planetHeight * bounds['y'] / float(city.height)
	width = planetWidth * bounds['width'] / float(city.width)
	height = planetHeight * bounds['height'] / float(city.height)
	x = min(max(x, -planetWidth/2), planetWidth/2)
	y = min(max(y, -planetHeight/2), planetHeight/2)
	if x + width > planetWidth/2:
		width = planetWidth/2 - x
	if y + height > planetHeight/2:
		height = planetHeight/2 - y
	return { 'x': x, 'y': y, 'width': width, 'height': height }

def geoJSONToProject(city, bounds):
	x = float(city.width) * bounds['x'] / planetWidth
	y = float(city.height) * bounds['y'] / planetHeight
	width = float(city.width) * bounds['width'] / planetWidth
	height = float(city.height) * bounds['height'] / planetHeight
	return { 'x': x, 'y': y, 'width': width, 'height': height }

def makeBox(left, top, right, bottom):
	return { "type": "Polygon", "coordinates": [ [ [left, top], [right, top], [right, bottom], [left, bottom], [left, top] ] ] }

def makeBoxCCW(left, top, right, bottom):
	return { "type": "Polygon", "coordinates": [ [ [left, bottom], [right, bottom], [right, top], [left, top], [left, bottom] ] ] }

def makeBoxFromBounds(city, bounds):
	bounds = projectToGeoJSON(city, bounds)
	return makeBox(bounds['x'], bounds['y'], bounds['x'] + bounds['width'], bounds['y'] + bounds['height'])

def makeBoxCCWFromBounds(city, bounds):
	bounds = projectToGeoJSON(city, bounds)
	return makeBoxCCW(bounds['x'], bounds['y'], bounds['x'] + bounds['width'], bounds['y'] + bounds['height'])

def makeTLBRFromBounds(city, bounds):
	bounds = projectToGeoJSON(city, bounds)
	return [(bounds['x'], bounds['y']), (bounds['x'] + bounds['width'], bounds['y'] + bounds['height'])]

# def makeBLTRFromBounds(city, bounds):
# 	bounds = projectToGeoJSON(city, bounds)
# 	return [(bounds['x'], bounds['y'] + bounds['height']), (bounds['x'] + bounds['width'], bounds['y'])]

def makeBoundsFromBox(city, box):
	left = box['coordinates'][0][0][0]
	top = box['coordinates'][0][0][1]
	right = box['coordinates'][0][1][0]
	bottom = box['coordinates'][0][2][1]
	return geoJSONToProject(city, { 'x': left, 'y': top, 'width': right - left, 'height': bottom - top })

def makeBoxFromPoints(box):
	if box is None:
		return None
	
	points = box['points']
	planetX = box['planet']['x']
	planetY = box['planet']['y']

	return makeBox(points[0][0], points[0][1], points[2][0], points[2][1])

userID = 0
isUpdatingRasters = False
# dummyArea = None
# defaultPathTools = ["Checkpoint", "EllipseShape", "FaceShape", "GeometricLines", "GridPath", "Meander", "PrecisePath", "RectangleShape", "ShapePath", "SpiralShape", "StarShape", "ThicknessPath"]
defaultPathTools = ["Precise path", "Thickness path", "Meander", "Grid path", "Geometric lines", "Shape path", "Rectangle", "Ellipse", "Star", "Spiral", "Face generator", "Checkpoint"]

# @dajaxice_register
def setDebugMode(request, debug):
	if not isAdmin(request.user):
		return json.dumps({"status": "error", "message": "not_admin"})
	global debugMode
	debugMode = debug
	return json.dumps({"message": "success"})

def setSimulateSlowResponsesMode(request, simulateSlowResponses):
	if not isAdmin(request.user):
		return json.dumps({"status": "error", "message": "not_admin"})
	global simulateSlowResponsesMode
	simulateSlowResponsesMode = simulateSlowResponses
	return json.dumps({"message": "success"})


def setDrawingMode(request, mode):
	if not isAdmin(request.user):
		return json.dumps({"status": "error", "message": "not_admin"})
	global drawingMode
	drawingMode = mode
	return json.dumps({"message": "success"})

def getPositiveVoteThreshold(city):
	return city.positiveVoteThreshold if city else 10

def getNegativeVoteThreshold(city):
	return city.negativeVoteThreshold if city else 3

def getVoteMinDuration(city):
	return datetime.timedelta(seconds=city.voteMinDuration) if city else datetime.timedelta(minutes=60)

def setVoteThresholds(request, cityName, positiveVoteThreshold=10, negativeVoteThreshold=3, positiveVoteThresholdTile=5, negativeVoteThresholdTile=3):
	if not isAdmin(request.user):
		return json.dumps({"status": "error", "message": "not_admin"})
	
	city = getCity(cityName)
	if not city:
		return json.dumps( { 'state': 'error', 'message': 'The city does not exist', 'code': 'CITY_DOES_NOT_EXIST' } )

	city.positiveVoteThreshold = positiveVoteThreshold
	city.negativeVoteThreshold = negativeVoteThreshold
	city.positiveVoteThresholdTile = positiveVoteThresholdTile
	city.negativeVoteThresholdTile = negativeVoteThresholdTile

	city.save()
	return json.dumps({"message": "success"})

def recomputeDrawingStates(request):
	drawings = Drawing.objects.get(status__in=['pending', 'drawing', 'validated', 'rejected'])
	
	for drawing in drawings:
		# send_mail('[Comme un dessein] recomputeDrawingStates', u'recomputeDrawingStates: updateDrawingState ' + str(drawing.pk), 'contact@commeundessein.co', ['idlv.contact@gmail.com'], fail_silently=True)
		updateDrawingState(drawing.pk, drawing)

	return json.dumps({"message": "success"})

def setVoteValidationDelay(request, cityName, hours, minutes, seconds):
	if not isAdmin(request.user):
		return json.dumps({"status": "error", "message": "not_admin"})
	
	city = getCity(cityName)
	if not city:
		return json.dumps( { 'state': 'error', 'message': 'The city does not exist', 'code': 'CITY_DOES_NOT_EXIST' } )

	city.voteValidationDelay = datetime.timedelta(hours=hours, minutes=minutes, seconds=seconds).total_seconds()
	city.save()
	return json.dumps({"message": "success"})

def setVoteMinDuration(request, cityName, hours, minutes, seconds):
	if not isAdmin(request.user):
		return json.dumps({"status": "error", "message": "not_admin"})

	city = getCity(cityName)
	if not city:
		return json.dumps( { 'state': 'error', 'message': 'The city does not exist', 'code': 'CITY_DOES_NOT_EXIST' } )

	city.voteMinDuration = datetime.timedelta(hours=hours, minutes=minutes, seconds=seconds).total_seconds()
	city.save()
	return json.dumps({"message": "success"})

def setCityNextEventDateAndLocation(request, cityName, date, location):
	if not isAdmin(request.user):
		return json.dumps({"status": "error", "message": "not_admin"})

	city = getCity(cityName)
	if not city:
		return json.dumps( { 'state': 'error', 'message': 'The city does not exist', 'code': 'CITY_DOES_NOT_EXIST' } )

	city.eventDate = datetime.datetime.fromtimestamp(date/1000.0)
	city.eventLocation = location
	city.save()
	return json.dumps({"message": "success"})

def setCityDimensions(request, cityName, width, height, strokeWidth):
	if not isAdmin(request.user):
		return json.dumps({"status": "error", "message": "not_admin"})

	city = getCity(cityName)
	if not city:
		return json.dumps( { 'state': 'error', 'message': 'The city does not exist', 'code': 'CITY_DOES_NOT_EXIST' } )

	city.width = width
	city.height = height
	city.strokeWidth = strokeWidth
	city.save()
	return json.dumps({"message": "success"})

@checkDebug
def changeUser(request, username):
	
	if not request.user.is_authenticated():
		return json.dumps({'state': 'not_logged_in'})

	try:
		userProfile = UserProfile.objects.get(username=request.user.username)
	except UserProfile.DoesNotExist:
		return json.dumps({"status": "error", "message": "The user does not exists."})

	if userProfile.banned:
		return json.dumps({'state': 'error', 'message': 'Your account has been suspended'})

	if username != request.user.username: 			# if change username: check that it does not already exist
		try:
			existingUser = UserProfile.objects.get(username=username)
			return json.dumps( { 'state': 'error', 'message': 'This username is already being used' } )
		except UserProfile.DoesNotExist:
			pass

	# Changing email does not work 
	# What happens if email is linked to social account?

	# if request.user.email != email:
	# 	emailAddress = EmailAddress.objects.get(user=request.user)

	# 	try:
	# 		existingEmailAddress = EmailAddress.objects.get(email=email)
	# 		return json.dumps( { 'state': 'error', 'message': 'This email address is already in use' } )
	# 	except EmailAddress.DoesNotExist:
	# 		pass

	# 	try:
	# 		emailAddress.email = email
	# 		emailAddress.save()
	# 	except NotUniqueError:
	# 		return json.dumps( { 'state': 'error', 'message': 'This email address is already in use' } )
	# 	except:
	# 		return json.dumps( { 'state': 'error', 'message': 'This email address is not valid' } )

	oldUsername = request.user.username

	if len(username) <= 0:
		return json.dumps( { 'state': 'error', 'message': 'This username is not valid' } )

	try:
		request.user.username = username
		request.user.save()
		userProfile.username = username
		userProfile.save()
	except NotUniqueError:
		return json.dumps( { 'state': 'error', 'message': 'This username is already being used' } )
	except:
		return json.dumps( { 'state': 'error', 'message': 'This username is not valid' } )

	Drawing.objects(owner=oldUsername).update(owner=username)
	Tile.objects(owner=oldUsername).update(owner=username)

	return  json.dumps({'state': 'success', 'username': username})

@checkDebug
def changeUserEmailFrequency(request, emailFrequency):
	
	if not request.user.is_authenticated():
		return json.dumps({'state': 'not_logged_in'})

	try:
		userProfile = UserProfile.objects.get(username=request.user.username)
	except UserProfile.DoesNotExist:
		return json.dumps({"status": "error", "message": "The user does not exists."})

	userProfile.emailFrequency = emailFrequency
	userProfile.save()

	return  json.dumps({'state': 'success'})

@checkDebug
def deleteUser(request):

	if not request.user.is_authenticated():
		return json.dumps({'state': 'not_logged_in'})

	try:
		userProfile = UserProfile.objects.get(username=request.user.username)
	except UserProfile.DoesNotExist:
		return json.dumps({"status": "error", "message": "The user does not exists."})

	anonymous_name = 'anonymous_' + str(random.random())

	Drawing.objects(owner=request.user.username).update(owner=anonymous_name)
	Tile.objects(owner=request.user.username).delete()

	for vote in userProfile.votes[:]:
		if isinstance(vote, Vote):
			if vote.drawing and vote in vote.drawing.votes:
				vote.drawing.votes.remove(vote)
				vote.drawing.save()
			if vote.tile and vote in vote.tile.votes:
				vote.tile.votes.remove(vote)
				vote.tile.save()
			vote.delete()

	for comment in userProfile.comments[:]:
		if isinstance(comment, Comment):
			if comment.drawing and comment in comment.drawing.comments:
				comment.drawing.comments.remove(comment)
				comment.drawing.save()
			if comment.tile and comment in comment.tile.comments:
				comment.tile.comments.remove(comment)
				comment.tile.save()
			comment.delete()

	userProfile.delete()
	request.user.delete()

	return  json.dumps({'state': 'success'})

@checkDebug
def deleteUserDrawings(request, username):

	if not isAdmin(request.user):
		return json.dumps({"status": "error", "message": "not_admin"})

	if not request.user.is_authenticated():
		return json.dumps({'state': 'not_logged_in'})

	try:
		userProfile = UserProfile.objects.get(username=request.user.username)
	except UserProfile.DoesNotExist:
		return json.dumps({"status": "error", "message": "The user does not exists."})

	drawings = Drawing.objects(owner=username)
	
	for drawing in drawings:
		layerName = 'inactive' if drawing.status == 'rejected' else 'active'
		removeDrawingFromRasters(city, drawing, layerName)

	drawings.delete()

	return  json.dumps({'state': 'success'})

# allauth.account.signals.email_confirmed(request, email_address)
@receiver(email_confirmed)
@checkDebug
def on_email_confirmed(sender, email_address, request, **kwargs):
	# if kwargs is None or 'email_address' not in kwargs:
	# 	print("Error: no email_address in on_email_confirmed")
	# 	return

	# request = kwargs['request']
	# email_address = kwargs['email_address']
	
	print("on_email_confirmed")

	user = email_address.user
	
	try:
		userProfile = UserProfile.objects.get(username=user.username)
	except UserProfile.DoesNotExist:
		print("Error: the user profile who confirmed his email is not found")
		return

	try: 
		emailAddress = EmailAddress.objects.get(user=user)
		if not emailAddress.verified:
			emailAddress.verified = True
			emailAddress.save()
	except EmailAddress.DoesNotExist:
		print("Error: the email address which was confirmed his email is not found")
		return

	userProfile.emailConfirmed = True
	userProfile.save()

	drawings = Drawing.objects(owner=user.username, status='emailNotConfirmed')
	drawings.update(status='pending')
	Vote.objects(author=userProfile).update(emailConfirmed=True)
	Comment.objects(author=userProfile).update(emailConfirmed=True)

	for vote in userProfile.votes:
		if isinstance(vote, Vote):
			try:
				# send_mail('[Comme un dessein] on_email_confirmed', u'on_email_confirmed pending ' + str(drawing.pk), 'contact@commeundessein.co', ['idlv.contact@gmail.com'], fail_silently=True)
				updateDrawingState(vote.drawing.pk, vote.drawing)
			except DoesNotExist:
				pass

	for drawing in drawings:
		cityName = 'Wetu'
		try:
			city = City.objects.get(pk=drawing.city)
			cityName = city.name
		except City.DoesNotExist:
			print('The city does not exist')
		drawingChanged.send(sender=None, type='new', clientId=drawing.clientId, pk=str(drawing.pk), svg=drawing.svg, city=cityName, itemType='drawing', bounds=makeBoundsFromBox(city, drawing.box))

	return

#allauth.account.signals.email_confirmation_sent(request, confirmation, signup)
@receiver(email_confirmation_sent)
def on_email_confirmation_sent(sender, request, confirmation, signup, **kwargs):
	send_mail('[Comme un dessein] New email confirmation sent', u'A new email confirmation was sent to ' + str(confirmation.email_address) + ', to confirm his email manually follow the link: https://commeundessein.co/accounts/confirm-email/' + confirmation.key , 'contact@commeundessein.co', ['idlv.contact@gmail.com'], fail_silently=True)
	return

@checkSimulateSlowResponse
@checkDebug
def isEmailKnown(request, email):
	if len(email) <= 0:
		return json.dumps({ 'error': 'The email address is empty.' })

	emailIsKnown = True
	emailShortNameIsKnown = True
	usernameIsKnown = True
	try:
		user = User.objects.get(email=email)
	except User.DoesNotExist:
		emailIsKnown = False
		emailShortName = email[:email.find('@')]
		try:
			user = User.objects.get(username=emailShortName)
		except User.DoesNotExist:
			emailShortNameIsKnown = False
	try:
		user = User.objects.get(username=email)
	except User.DoesNotExist:
		usernameIsKnown = False
	return json.dumps({ 'emailIsKnown': emailIsKnown, 'usernameIsKnown': usernameIsKnown, 'emailShortNameIsKnown': emailShortNameIsKnown })

@checkSimulateSlowResponse
@checkDebug
def isUsernameKnown(request, username):
	try:
		user = User.objects.get(username=username)
	except User.DoesNotExist:
		return json.dumps({'usernameIsKnown': False})
	return json.dumps({'usernameIsKnown': True})

# @dajaxice_register
@checkSimulateSlowResponse
@checkDebug
def multipleCalls(request, functionsAndArguments):
	results = []
	for fa in functionsAndArguments:
		results.append(json.loads(globals()[fa['function']](request=request, **fa['arguments'])))
	return json.dumps(results)


## debug
@checkSimulateSlowResponse
@checkDebug
def debugDatabase(request):
	models = ['Path', 'Div', 'Box', 'Drawing']

	# for model in models:
	# 	objects = globals()[model].objects()
	# 	for obj in objects:
	# 		obj.clientId = obj.clientID
	# 		obj.save()
	return


# @checkDebug
# def deleteItems(request, itemsToDelete, confirm):
# 	if not isAdmin(request.user):
# 		return json.dumps( {'state': 'error', 'message': 'not admin' } )

# 	if confirm != 'confirm':
# 		return json.dumps( {'state': 'error', 'message': 'please confirm' } )
	
# 	for itemToDelete in itemsToDelete:
# 		itemType = itemToDelete['itemType']
# 		pks = itemToDelete['pks']
		
# 		if itemType not in ['Path', 'Div', 'Box', 'AreaToUpdate', 'Drawing']:
# 			return json.dumps({'state': 'error', 'message': 'Can only delete Paths, Divs, Boxs, AreaToUpdates or Drawings.'})

# 		itemsQuerySet = globals()[itemType].objects(pk__in=pks)
	
# 		itemsQuerySet.delete()

# 	return json.dumps( {'state': 'success', 'message': 'items successfully deleted' } )

# @checkDebug
# def deleteAllItems(request, confirm):
# 	if not isAdmin(request.user):
# 		return json.dumps( {'state': 'error', 'message': 'not admin' } )

# 	if confirm != 'confirm':
# 		return json.dumps( {'state': 'error', 'message': 'please confirm' } )

# 	for itemType in ['Path', 'Div', 'Box', 'AreaToUpdate', 'Drawing']:
		
# 		itemsQuerySet = globals()[itemType].objects()
	
# 		itemsQuerySet.delete()

# 	return json.dumps( {'state': 'success', 'message': 'items successfully deleted' } )

# @dajaxice_register
@checkDebug
def githubRequest(request, githubRequest, method='get', data=None, params=None, headers=None):
	token = ACCESS_TOKEN

	try:
		socialAccount = SocialAccount.objects.get(user_id=request.user.id, provider='github')
		userToken = SocialToken.objects.get(account_id=socialAccount.id, account__provider='github')
		if userToken:
			token = userToken
	except:
		pass
	if data:
		data = json.dumps(data)
	if not headers:
		headers = {}
	headers['Authorization'] = 'token ' + str(token)
	r = getattr(requests, method)(githubRequest, data=data, params=params, headers=headers)
	response = { 'content': r.json(), 'status': r.status_code }
	if 'link' in r.headers:
		response['headers'] = { 'link': r.headers['link'] }
	return json.dumps(response)

# r = requests.post(githubRequest, headers={'Authorization': 'token ' + ACCESS_TOKEN})

# @dajaxice_register
@checkDebug
def getGithubAuthToken(request):
	client_id = None
	try:
		socialAccount = SocialAccount.objects.get(user_id=request.user.id, provider='github')
		token = SocialToken.objects.get(account__user=socialAccount.id, account__provider='github')
		r = requests.put('https://api.github.com/authorizations/clients/'+str(client_id), params={'client_secret': CLIENT_SECRET})
	except:
		return json.dumps({"state": "error", "message": "success"})
	return



# @dajaxice_register
@checkDebug
def createCity(request, name, public=None):
	
	if not isAdmin(request.user):
		return json.dumps({"status": "error", "message": "not_admin"})

	try:
		city = City.objects.get(name=name, owner=request.user.username)
		return json.dumps( { 'state': 'error', 'message': 'The city named ' + name + ' already exists.' } )
	except Exception:
		pass

	city = City(name=name, owner=request.user.username, public=public)
	city.save()

	return json.dumps( { 'state': 'succes', 'city': city.to_json() } )

# @dajaxice_register
@checkDebug
def deleteCity(request, name):
	if not isAdmin(request.user):
		return json.dumps({"status": "error", "message": "not_admin"})
	try:
		city = City.objects.get(name=name, owner=request.user.username)
	except City.DoesNotExist:
		return json.dumps( { 'state': 'error', 'message': 'The city ' + name + ' for user ' + request.user.username + ' does not exist.' } )

	city.delete()

	models = ['Path', 'Div', 'Box', 'AreaToUpdate']

	for model in models:
		globals()[model].objects(city=city.pk).delete()

	try:
		shutil.rmtree('media/rasters/' + str(city.name))
	except Exception:
		pass

	return json.dumps( { 'state': 'succes', 'cityPk': str(city.pk) } )

# @dajaxice_register
@checkDebug
def updateCity(request, pk, name, public=None):
	if not isAdmin(request.user):
		return json.dumps({"status": "error", "message": "not_admin"})
	try:
		city = City.objects.get(name=name, owner=request.user.username)
		return json.dumps( { 'state': 'error', 'message': 'The city named ' + name + ' already exists.' } )
	except Exception:
		pass

	try:
		city = City.objects.get(pk=pk, owner=request.user.username)
		city.name = name
		if public:
			city.public = public
		city.save()
	except City.DoesNotExist:
		return json.dumps( { 'state': 'error', 'message': 'The city with id ' + pk + ' for user ' + request.user.username + ' does not exist.' } )

	return json.dumps( { 'state': 'succes', 'city': city.to_json() } )

# @dajaxice_register
@checkDebug
def loadCities(request):
	userCities = City.objects(owner=request.user.username)
	publicCities = City.objects(public=True)
	return json.dumps( { 'userCities': userCities.to_json(), 'publicCities': publicCities.to_json() } )

# @dajaxice_register
@checkDebug
def loadUserCities(request):
	userCities = City.objects(owner=request.user.username)
	return json.dumps( { 'userCities': userCities.to_json() } )

# @dajaxice_register
@checkDebug
def loadPublicCities(request):
	publicCities = City.objects(public=True)
	return json.dumps( { 'publicCities': publicCities.to_json() } )

# @dajaxice_register
@checkDebug
def loadCity(request, pk):
	try:
		city = City.objects.get(pk=pk, owner=request.user.username)
	except City.DoesNotExist:
		return json.dumps( { 'state': 'error', 'message': 'The city with id ' + pk + ' for user ' + request.user.username + ' does not exist.' } )
	return json.dumps( { 'state': 'succes', 'city': city.to_json() } )

def getCity(cityName=None):
	if not cityName:
		city = commeUnDesseinCity
	else:
		try:
			city = City.objects.get(name=cityName)
			if not city.public:
				return None
		except City.DoesNotExist:
			return None
	return city

# def checkAddItem(item, items, itemsDates=None, ignoreDrafts=False):
# 	if not item.pk in items:
# 		if ignoreDrafts:
# 			itemIsDraft = type(item) is Path and item.isDraft
# 			if not itemIsDraft:
# 				items[item.pk] = item.to_json()
# 		else:
# 			items[item.pk] = item.to_json()
# 	return

# def checkAddItemRasterizer(item, items, itemsDates, ignoreDrafts=False):
# 	pk = item.pk
# 	itemLastUpdate = unix_time_millis(item.lastUpdate)
# 	if not pk in items and (not pk in itemsDates or itemsDates[pk]<itemLastUpdate):
# 		items[pk] = item.to_json()
# 		if pk in itemsDates:
# 			del itemsDates[pk]
# 	return

# def getItems(models, areasToLoad, qZoom, city, checkAddItemFunction, itemDates=None, owner=None, loadDrafts=True):
# 	items = {}
# 	for area in areasToLoad:

# 		tlX = area['pos']['x']
# 		tlY = area['pos']['y']

# 		planetX = area['planet']['x']
# 		planetY = area['planet']['y']

# 		geometry = makeBox(tlX, tlY, tlX+qZoom, tlY+qZoom)

# 		for model in models:

# 			itemsQuerySet = globals()[model].objects(city=city, planetX=planetX, planetY=planetY, box__geo_intersects=geometry)

# 			for item in itemsQuerySet:
# 				checkAddItemFunction(item, items, itemDates, loadDrafts)

# 	if loadDrafts:
# 		# add drafts
# 		if owner is not None:
# 			drafts = Path.objects(city=city, isDraft=True, owner=owner)
# 			for draft in drafts:
# 				if not draft.pk in items:
# 					items[draft.pk] = draft.to_json()

# 	return items

# def getAllItems(models, city, checkAddItemFunction, itemDates=None, owner=None, loadDrafts=True):
# 	items = {}

# 	for model in models:
		
# 		if model == Path and loadDrafts:
# 			itemsQuerySet = globals()[model].objects(city=city, isDraft=False)
# 		else:
# 			itemsQuerySet = globals()[model].objects(city=city)

# 		for item in itemsQuerySet:
# 			if item.pk not in items:
# 				items[item.pk] = item.to_json()
# 		# checkAddItemFunction(item, items, itemDates, loadDrafts)

# 	if loadDrafts:
# 		# add drafts
# 		if owner is not None:
# 			drafts = Path.objects(city=city, isDraft=True, owner=owner)
# 			for draft in drafts:
# 				if not draft.pk in items:
# 					items[draft.pk] = draft.to_json()

# 	return items

@checkDebug
def loadAll(request, cityName=None):

	if not isAdmin(request.user):
		return json.dumps({"status": "error", "message": "not_admin"})

	drawings = Drawing.objects()

	items = []
	for drawing in drawings:
		items.append(drawing.to_json())

	return json.dumps( { 'items': items, 'user': request.user.username } )

@checkSimulateSlowResponse
@checkDebug
def loadDraft(request, cityName=None):

	city = getCity(cityName)

	if not city:
		return json.dumps( { 'state': 'error', 'message': 'The city does not exist', 'code': 'CITY_DOES_NOT_EXIST' } )

	cityPk = str(city.pk)

	try:
		userProfile = UserProfile.objects.get(username=request.user.username)
		if not userProfile.emailConfirmed:
			emailConfirmed = EmailAddress.objects.filter(user=request.user, verified=True).exists()
			userProfile.emailConfirmed = emailConfirmed
			userProfile.save()
	except UserProfile.DoesNotExist:
		print('User does not exist')

	items = []
	drafts = Drawing.objects(city=cityPk, status='draft', owner=request.user.username).only('status', 'pk', 'clientId', 'owner', 'pathList', 'title')
	
	# if we could not find a draft and authenticated : create one
	if request.user.is_authenticated() and len(drafts) == 0:
		try:
			clientId = '' + str(datetime.datetime.now()) + str(random.random())
			draft = Drawing(clientId=clientId, city=cityPk, planetX=0, planetY=0, owner=request.user.username, date=datetime.datetime.now(), status='draft')
			draft.save()
			drafts = [draft]
		except NotUniqueError:
			pass

	if len(drafts) > 0:
		items.append(drafts[0].to_json())

	if isAdmin(request.user):
		flaggedDrawings = Drawing.objects(city=cityPk, status='flagged_pending').only('status', 'pk', 'clientId', 'owner', 'title', 'box', 'pathList')
	
		for drawing in flaggedDrawings:
			items.append(drawing.to_json())

	# return json.dumps( { 'paths': paths, 'boxes': boxes, 'divs': divs, 'user': user, 'rasters': rasters, 'areasToUpdate': areas, 'zoom': zoom } )
	return json.dumps( { 'items': items, 'user': request.user.username } )

# @checkDebug
# def loadDrawingsFromBounds(request, xMin, yMin, xMax, yMax, city):

# 	start = time.time()

# 	(cityPk, cityFinished) = getCity(request, city)
# 	if not cityPk:
# 		return json.dumps( { 'state': 'error', 'message': 'The city does not exist', 'code': 'CITY_DOES_NOT_EXIST' } )

# 	statusToLoad = ['pending', 'drawing', 'drawn', 'rejected']

# 	if isAdmin(request.user):
# 		statusToLoad.append('emailNotConfirmed')
# 		statusToLoad.append('notConfirmed')
# 		statusToLoad.append('flagged')
# 		statusToLoad.append('test')

# 	# drawings = Drawing.objects(city=cityPk, left__in=range(xMin, xMax), top__in=range(yMin, yMax), status__in=statusToLoad).only('status', 'pk', 'clientId', 'title', 'owner', 'bounds', 'date')
# 	drawings = Drawing.objects(city=cityPk, left__gte=xMin, left__lt=xMax, top__gte=yMin, top__lt=yMax, status__in=statusToLoad).only('status', 'pk', 'clientId', 'title', 'owner', 'bounds', 'date')

# 	items = []
# 	for drawing in drawings:
# 		items.append(drawing.to_json())

# 	return json.dumps( { 'items': items, 'user': request.user.username } )

# @checkDebug
# def loadTilesFromBounds(request, xMin, yMin, xMax, yMax, city=None):

# 	(cityPk, cityFinished) = getCity(request, city)
# 	if not cityPk:
# 		return json.dumps( { 'state': 'error', 'message': 'The city does not exist', 'code': 'CITY_DOES_NOT_EXIST' } )

# 	# tiles = Tile.objects(city=cityPk, x__in=range(xMin, xMax), y__in=range(yMin, yMax))
# 	tiles = Tile.objects(city=cityPk, x__gte=xMin, x__lt=xMax, y__gte=yMin, y__lt=yMax).only('status', 'pk', 'x', 'y')

# 	return json.dumps( { 'tiles': tiles.to_json(), 'user': request.user.username } )

@checkSimulateSlowResponse
@checkDebug
def loadDrawingsAndTilesFromBounds(request, bounds, cityName=None, drawingsToIgnore=[], tilesToIgnore=[], discussionsToIgnore=[], rejected=False):

	city = getCity(cityName)
	
	if not city:
		return json.dumps( { 'state': 'error', 'message': 'The city does not exist', 'code': 'CITY_DOES_NOT_EXIST' } )

	cityPk = str(city.pk)

	statusToLoad = ['pending', 'drawing', 'validated', 'drawn']

	if isAdmin(request.user):
		statusToLoad.append('emailNotConfirmed')
		statusToLoad.append('notConfirmed')
		statusToLoad.append('test')

	if rejected:
		statusToLoad.append('rejected')

	if bounds['x'] >= city.width / 2 or bounds['y'] >= city.height / 2 or city.width <= 0 or city.height <= 0:
	 	return json.dumps( { 'tiles': [], 'items': [], 'user': request.user.username } )

	box = makeBoxFromBounds(city, bounds)
	# box = makeBoxCCWFromBounds(city, bounds)
	# box = makeTLBRFromBounds(city, bounds)

	drawings = None

	fields = ['status', 'pk', 'clientId', 'title', 'owner', 'date', 'box']
	drawings = Drawing.objects(city=cityPk, box__geo_intersects=box, status__in=statusToLoad, pk__nin=drawingsToIgnore).only(*fields)
	# drawings = Drawing.objects(city=cityPk, box__geo_within_polygon=box["coordinates"][0], status__in=statusToLoad, pk__nin=drawingsToIgnore).only(*fields)
	# drawings = Drawing.objects(city=cityPk, box__geo_within_box=box, status__in=statusToLoad, pk__nin=drawingsToIgnore).only(*fields)
	

	items = []
	for drawing in drawings:
		items.append(drawing.to_json())

	tiles = None

	fields = ['status', 'owner', 'pk', 'x', 'y', 'clientId', 'photoURL']
	tiles = Tile.objects(city=cityPk, box__geo_intersects=box, pk__nin=tilesToIgnore).only(*fields)
	# tiles = Tile.objects(city=cityPk, box__geo_within_polygon=box["coordinates"][0], pk__nin=tilesToIgnore).only(*fields)
	# tiles = Tile.objects(city=cityPk, box__geo_within_box=box, pk__nin=tilesToIgnore).only(*fields)

	discussions = None

	# fields = ['title', 'pk', 'box', 'clientId']
	discussions = Discussion.objects(city=cityPk, box__geo_intersects=box, pk__nin=discussionsToIgnore)

	return json.dumps( { 'tiles': tiles.to_json(), 'items': items, 'discussions': discussions.to_json(), 'user': request.user.username } )


# @checkDebug
# def loadBounds(request, city=None):

# 	start = time.time()

# 	(cityPk, cityFinished) = getCity(request, city)
# 	if not cityPk:
# 		return json.dumps( { 'state': 'error', 'message': 'The city does not exist', 'code': 'CITY_DOES_NOT_EXIST' } )

# 	try:
# 		userProfile = UserProfile.objects.get(username=request.user.username)
# 		if not userProfile.emailConfirmed:
# 			emailConfirmed = EmailAddress.objects.filter(user=request.user, verified=True).exists()
# 			userProfile.emailConfirmed = emailConfirmed
# 			userProfile.save()
# 	except UserProfile.DoesNotExist:
# 		print('User does not exist')


# 	statusToLoad = ['pending', 'drawing', 'drawn', 'rejected']

# 	if isAdmin(request.user):
# 		statusToLoad.append('emailNotConfirmed')
# 		statusToLoad.append('notConfirmed')
# 		statusToLoad.append('flagged')
# 		statusToLoad.append('test')

# 	# drawings = Drawing.objects(city=cityPk, status__in=statusToLoad).only('svg', 'status', 'pk', 'clientId', 'title', 'owner', 'bounds')
# 	drawings = Drawing.objects(city=cityPk, status__in=statusToLoad).only('status', 'pk', 'clientId', 'title', 'owner', 'bounds', 'date')

# 	items = []
# 	for drawing in drawings:
# 		items.append(drawing.to_json())

# 	# emailNotConfirmed and notConfirmed are out of date

# 	# draftsAndNotConfirmed = Drawing.objects(city=cityPk, status__in=['draft', 'emailNotConfirmed', 'notConfirmed'], owner=request.user.username).only('svg', 'status', 'pk', 'clientId', 'owner', 'pathList', 'title', 'date')
# 	drafts = Drawing.objects(city=cityPk, status='draft', owner=request.user.username).only('svg', 'status', 'pk', 'clientId', 'owner', 'pathList', 'title')
	
# 	# if we could not find a draft and authenticated : create one
# 	if request.user.is_authenticated() and len(drafts) == 0:
# 		try:
# 			clientId = '' + str(datetime.datetime.now()) + str(random.random())
# 			drawing = Drawing(clientId=clientId, city=cityPk, planetX=0, planetY=0, owner=request.user.username, date=datetime.datetime.now(), status='draft')
# 			drawing.save()
# 			drafts = [drawing]
# 		except NotUniqueError:
# 			pass

# 	if len(drafts) > 0:
# 		items.append(drafts[0].to_json())

# 	# return json.dumps( { 'paths': paths, 'boxes': boxes, 'divs': divs, 'user': user, 'rasters': rasters, 'areasToUpdate': areas, 'zoom': zoom } )
# 	return json.dumps( { 'items': items, 'user': request.user.username } )

def emailIsConfirmed(request, userProfile=None):
	if not userProfile:
		userProfile = UserProfile.objects.get(username=request.user.username)
	if not userProfile.emailConfirmed:
		emailConfirmed = EmailAddress.objects.filter(user=request.user, verified=True).exists()
		userProfile.emailConfirmed = emailConfirmed
		userProfile.save()
		return emailConfirmed
	return userProfile.emailConfirmed

# @checkDebug
# def loadAllSVG(request, city=None):

# 	start = time.time()

# 	(cityPk, cityFinished) = getCity(request, city)
# 	if not cityPk:
# 		return json.dumps( { 'state': 'error', 'message': 'The city does not exist', 'code': 'CITY_DOES_NOT_EXIST' } )

# 	try:
# 		userProfile = UserProfile.objects.get(username=request.user.username)
# 		if not userProfile.emailConfirmed:
# 			emailConfirmed = EmailAddress.objects.filter(user=request.user, verified=True).exists()
# 			userProfile.emailConfirmed = emailConfirmed
# 			userProfile.save()
# 	except UserProfile.DoesNotExist:
# 		print('User does not exist')


# 	statusToLoad = ['pending', 'drawing', 'drawn', 'rejected']

# 	if isAdmin(request.user):
# 		statusToLoad.append('emailNotConfirmed')
# 		statusToLoad.append('notConfirmed')
# 		statusToLoad.append('flagged')

# 	# drawings = Drawing.objects(city=cityPk, status__in=statusToLoad).only('svg', 'status', 'pk', 'clientId', 'title', 'owner', 'bounds')
# 	drawings = Drawing.objects(city=cityPk, status__in=statusToLoad).only('status', 'pk', 'clientId', 'title', 'owner', 'bounds')

# 	items = []
# 	for drawing in drawings:
# 		items.append(drawing.to_json())

# 	# emailNotConfirmed and notConfirmed are are out of date

# 	# draftsAndNotConfirmed = Drawing.objects(city=cityPk, status__in=['draft', 'emailNotConfirmed', 'notConfirmed'], owner=request.user.username).only('svg', 'status', 'pk', 'clientId', 'owner', 'pathList', 'title')
# 	drafts = Drawing.objects(city=cityPk, status='draft', owner=request.user.username).only('svg', 'status', 'pk', 'clientId', 'owner', 'pathList', 'title')
	
# 	# if we could not find a draft and authenticated : create one
# 	if request.user.is_authenticated() and len(drafts) == 0:
# 		try:
# 			clientId = '' + str(datetime.datetime.now()) + str(random.random())
# 			drawing = Drawing(clientId=clientId, city=cityPk, planetX=0, planetY=0, owner=request.user.username, date=datetime.datetime.now(), status='draft')
# 			drawing.save()
# 			drafts = [drawing]
# 		except NotUniqueError:
# 			pass

# 	if len(drafts) > 0:
# 		items.append(drafts[0].to_json())

# 	# return json.dumps( { 'paths': paths, 'boxes': boxes, 'divs': divs, 'user': user, 'rasters': rasters, 'areasToUpdate': areas, 'zoom': zoom } )
# 	return json.dumps( { 'items': items, 'user': request.user.username } )

@checkSimulateSlowResponse
@checkDebug
def loadVotes(request, cityName=None):

	try:
		userVotes = UserProfile.objects.only('votes').get(username=request.user.username)
	except UserProfile.DoesNotExist:
		return json.dumps( { 'state': 'fail_silently', 'message': 'User does not exist.' } )

	votes = []

	if userVotes.votes:
		for vote in userVotes.votes:
			if isinstance(vote, Vote):
				try:
					pk = str(vote.drawing.clientId) if vote.drawing else str(vote.tile.clientId)
					votes.append({ 'pk': pk, 'positive': vote.positive, 'emailConfirmed': vote.author.emailConfirmed } )
				except DoesNotExist:
					pass

	return json.dumps( { 'votes': votes } )

# # @dajaxice_register
# @checkDebug
# def loadRasterizer(request, areasToLoad, itemsDates, city):

# 	start = time.time()

# 	(city, cityFinished) = getCity(request, city)
# 	if not city:
# 		return json.dumps( { 'state': 'error', 'message': 'The city does not exist' } )

# 	models = ['Path', 'Box']
# 	items = getItems(models, areasToLoad, 1, city, checkAddItemRasterizer, itemsDates)

# 	# add items to update which are not on the loading area (to update items which have been moved out of the area to load)
# 	for model in models:
# 		itemsQuerySet = globals()[model].objects(pk__in=itemsDates.keys())
# 		for item in itemsQuerySet:
# 			pk = str(item.pk)
# 			itemLastUpdate = unix_time_millis(item.lastUpdate)
# 			if not pk in items and itemsDates[pk]<itemLastUpdate:
# 				items[pk] = item.to_json()
# 			del itemsDates[pk]


# 	end = time.time()
# 	print "Time elapsed: " + str(end - start)

# 	return json.dumps( { 'items': items.values(), 'deletedItems': itemsDates } )

# # @return [Array<{x: x, y: y}>] the list of areas on which the bounds lie
# def getAreas(bounds):
# 	areas = {}
# 	scale = 1000
# 	l = int(floor(bounds['x'] / scale))
# 	t = int(floor(bounds['y'] / scale))
# 	r = int(floor((bounds['x']+bounds['width']) / scale))
# 	b = int(floor((bounds['y']+bounds['height']) / scale))

# 	areas = {}
# 	for x in range(l, r+1):
# 		for y in range(t, b+1):
# 			if not x in areas:
# 				areas[x] = {}
# 			areas[x][y] = True
# 	return areas

# --- Drawings --- #

# @dajaxice_register
@checkSimulateSlowResponse
@checkDebug
def saveDrawing(request, clientId, cityName, date, title, description=None, points=None, data=None):

	if not request.user.is_authenticated():
		return json.dumps({'state': 'not_logged_in'})

	city = getCity(cityName)
	
	if not city:
		return json.dumps( { 'state': 'error', 'message': 'The city does not exist', 'code': 'CITY_DOES_NOT_EXIST' } )

	cityPk = str(city.pk)

	if city.finished:
		return json.dumps({'state': 'info', 'message': "The installation is over"})

	pathList = []
	if points:
		pathList.append(json.dumps({ 'points': points, 'data': data }))

	drafts = Drawing.objects(city=cityPk, owner=request.user.username, status='draft')
	
	if drafts is not None and len(drafts) > 0:
		for draft in drafts:
			if len(draft.pathList) > 0:
				return json.dumps({'state': 'error', 'message': "You must submit your draft before create a new one"})
			else:
				draft.delete()

	try:
		drawing = Drawing(clientId=clientId, city=cityPk, planetX=0, planetY=0, owner=request.user.username, pathList=pathList, date=datetime.datetime.fromtimestamp(date/1000.0), title=title, description=description, status='draft')
		drawing.save()
	except NotUniqueError:
		return json.dumps({'state': 'error', 'message': 'A drawing with this id already exists.'})

	return json.dumps( {'state': 'success', 'owner': request.user.username, 'pk':str(drawing.pk), 'negativeVoteThreshold': city.negativeVoteThreshold, 'positiveVoteThreshold': city.positiveVoteThreshold, 'voteMinDuration': city.voteMinDuration } )

# @checkDebug
# def saveDrawing2(request, clientId, date, pathPks, title, description):
# 	if not request.user.is_authenticated():
# 		return json.dumps({'state': 'not_logged_in'})

# 	paths = []

# 	xMin = None
# 	xMax = None
# 	yMin = None
# 	yMax = None

# 	city = None
# 	planetX = None
# 	planetY = None

# 	for pathPk in pathPks:
# 		try:
# 			path = Path.objects.get(pk=pathPk)

# 			if path.drawing:
# 				return json.dumps({'state': 'error', 'message': 'One path is already part of a drawing.'})

# 			if not userAllowed(request, path.owner):
# 				return json.dumps({'state': 'error', 'message': 'One path is not property of user.'})

# 			if city != None and path.city != city or planetX != None and path.planetX != planetX or planetY != None and path.planetY != planetY:
# 				return json.dumps({'state': 'error', 'message': 'One path is from a different city or planet.'})

# 			city = path.city
# 			planetX = path.planetX
# 			planetY = path.planetY

# 			cbox = path.box['coordinates'][0]
# 			cleft = cbox[0][0]
# 			ctop = cbox[0][1]
# 			cright = cbox[2][0]
# 			cbottom = cbox[2][1]

# 			if not xMin or cleft < xMin:
# 				xMin = cleft
# 			if not xMax or cright > xMax:
# 				xMax = cright
# 			if not yMin or ctop < yMin:
# 				yMin = ctop
# 			if not yMax or cbottom > yMax:
# 				yMax = cbottom

# 			paths.append(path)
# 		except Path.DoesNotExist:
# 			return json.dumps({'state': 'error', 'message': 'Element does not exist for this user.'})

# 	points = [ [xMin, yMin], [xMax, yMin], [xMax, yMax], [xMin, yMax], [xMin, yMin] ]

# 	try:
# 		drawing = Drawing(clientId=clientId, city=city, planetX=planetX, planetY=planetY, box=[points], owner=request.user.username, paths=paths, date=datetime.datetime.fromtimestamp(date/1000.0), title=title, description=description)
# 		drawing.save()
# 	except NotUniqueError:
# 		return json.dumps({'state': 'error', 'message': 'A drawing with this name already exists.'})

# 	pathPks = []
# 	for path in paths:
# 		path.drawing = drawing
# 		path.isDraft = False
# 		path.save()
# 		pathPks.append(str(path.pk))

# 	return json.dumps( {'state': 'success', 'owner': request.user.username, 'pk':str(drawing.pk), 'pathPks': pathPks, 'negativeVoteThreshold': negativeVoteThreshold, 'positiveVoteThreshold': positiveVoteThreshold, 'voteMinDuration': voteMinDuration.total_seconds() } )

@checkSimulateSlowResponse
@checkDebug
def submitDrawing(request, pk, clientId, svg, date, bounds, title=None, description=None, png=None):

	if not request.user.is_authenticated():
		return json.dumps({'state': 'not_logged_in'})
	
	try:
		userProfile = UserProfile.objects.get(username=request.user.username)
	except UserProfile.DoesNotExist:
		return json.dumps( { 'status': 'error', 'message': 'The user profile does not exist.' } )
	
	if userProfile.banned:
		return json.dumps({'state': 'error', 'message': 'Your account has been suspended'})

	if not emailIsConfirmed(request, userProfile):
		return json.dumps({'state': 'error', 'message': 'Please confirm your email'})

	drawing = getDrawing(pk, clientId)

	if drawing is None:
		return json.dumps({'state': 'error', 'message': 'Element does not exist'})
	
	if drawing.status != 'draft':
		return json.dumps({'state': 'error', 'message': 'Error: drawing status is invalid'})
	
	try:
		city = City.objects.get(pk=drawing.city)
		if city.finished:
			return json.dumps({'state': 'info', 'message': "The city is finished"})
	except City.DoesNotExist:
		return json.dumps({'state': 'info', 'message': "The city is does not exist"})

	drawing.svg = svg
	drawing.date = datetime.datetime.fromtimestamp(date/1000.0)

	drawing.status = 'pending'
	drawing.title = title
	drawing.description = description

	drawing.box = makeBoxFromBounds(city, bounds)
	# if bounds is too large:
	# 	return json.dumps({'state': 'error', 'message': "The drawing is too large"})

	# drawing.bounds = json.dumps(bounds)
	# drawing.left = int(floor(bounds['x'] / 1000))
	# drawing.top = int(floor(bounds['y'] / 1000))
	
	# send_mail('[Comme un dessein] submitDrawing pending', u'submitDrawing pending ' + str(drawing.pk), 'contact@commeundessein.co', ['idlv.contact@gmail.com'], fail_silently=True)

	try:
		drawing.save()
	except NotUniqueError:
		return json.dumps({'state': 'error', 'message': 'A drawing with this name already exists.'})
	
	# Save image
	if png is not None:
		imgstr = re.search(r'base64,(.*)', png).group(1)
		output = open('Wetu/static/drawings/'+pk+'.png', 'wb')
		imageData = imgstr.decode('base64')
		output.write(imageData)
		output.close()

		updateRasters(imageData, bounds, city)

	svgFile = open('Wetu/static/drawings/'+pk+'.svg', 'wb')
	svgFile.write(svg)
	svgFile.close()

	drawingChanged.send(sender=None, type='new', clientId=drawing.clientId, pk=str(drawing.pk), svg=drawing.svg, city=city.name, itemType='drawing', bounds=bounds)

	applicationName = 'Comme un dessein' if settings.APPLICATION == 'COMME_UN_DESSEIN' else 'Espero'
	send_mail(applicationName + ' - New drawing', u'A new drawing has been submitted: https://commeundessein.co/drawing-'+str(drawing.pk) + u'\nsee thumbnail at: https://commeundessein.co/static/drawings/'+str(drawing.pk)+u'.png', 'contact@commeundessein.co', ['idlv.contact@gmail.com'], fail_silently=True)

	thread = Thread(target = createDrawingDiscussion, args = (drawing,))
	thread.start()
	thread.join()

	# Create new draft and return it

	clientId = '' + str(datetime.datetime.now()) + str(random.random())
	draft = Drawing(clientId=clientId, city=str(city.pk), planetX=0, planetY=0, owner=request.user.username, date=datetime.datetime.now(), status='draft')
	draft.save()

	return json.dumps( {'state': 'success', 'owner': request.user.username, 'pk':str(drawing.pk), 'status': drawing.status, 'negativeVoteThreshold': city.negativeVoteThreshold, 'positiveVoteThreshold': city.positiveVoteThreshold, 'voteMinDuration': city.voteMinDuration, 'draft': draft.to_json() } )


@checkSimulateSlowResponse
@checkDebug
def submitDiscussion(request, clientId, title, cityName, bounds):

	if not request.user.is_authenticated():
		return json.dumps({'state': 'not_logged_in'})
	
	try:
		userProfile = UserProfile.objects.get(username=request.user.username)
	except UserProfile.DoesNotExist:
		return json.dumps( { 'status': 'error', 'message': 'The user profile does not exist.' } )
	
	if userProfile.banned:
		return json.dumps({'state': 'error', 'message': 'Your account has been suspended'})

	if not emailIsConfirmed(request, userProfile):
		return json.dumps({'state': 'error', 'message': 'Please confirm your email'})

	city = getCity(cityName)
	
	if not city:
		return json.dumps( { 'state': 'error', 'message': 'The city does not exist', 'code': 'CITY_DOES_NOT_EXIST' } )

	cityPk = str(city.pk)

	discussion = Discussion(clientId=clientId, city=str(city.pk), title=title, owner=request.user.username, author=userProfile)
	discussion.box = makeBoxFromBounds(city, bounds)

	try:
		discussion.save()
	except NotUniqueError:
		return json.dumps({'state': 'error', 'message': 'A discussion with this clientId already exists.'})
	
	drawingChanged.send(sender=None, type='new', clientId=discussion.clientId, pk=str(discussion.pk), city=city.name, itemType='discussion', bounds=bounds)

	# Create new draft and return it

	clientId = '' + str(datetime.datetime.now()) + str(random.random())

	return json.dumps( {'state': 'success', 'owner': request.user.username, 'pk':str(discussion.pk) } )

@checkSimulateSlowResponse
@checkDebug
def loadDiscussion(request, pk):
	try:
		discussion = Discussion.objects.get(pk=pk)
	except Discussion.DoesNotExist:
		return json.dumps({'state': 'error', 'message': 'Element does not exist'})
	
	return json.dumps( {'state': 'success', 'discussion': discussion.to_json() } )


@checkSimulateSlowResponse
@checkDebug
def updateDiscussion(request, pk, title, bounds):

	if not request.user.is_authenticated():
		return json.dumps({'state': 'not_logged_in'})
	
	try:
		userProfile = UserProfile.objects.get(username=request.user.username)
	except UserProfile.DoesNotExist:
		return json.dumps( { 'status': 'error', 'message': 'The user profile does not exist.' } )
	
	if userProfile.banned:
		return json.dumps({'state': 'error', 'message': 'Your account has been suspended'})

	if not emailIsConfirmed(request, userProfile):
		return json.dumps({'state': 'error', 'message': 'Please confirm your email'})

	try:
		discussion = Discussion.objects.get(pk=pk)
	except Discussion.DoesNotExist:
		return json.dumps( { 'state': 'error', 'message': 'The discussion does not exist' } )


	try:
		city = City.objects.get(pk=discussion.city)
	except City.DoesNotExist:
		return json.dumps({'state': 'info', 'message': "The city is does not exist"})

	cityPk = str(city.pk)

	discussion.box = makeBoxFromBounds(city, bounds)
	discussion.title = title

	discussion.save()

	# drawingChanged.send(sender=None, type='new', clientId=discussion.clientId, pk=str(discussion.pk), city=city.name, itemType='discussion', bounds=bounds)

	return json.dumps( {'state': 'success' } )


@checkSimulateSlowResponse
@checkDebug
def updateDrawingBox(request, pk, clientId, bounds):
	if not isAdmin(request.user):
		return json.dumps({"status": "error", "message": "not_admin"})

	if not request.user.is_authenticated():
		return json.dumps({'state': 'not_logged_in'})
	
	try:
		userProfile = UserProfile.objects.get(username=request.user.username)
	except UserProfile.DoesNotExist:
		return json.dumps( { 'status': 'error', 'message': 'The user profile does not exist.' } )
	
	drawing = getDrawing(pk, clientId)

	if drawing is None:
		return json.dumps({'state': 'error', 'message': 'Element does not exist'})

	try:
		city = City.objects.get(pk=drawing.city)
	except City.DoesNotExist:
		return json.dumps({'state': 'info', 'message': "The city is does not exist"})

	drawing.box = makeBoxFromBounds(city, bounds)

	drawing.save()

	return json.dumps( {'state': 'success' } )


@checkSimulateSlowResponse
@checkDebug
def submitTile(request, number, x, y, bounds, clientId, cityName):

	if not request.user.is_authenticated():
		return json.dumps({'state': 'not_logged_in'})
	
	try:
		userProfile = UserProfile.objects.get(username=request.user.username)
	except UserProfile.DoesNotExist:
		return json.dumps( { 'status': 'error', 'message': 'The user profile does not exist.' } )
	
	if userProfile.banned:
		return json.dumps({'state': 'error', 'message': 'Your account has been suspended'})

	if not emailIsConfirmed(request, userProfile):
		return json.dumps({'state': 'error', 'message': 'Please confirm your email'})


	city = getCity(cityName)
	
	if not city:
		return json.dumps( { 'state': 'error', 'message': 'The city does not exist', 'code': 'CITY_DOES_NOT_EXIST' } )

	cityPk = str(city.pk)

	try:
		existingTile = Tile.objects.get(city=cityPk, x=x, y=y)
		return json.dumps({'state': 'error', 'message': 'A tile with this position already exists'})
	except Tile.DoesNotExist:
		pass

	tile = Tile(author=userProfile, owner=userProfile.username, city=cityPk, number=number, x=x, y=y, box=makeBoxFromBounds(city, bounds), clientId=clientId, dueDate=city.eventDate, placementDate=datetime.datetime.now() + datetime.timedelta(hours=24))

	try:
		tile.save()
	except NotUniqueError:
		return json.dumps({'state': 'error', 'message': 'A tile with this client id already exists'})

	drawingChanged.send(sender=None, type='new', clientId=tile.clientId, pk=str(tile.pk), city=cityName, itemType='tile', bounds=bounds)

	# thread = Thread(target = createDrawingDiscussion, args = (drawing,))
	# thread.start()
	# thread.join()

	return json.dumps( {'state': 'success', 'votes': [], 'tile': tile.to_json(), 'tile_author': tile.author.username } )

def createDrawingDiscussion(drawing):
	values = { 'title': drawing.title, 'raw': u'Discussion à propos de ' + drawing.title + u'.\n\nhttps://commeundessein.co/drawing-'+str(drawing.pk)+'\n\nhttps://commeundessein.co/static/drawings/'+str(drawing.pk)+'.png', 'category': 'dessins', 'api_username': localSettings['DISCOURSE_USERNAME'], 'api_key': localSettings['DISCOURSE_API_KEY'] }

	values_data = {}
	for k, v in values.iteritems():
		values_data[k] = unicode(v).encode('utf-8')
	data = urllib.urlencode(values_data)

	try:
		url = 'http://discussion.commeundessein.co/posts'
		req = urllib2.Request(url, data)
		response = urllib2.urlopen(req)
		resultJson = response.read()
		result = json.loads(resultJson)
		drawing.discussionId = result['topic_id']
	except:
		pass
	drawing.save()
	return

# @checkDebug
# def validateDrawing(request, pk):

# 	if not isAdmin(request.user):
# 		return json.dumps({"status": "error", "message": "not_admin"})
# 	else:
# 		return json.dumps({"status": "error", "message": "deprecated function: no need to validate drawings anymore."})

# 	drawing = getDrawing(pk, None)

# 	if drawing is None:
# 		return json.dumps({'state': 'error', 'message': 'Drawing does not exist'})

# 	if drawing.status != 'notConfirmed':
# 		return json.dumps({'state': 'error', 'message': 'Drawing status is not notConfirmed: ' + drawing.status })

# 	try:
# 		userProfile = UserProfile.objects.get(username=drawing.owner)
# 	except userProfile.DoesNotExist:
# 		return json.dumps( { 'status': 'error', 'message': 'The user profile does not exist.' } )

# 	if userProfile.emailConfirmed:
# 		drawing.status = 'pending'
# 		# send_mail('[Comme un dessein] validateDrawing', u'validateDrawing pending ' + str(drawing.pk), 'contact@commeundessein.co', ['idlv.contact@gmail.com'], fail_silently=True)
# 		cityName = 'Wetu'
# 		try:
# 			city = City.objects.get(pk=drawing.city)
# 			cityName = city.name
# 		except City.DoesNotExist:
# 			print('The city does not exist')
# 		drawingChanged.send(sender=None, type='new', clientId=drawing.clientId, pk=str(drawing.pk), svg=drawing.svg, city=cityName)
# 	else:
# 		# send_mail('[Comme un dessein] validateDrawing', u'validateDrawing emailNotConfirmed ' + str(drawing.pk), 'contact@commeundessein.co', ['idlv.contact@gmail.com'], fail_silently=True)
# 		drawing.status = 'emailNotConfirmed'

# 	drawing.save()
# 	return json.dumps( {'state': 'success'} )

@checkSimulateSlowResponse
@checkDebug
def bannUser(request, username, reportDrawings=False, reportTiles=False, removeVotes=False, removeComments=False):
	if not isAdmin(request.user):
		return json.dumps({"status": "error", "message": "not_admin"})
	try:
		userProfile = UserProfile.objects.get(username=username)
	except UserProfile.DoesNotExist:
		return json.dumps({"status": "error", "message": "The user does not exists."})

	userProfile.banned = True

	if reportDrawings:
		drawings = Drawing.objects(owner=userProfile.username)
		for drawing in drawings:
			reportAbuse(request, drawing.pk, 'drawing')

	if reportTiles:
		tiles = Tile.objects(owner=userProfile.username)
		for tile in tiles:
			reportAbuse(request, tile.pk, 'tile')

	if removeVotes:
		for vote in userProfile.votes[:]:
			if isinstance(vote, Vote):
				if vote.drawing and vote in vote.drawing.votes:
					vote.drawing.votes.remove(vote)
					vote.drawing.save()
				if vote.tile and vote in vote.tile.votes:
					vote.tile.votes.remove(vote)
					vote.tile.save()
				vote.delete()
	
	if removeComments:
		for comment in userProfile.comments[:]:
			if isinstance(comment, Comment):
				if comment.drawing and comment in comment.drawing.comments:
					comment.drawing.comments.remove(comment)
					comment.drawing.save()
				if comment.tile and comment in comment.tile.comments:
					comment.tile.comments.remove(comment)
					comment.tile.save()
				comment.delete()

	userProfile.save()

	return json.dumps( {'state': 'success'} )

@checkSimulateSlowResponse
@checkDebug
def createUsers(request, logins):

	if not isAdmin(request.user):
		return json.dumps({"status": "error", "message": "not_admin"})
	
	for login in logins:
		print('user: ' + login['username'])
		try:
			user = User.objects.create_user(username=''+login['username'])
			user.set_password(''+login['password'])
			user.save()
			userProfile = UserProfile(username=''+login['username'], emailConfirmed=True)
			userProfile.save()
			print('created ' + userProfile.username)
			try:
				userTest = User.objects.get(username=''+login['username'])
			except Exception as e:
				print('could not get User')
				print(e)
			try:
				userProfileTest = UserProfile.objects.get(username=''+login['username'])
			except Exception as e:
				print('could not get UserProfile')
				print(e)
		except Exception as e:
			print(e)
  			pass

	return json.dumps( {'state': 'success'} )

@checkSimulateSlowResponse
@checkDebug
def reportAbuse(request, pk, itemType='drawing'):

	if not request.user.is_authenticated():
		return json.dumps({'state': 'not_logged_in'})

	try:
		userProfile = UserProfile.objects.get(username=request.user.username)
	except UserProfile.DoesNotExist:
		return json.dumps({"status": "error", "message": "The user does not exists."})

	if not emailIsConfirmed(request, userProfile):
		return json.dumps({'state': 'error', 'message': 'Please confirm your email'})

	if not userProfile.emailConfirmed:
		return json.dumps({"status": "error", "message": "Your email must be confirmed to report an abuse."})
	
	if userProfile.banned:
		return json.dumps({'state': 'error', 'message': 'Your account has been suspended'})

	if itemType == 'drawing':
		try:
			item = Drawing.objects.get(pk=pk)
		except Drawing.DoesNotExist:
			return json.dumps({'state': 'error', 'message': 'Element does not exist'})
	else:
		try:
			item = Tile.objects.get(pk=pk)
		except Tile.DoesNotExist:
			return json.dumps({'state': 'error', 'message': 'Element does not exist'})

	try:
		city = City.objects.get(pk=item.city)
		if city.finished:
			return json.dumps({'state': 'info', 'message': "The installation is over"})
	except City.DoesNotExist:
		return json.dumps({'state': 'error', 'message': "The city does not exist"})

	if item.status != 'flagged_pending' and item.status != 'flagged':
		item.previousStatus = item.status

	wasFlaggedPending = item.status == 'flagged_pending'
	
	if userProfile.admin:
		item.status = 'flagged'
		try:
			drawingOwner = UserProfile.objects.get(username=item.owner)
			drawingOwner.nAbuses += 1
			drawingOwner.save()
		except UserProfile.DoesNotExist:
			pass
	else:
		item.status = 'flagged_pending'
	# send_mail('[Comme un dessein] reportAbuse', u'reportAbuse flagged ' + str(item.pk), 'contact@commeundessein.co', ['idlv.contact@gmail.com'], fail_silently=True)
	item.abuseReporter = request.user.username
	item.save()

	if itemType == 'drawing' and not wasFlaggedPending: 	# if status was flagged_pending: the drawing was removed when the user flagged it
		layerName = 'inactive' if item.previousStatus == 'rejected' else 'active'
		removeDrawingFromRasters(city, item, layerName)
	
	emailOfDrawingOwner = ''
	try:
		ownerOfDrawing = User.objects.get(username=item.owner)
		emailOfDrawingOwner = ownerOfDrawing.email
	except User.DoesNotExist:
		print('OwnerOfDrawing does not exist.')

	applicationName = 'Comme un dessein' if settings.APPLICATION == 'COMME_UN_DESSEIN' else 'Espero'
	if itemType == 'drawing':
		send_mail(applicationName + ' - Abuse report !', u'The drawing \"' + item.title + u'\" has been reported on Comme un Dessein !\n\nVerify it on https://commeundessein.co/drawing-'+str(item.pk)+u'\nAuthor of the report: ' + request.user.username + u', email: ' + request.user.email + u'\nAuthor of the flagged drawing: ' + item.owner + ', email: ' + emailOfDrawingOwner, 'contact@commeundessein.co', ['idlv.contact@gmail.com'], fail_silently=True)
	else:
		send_mail(applicationName + ' - Abuse report !', u'The tile \"' + str(item.number) + u'\" has been reported on Comme un Dessein !\n\nVerify it on https://commeundessein.co/drawing-'+str(item.pk)+u'\nAuthor of the report: ' + request.user.username + u', email: ' + request.user.email + u'\nAuthor of the flagged drawing: ' + item.owner + ', email: ' + emailOfDrawingOwner, 'contact@commeundessein.co', ['idlv.contact@gmail.com'], fail_silently=True)

	try:
		itemName = 'dessin' if itemType == 'drawing' else 'case'
		title = item.title if itemType == 'drawing' else str(item.number)
		userProfile = UserProfile.objects.get(username=item.owner)
		message = u'Votre ' + itemName + u' \"' + title + u'\" à été modéré.'
		queueEmail(userProfile, message)
	except UserProfile.DoesNotExist:
		pass

	drawingChanged.send(sender=None, type='status', clientId=item.clientId, status=item.status, pk=str(item.pk), itemType=itemType, bounds=makeBoundsFromBox(city, item.box))

	return json.dumps( {'state': 'success'} )

@checkSimulateSlowResponse
@checkDebug
def cancelAbuse(request, pk, itemType='drawing'):

	if not request.user.is_authenticated():
		return json.dumps({'state': 'not_logged_in'})

	if not isAdmin(request.user):
		return json.dumps({"status": "error", "message": "not_admin"})

	# send_mail('[Comme un dessein] validateDrawing', u'validateDrawing pending ' + pk, 'contact@commeundessein.co', ['idlv.contact@gmail.com'], fail_silently=True)

	if itemType == 'drawing':
		try:
			drawing = Drawing.objects.get(pk=pk)
		except Drawing.DoesNotExist:
			return json.dumps({'state': 'error', 'message': 'Element does not exist'})

		updateDrawingState(None, drawing, True)
		

		reporter = None
		try:
			reporter = UserProfile.objects.get(username=drawing.abuseReporter)
		except UserProfile.DoesNotExist:
			return json.dumps({"status": "error", "message": "The abuse reporter does not exists."})

		reporter.nFalseReport += 1
		reporter.save()
	else:
		try:
			tile = Tile.objects.get(pk=pk)
		except Tile.DoesNotExist:
			return json.dumps({'state': 'error', 'message': 'Element does not exist'})
		
		updateTileState(None, tile, True)

	# Websocket broadcast is done in updateDrawingState or updateTileState

	return json.dumps( {'state': 'success'} )

@checkSimulateSlowResponse
@checkDebug
def deleteUsers(request, logins):
	if not isAdmin(request.user):
		return json.dumps({"status": "error", "message": "not_admin"})
	
	for login in logins:
		print('user: ' + login['username'])
		try:
			user = User.objects.get(username=login['username'])
			user.delete()
			userProfile = UserProfile.objects.get(username=login['username'])
			userProfile.delete()
			print('deleted ' + login['username'])
			try:
				userTest = User.objects.get(username=''+login['username'])
				print('could get User')
			except Exception as e:
				print('could not get User')
				print(e)
			try:
				userProfileTest = UserProfile.objects.get(username=''+login['username'])
				print('could get UserProfile')
			except Exception as e:
				print('could not get UserProfile')
				print(e)

		except Exception as e:
			print(e)
  			pass
	return json.dumps( {'state': 'success'} )

@checkSimulateSlowResponse
@checkDebug
def createDrawingThumbnail(request, pk, png=None):
	
	if not isAdmin(request.user):
		return json.dumps({"status": "error", "message": "not_admin"})

	imgstr = re.search(r'base64,(.*)', png).group(1)
	output = open('Wetu/static/drawings/'+pk+'.png', 'wb')
	output.write(imgstr.decode('base64'))
	output.close()
	return

# @dajaxice_register
@checkSimulateSlowResponse
@checkDebug
def loadDrawing(request, pk, loadSVG=False, loadVotes=True, svgOnly=False, loadPathList=False):
	try:
		fields = ['pk']
		if not svgOnly:
			fields += ['status', 'clientId', 'title', 'owner', 'discussionId', 'box']
		if loadSVG or svgOnly:
			fields.append('svg')
		if loadVotes:
			fields.append('votes')
		if loadPathList:
			fields.append('pathList')

		drawing = Drawing.objects.only(*fields).get(pk=pk)
	except Drawing.DoesNotExist:
		return json.dumps({'state': 'error', 'message': 'Element does not exist'})
	
	votes = []
	
	if loadVotes and drawing.votes:

		for vote in drawing.votes:
			if isinstance(vote, Vote):
				try:
					votes.append( { 'vote': vote.to_json(), 'author': vote.author.username, 'authorPk': str(vote.author.pk), 'emailConfirmed': vote.author.emailConfirmed } )
				except DoesNotExist:
					pass

	return json.dumps( {'state': 'success', 'votes': votes, 'drawing': drawing.to_json() } )

@checkSimulateSlowResponse
@checkDebug
def loadTile(request, pk, loadVotes=True):
	try:
		fields = ['pk', 'clientId', 'author', 'number', 'x', 'y', 'status', 'photoURL', 'dueDate', 'placementDate']

		if loadVotes:
			fields.append('votes')

		tile = Tile.objects.only(*fields).get(pk=pk)
	except Tile.DoesNotExist:
		return json.dumps({'state': 'error', 'message': 'Element does not exist'})
	
	votes = []
	
	if loadVotes and tile.votes:
		for vote in tile.votes:
			if isinstance(vote, Vote):
				try:
					votes.append( { 'vote': vote.to_json(), 'author': vote.author.username, 'authorPk': str(vote.author.pk), 'emailConfirmed': vote.author.emailConfirmed } )
				except DoesNotExist:
					pass

	return json.dumps( {'state': 'success', 'votes': votes, 'tile': tile.to_json(), 'tile_author': tile.author.username } )

@checkSimulateSlowResponse
@checkDebug
def loadTimelapse(request, pks):
	
	drawings = Drawing.objects(pk__in=pks, status__in=['rejected', 'drawn', 'drawing', 'validated', 'pending']).only('pk', 'status', 'votes')

	results = []
	
	for drawing in drawings:
		votes = []
		for vote in drawing.votes:
			if isinstance(vote, Vote):
				try:
					votes.append( { 'vote': vote.to_json(), 'author': vote.author.username, 'authorPk': str(vote.author.pk), 'emailConfirmed': vote.author.emailConfirmed } )
				except DoesNotExist:
					pass
		result = { 'pk': str(drawing.pk), 'votes': votes, 'status': drawing.status }
		results.append(result)

	# file = json.dumps( {'state': 'success', 'results': results }, indent=4 )
	# output = open('timelapse.json', 'wb')
	# output.write(file)
	# output.close()

	return json.dumps( {'state': 'success', 'results': results } )

@checkSimulateSlowResponse
@checkDebug
def getDrawingDiscussionId(request, pk):
	try:
		drawing = Drawing.objects.only('discussionId').get(pk=pk)
	except Drawing.DoesNotExist:
		return json.dumps({'state': 'error', 'message': 'Element does not exist'})

	return  json.dumps( {'state': 'success', 'drawing': drawing.to_json() } )

@checkSimulateSlowResponse
@checkDebug
def loadComments(request, itemPk, itemType='drawing'):
	
	if itemType == 'tile':
		try:
			drawing = Tile.objects.only('comments').get(pk=itemPk)
		except Tile.DoesNotExist:
			return json.dumps({'state': 'error', 'message': 'Tile does not exist'})
	else:
		try:
			drawing = Drawing.objects.only('comments').get(pk=itemPk)
		except Drawing.DoesNotExist:
			return json.dumps({'state': 'error', 'message': 'Drawing does not exist'})
	
	comments = []
	if drawing.comments:
		for comment in drawing.comments:
			if isinstance(comment, Comment):
				try:
					comments.append( { 'comment': comment.to_json(), 'author': comment.author.username, 'authorPk': str(comment.author.pk), 'emailConfirmed': comment.author.emailConfirmed } )
				except DoesNotExist:
					pass

	return json.dumps( {'state': 'success', 'comments': comments } )

@checkSimulateSlowResponse
@checkDebug
def loadDrawings(request, pks, loadSVG=False):
	try:
		fields = ['status', 'pk', 'clientId', 'title', 'owner', 'votes']
		
		if loadSVG:
			fields.append('svg')

		drawings = Drawing.objects(pk__in=pks).only(*fields)

	except Drawing.DoesNotExist:
		return json.dumps({'state': 'error', 'message': 'Element does not exist'})

	items = []
	for drawing in drawings:
		userVoteJson = None
		try:
			userVote = Vote.objects.only('positive', 'emailConfirmed').get(drawing=drawing.pk, author=request.user.username)
			userVoteJson = userVote.to_json()
		except Vote.DoesNotExist:
			pass
		items.append({'drawing':drawing.to_json(), 'userVote': userVoteJson })
	
	return json.dumps( { 'items': items } )

# @dajaxice_register
@checkSimulateSlowResponse
@checkDebug
def updateDrawing(request, pk, title, description=None):

	if not request.user.is_authenticated():
		return json.dumps({'state': 'not_logged_in'})

	try:
		user = UserProfile.objects.get(username=request.user.username)
	except UserProfile.DoesNotExist:
		return json.dumps({'state': 'error', 'message': 'The user profile does not exist.'})
	
	if user.banned:
		return json.dumps({'state': 'error', 'message': 'Your account has been suspended'})

	try:
		drawing = Drawing.objects.get(pk=pk)
	except Drawing.DoesNotExist:
		return json.dumps({'state': 'error', 'message': 'Element does not exist'})

	try:
		city = City.objects.get(pk=drawing.city)
		if city.finished:
			return json.dumps({'state': 'info', 'message': "The installation is over"})
	except City.DoesNotExist:
		pass

	if not userAllowed(request, drawing.owner):
		return json.dumps({'state': 'error', 'message': 'Not owner of drawing'})
	
	if isDrawingStatusValidated(drawing):
		return json.dumps({'state': 'error', 'message': 'The drawing is already validated, it cannot be modified anymore.'})

	drawing.title = title
	
	if description:
		drawing.description = description

	try:
		drawing.save()
	except NotUniqueError:
		return json.dumps({'state': 'error', 'message': 'A drawing with this name already exists.'})

	drawingChanged.send(sender=None, type='title', clientId=drawing.clientId, title=title, description=description, itemType='drawing')

	return json.dumps( {'state': 'success' } )

def updateDrawingRaster(bounds, png, city):
	imgstr = re.search(r'base64,(.*)', png).group(1)
	imageData = imgstr.decode('base64')
	updateRasters(imageData, bounds, city)
	return

@checkSimulateSlowResponse
@checkDebug
def updateDrawingImage(request, pk, bounds, png):

	if not request.user.is_authenticated():
		return json.dumps({'state': 'not_logged_in'})

	try:
		user = UserProfile.objects.get(username=request.user.username)
	except UserProfile.DoesNotExist:
		return json.dumps({'state': 'error', 'message': 'The user profile does not exist.'})
	
	if user.banned:
		return json.dumps({'state': 'error', 'message': 'Your account has been suspended'})

	try:
		drawing = Drawing.objects.get(pk=pk)
	except Drawing.DoesNotExist:
		return json.dumps({'state': 'error', 'message': 'Element does not exist'})

	try:
		city = City.objects.get(pk=drawing.city)
		if city.finished:
			return json.dumps({'state': 'info', 'message': "The installation is over"})
	except City.DoesNotExist:
		pass

	if not userAllowed(request, drawing.owner):
		return json.dumps({'state': 'error', 'message': 'Not owner of drawing'})
	
	updateDrawingRaster(bounds, png, city)

	return json.dumps( {'state': 'success' } )

def getDrawing(pk=None, clientId=None):

	if pk is None and clientId is None:
		return None

	drawing = None

	if pk:
		try:
			drawing = Drawing.objects.get(pk=pk)
		except Drawing.DoesNotExist:
			if not clientId:
				return None
	
	if drawing is None and clientId:
		try:
			drawing = Drawing.objects.get(clientId=clientId)
		except Drawing.DoesNotExist:
			return None

	return drawing

# @dajaxice_register
@checkSimulateSlowResponse
@checkDebug
def addPathToDrawing(request, points, data, bounds, pk=None, clientId=None):
	
	if not request.user.is_authenticated():
		return json.dumps({'state': 'not_logged_in'})

	drawing = getDrawing(pk, clientId)

	if drawing is None:
		return json.dumps({'state': 'error', 'message': 'Element does not exist'})

	if not userAllowed(request, drawing.owner):
		return json.dumps({'state': 'error', 'message': 'Not owner of drawing'})

	if drawing.status != 'draft':
		return json.dumps({'state': 'error', 'message': 'The drawing is not a draft, it cannot be modified anymore.'})

	try:
		city = City.objects.get(pk=drawing.city)
		if city.finished:
			return json.dumps({'state': 'info', 'message': "The installation is over"})
	except City.DoesNotExist:
		pass

	drawing.pathList.append(json.dumps({ 'points': points, 'data': data }))
	
	drawing.box = makeBoxFromBounds(city, bounds)

	drawing.save()

	return json.dumps( {'state': 'success' } )

@checkSimulateSlowResponse
@checkDebug
def addPathsToDrawing(request, pointLists, bounds, pk=None, clientId=None):

	if not request.user.is_authenticated():
		return json.dumps({'state': 'not_logged_in'})

	if pk is None and clientId is None:
		return json.dumps({'state': 'error', 'message': 'Element does not exist'})

	drawing = getDrawing(pk, clientId)

	if drawing is None:
		return json.dumps({'state': 'error', 'message': 'Element does not exist'})

	try:
		city = City.objects.get(pk=drawing.city)
		if city.finished:
			return json.dumps({'state': 'info', 'message': "This installation is over"})
	except City.DoesNotExist:
		pass

	if not userAllowed(request, drawing.owner):
		return json.dumps({'state': 'error', 'message': 'Not owner of drawing'})

	if drawing.status != 'draft':
		return json.dumps({'state': 'error', 'message': 'The drawing is not a draft, it cannot be modified anymore.'})

	for p in pointLists:
		drawing.pathList.append(json.dumps({ 'points': p['points'], 'data': p['data'] }))

	drawing.box = makeBoxFromBounds(city, bounds)

	drawing.save()

	return json.dumps( {'state': 'success' } )

@checkSimulateSlowResponse
@checkDebug
def setPathsToDrawing(request, pointLists, bounds, pk=None, clientId=None):
	
	if not request.user.is_authenticated():
		return json.dumps({'state': 'not_logged_in'})

	if pk is None and clientId is None:
		return json.dumps({'state': 'error', 'message': 'Element does not exist'})

	drawing = getDrawing(pk, clientId)

	if drawing is None:
		return json.dumps({'state': 'error', 'message': 'Element does not exist'})

	try:
		city = City.objects.get(pk=drawing.city)
		if city.finished:
			return json.dumps({'state': 'info', 'message': "The installation is over"})
	except City.DoesNotExist:
		return json.dumps({'state': 'error', 'message': "The city does not exist"})

	if not userAllowed(request, drawing.owner):
		return json.dumps({'state': 'error', 'message': 'Not owner of drawing'})

	if drawing.status != 'draft':
		return json.dumps({'state': 'error', 'message': 'The drawing is not a draft, it cannot be modified anymore.'})

	drawing.pathList = []

	for p in pointLists:
		drawing.pathList.append(json.dumps({ 'points': p['points'], 'data': p['data'] }))

	if bounds:
		drawing.box = makeBoxFromBounds(city, bounds)

	drawing.box = None

	drawing.save()

	return json.dumps( {'state': 'success' } )

# @checkSimulateSlowResponse
# @checkDebug
# def updateDrawings(request):
# 	if not isAdmin(request.user):
# 		return json.dumps( { 'state': 'error', 'message': 'You must be administrator to update drawings.' } )

# 	drawings = Drawing.objects()
# 	for drawing in drawings:
# 		drawing.pathList = []
# 		for path in drawing.paths:
# 			data = json.loads(path.data)
# 			points = json.dumps({ 'points': data['points'], 'data': data['data'] })
# 			drawing.pathList.append(points)
# 		drawing.save()
# 	return json.dumps( {'state': 'success' } )

@checkSimulateSlowResponse
@checkDebug
def updateDrawingBounds(request, pk, bounds, svg):
	if not isAdmin(request.user):
		return json.dumps( { 'state': 'error', 'message': 'You must be administrator to update drawings.' } )
	
	try:
		drawing = Drawing.objects.get(pk=pk)
	except Drawing.DoesNotExist:
		return json.dumps({'state': 'error', 'message': 'Element does not exist'})

	try:
		city = City.objects.get(pk=drawing.city)
		if city.finished:
			return json.dumps({'state': 'info', 'message': "The city is finished"})
	except City.DoesNotExist:
		return json.dumps({'state': 'error', 'message': "The city does not exist"})

	drawing.box = makeBoxFromBounds(city, bounds)
	drawing.save()

	svgFile = open('Wetu/static/drawings/'+pk+'.svg', 'wb')
	svgFile.write(svg)
	svgFile.close()

	return json.dumps( {'state': 'success' } )

@checkSimulateSlowResponse
@checkDebug
def updateDrawingSVG(request, pk, svg):
	if not isAdmin(request.user):
		return json.dumps( { 'state': 'error', 'message': 'You must be administrator to update drawings.' } )
	try:
		drawing = Drawing.objects.get(pk=pk)
	except Drawing.DoesNotExist:
		return json.dumps({'state': 'error', 'message': 'Element does not exist'})

	drawing.svg = svg
	drawing.save()

	return json.dumps( {'state': 'success' } )

# @dajaxice_register
@checkSimulateSlowResponse
@checkDebug
def deleteDrawing(request, pk):

	if not request.user.is_authenticated():
		return json.dumps({'state': 'not_logged_in'})

	try:
		drawing = Drawing.objects.get(pk=pk)
	except Drawing.DoesNotExist:
		return json.dumps({'state': 'error', 'message': 'Element does not exist for this user.'})

	try:
		city = City.objects.get(pk=drawing.city)
		if city.finished:
			return json.dumps({'state': 'info', 'message': "The installation is over"})
	except City.DoesNotExist:
		return json.dumps({'state': 'error', 'message': "The city does not exist"})


	if not userAllowed(request, drawing.owner):
		return json.dumps({'state': 'error', 'message': 'Not owner of drawing'})

	if isDrawingStatusValidated(drawing):
		return json.dumps({'state': 'error', 'message': 'The drawing is already validated, it cannot be cancelled anymore.'})

	drawing.delete()

	drawingChanged.send(sender=None, type='delete', clientId=drawing.clientId, pk=str(drawing.pk), itemType='drawing')

	return json.dumps( { 'state': 'success', 'pk': pk } )

@checkSimulateSlowResponse
@checkDebug
def deleteDiscussion(request, pk):

	if not request.user.is_authenticated():
		return json.dumps({'state': 'not_logged_in'})

	try:
		discussion = Discussion.objects.get(pk=pk)
	except Discussion.DoesNotExist:
		return json.dumps({'state': 'error', 'message': 'Element does not exist for this user.'})

	try:
		city = City.objects.get(pk=discussion.city)
		if city.finished:
			return json.dumps({'state': 'info', 'message': "The installation is over"})
	except City.DoesNotExist:
		return json.dumps({'state': 'error', 'message': "The city does not exist"})

	if not userAllowed(request, discussion.owner):
		return json.dumps({'state': 'error', 'message': 'Not owner of drawing'})

	discussion.delete()

	drawingChanged.send(sender=None, type='delete', clientId=discussion.clientId, pk=str(discussion.pk), itemType='discussion')

	return json.dumps( { 'state': 'success', 'pk': pk } )

@checkSimulateSlowResponse
@checkDebug
def cancelDrawing(request, pk):

	if not request.user.is_authenticated():
		return json.dumps({'state': 'not_logged_in'})

	try:
		drawing = Drawing.objects.get(pk=pk)
	except Drawing.DoesNotExist:
		return json.dumps({'state': 'error', 'message': 'Element does not exist for this user.'})

	if not userAllowed(request, drawing.owner):
		return json.dumps({'state': 'error', 'message': 'Not owner of drawing'})
	
	try:
		city = City.objects.get(pk=drawing.city)
		if city.finished:
			return json.dumps({'state': 'info', 'message': "The installation is over"})
	except City.DoesNotExist:
		return json.dumps({'state': 'error', 'message': "The city does not exist"})

	if isDrawingStatusValidated(drawing):
		return json.dumps({'state': 'error', 'message': 'The drawing is already validated, it cannot be cancelled anymore.'})

	previousStatus = drawing.status
	if drawing.status != 'flagged_pending' and drawing.status != 'flagged':
		drawing.previousStatus = previousStatus

	drawing.status = 'draft'
	# send_mail('[Comme un dessein] cancelDrawing', u'cancelDrawing draft ' + str(drawing.pk), 'contact@commeundessein.co', ['idlv.contact@gmail.com'], fail_silently=True)
	drawing.svg = None
	drawing.title = None
	
	try:
		drafts = Drawing.objects(city=drawing.city, status=['draft'], owner=drawing.owner)
		for draft in drafts:
			if len(draft.pathList) > 0:
				return json.dumps({'state': 'error', 'message': "You must submit your draft before cancelling a drawing"})
	except Drawing.DoesNotExist:
		pass

	# for draft in drafts:
	# 	drawing.pathList += draft.pathList

	for vote in drawing.votes[:]:
		vote.author.votes.remove(vote)
		vote.author.save()
		drawing.votes.remove(vote)
		vote.delete()

	for comment in drawing.comments[:]:
		comment.author.comments.remove(comment)
		comment.author.save()
		drawing.comments.remove(comment)
		comment.delete()

	drawing.save()

	layerName = 'inactive' if previousStatus == 'rejected' else 'active'
	removeDrawingFromRasters(city, drawing, layerName)

	drawingChanged.send(sender=None, type='cancel', clientId=drawing.clientId, pk=str(drawing.pk), itemType='drawing')

	return json.dumps( { 'state': 'success', 'pk': pk, 'status': drawing.status, 'pathList': drawing.pathList } )

@checkSimulateSlowResponse
@checkDebug
def cancelTile(request, pk):

	if not request.user.is_authenticated():
		return json.dumps({'state': 'not_logged_in'})

	try:
		tile = Tile.objects.get(pk=pk)
	except Tile.DoesNotExist:
		return json.dumps({'state': 'error', 'message': 'Element does not exist for this user.'})

	if not userAllowed(request, tile.author.username):
		return json.dumps({'state': 'error', 'message': 'Not owner of tile'})
	
	try:
		city = City.objects.get(pk=tile.city)
		if city.finished:
			return json.dumps({'state': 'info', 'message': "The installation is over"})
	except City.DoesNotExist:
		return json.dumps({'state': 'error', 'message': "The city does not exist"})

	tile.delete()

	drawingChanged.send(sender=None, clientId=tile.clientId, type='cancel', pk=str(tile.pk), itemType='tile')

	return json.dumps( { 'state': 'success', 'tile': tile.to_json() } )

@checkSimulateSlowResponse
@checkDebug
def deleteDrawings(request, drawingsToDelete, confirm=None):
	if not isAdmin(request.user):
		return json.dumps( {'state': 'error', 'message': 'not admin' } )

	if confirm != 'confirm':
		return json.dumps( {'state': 'error', 'message': 'please confirm' } )
	
	drawings = Drawing.objects(pk__in=drawingsToDelete)
	
	for drawing in drawings:
		drawing.delete()

		try:
			city = City.objects.get(pk=drawing.city)
			if drawing.status != 'flagged_pending' and drawing.status != 'flagged':
				layerName = 'inactive' if drawing.status == 'rejected' else 'inactive'
				removeDrawingFromRasters(city, drawing, layerName)
		except City.DoesNotExist:
			pass

		drawingChanged.send(sender=None, type='delete', clientId=drawing.clientId, pk=str(drawing.pk), itemType='drawing')

	return json.dumps( { 'state': 'success', 'pks': drawingsToDelete } )

# --- get drafts --- #

@checkSimulateSlowResponse
@checkDebug
def removeDeadReferences(request):

	if not isAdmin(request.user):
		return json.dumps( {'state': 'error', 'message': 'not admin' } )

	users = UserProfile.objects()
	for user in users:
		modified = False
		for vote in user.votes[:]:
			if not isinstance(vote, Vote):
				user.votes.remove(vote)
				modified = True
		for comment in user.comments[:]:
			if not isinstance(comment, Comment):
				user.comments.remove(comment)
				modified = True
		if modified:
			user.save()

	# votes = Vote.objects()
	# for vote in votes:
	# 	if not isinstance(vote.author, UserProfile) or not isinstance(vote.drawing, Drawing):
	# 		vote.delete()
	
	# comments = Comment.objects()
	# for comment in comments:
	# 	if not isinstance(comment.author, UserProfile) or not isinstance(comment.drawing, Drawing):
	# 		comment.delete()

	drawings = Drawing.objects()
	for drawing in drawings:
		modified = False
		for vote in drawing.votes[:]:
			if not isinstance(vote, Vote):
				drawing.votes.remove(vote)
				modified = True
		for comment in drawing.comments[:]:
			if not isinstance(comment, Comment):
				drawing.comments.remove(comment)
				modified = True
		if modified:
			drawing.save()

	return json.dumps( { 'state': 'success' } )

# @checkDebug
# @checkSimulateSlowResponse
# def getDrafts(request, cityName=None):

# 	if not request.user.is_authenticated():
# 		return json.dumps({'state': 'not_logged_in'})

# 	city = getCity(cityName)
# 	if not city:
# 		return json.dumps( { 'state': 'error', 'message': 'The city does not exist', 'code': 'CITY_DOES_NOT_EXIST' } )

# 	paths = Path.objects(owner=request.user.username, isDraft=True, city=str(city.pk))
# 	items = []

# 	for path in paths:
# 		items.append(path.to_json())

# 	return  json.dumps( {'state': 'success', 'items': items } )

# --- votes --- #

def computeVotes(drawing):
	nPositiveVotes = 0
	nNegativeVotes = 0
	for vote in drawing.votes:
		if isinstance(vote, Vote) and vote.author.emailConfirmed:
			if vote.positive:
				nPositiveVotes += 1
			else:
				nNegativeVotes += 1
	return (nPositiveVotes, nNegativeVotes)

def isDrawingValidated(city, nPositiveVotes, nNegativeVotes):
	return nPositiveVotes >= city.positiveVoteThreshold and nNegativeVotes < city.negativeVoteThreshold

def isDrawingRejected(city, nNegativeVotes):
	return nNegativeVotes >= city.negativeVoteThreshold

def isTileValidated(city, nPositiveVotes, nNegativeVotes):
	return nPositiveVotes >= city.positiveVoteThresholdTile and nNegativeVotes < city.negativeVoteThresholdTile

def isTileRejected(city, nNegativeVotes):
	return nNegativeVotes >= city.negativeVoteThresholdTile

def updateDrawingState(drawingPk=None, drawing=None, unflag=False):
	if not drawing and not drawingPk:
		return

	if not drawing:
		try:
			drawing = Drawing.objects.get(pk=drawingPk)
		except Drawing.DoesNotExist:
			return

	city = None
	try:
		city = City.objects.get(pk=drawing.city)
		if city.finished:
			return
	except City.DoesNotExist:
		return

	if isDrawingStatusValidated(drawing):
		# send_mail('[Comme un dessein] WARNING updateDrawingState', u'updateDrawingState trying to update status while validated ' + str(drawing.pk), 'contact@commeundessein.co', ['idlv.contact@gmail.com'], fail_silently=True)
		return

	(nPositiveVotes, nNegativeVotes) = computeVotes(drawing)

	drawingStateChanged = False

	actionName = u''
	if isDrawingValidated(city, nPositiveVotes, nNegativeVotes) and drawing.status == 'pending':
		drawing.status = 'validated'
		actionName = u'validé'
		drawing.save()
		drawingStateChanged = True
	elif isDrawingRejected(city, nNegativeVotes) and drawing.status == 'pending':
		# drawingWasActive = drawing.status == 'pending' or drawing.status == 'validated' or drawing.status == 'created' or drawing.status == 'drawing'
		drawing.status = 'rejected'
		actionName = u'rejeté'
		drawing.save()
		# if drawingWasActive:
		removeDrawingFromRasters(city, drawing, 'active')
		updateRastersFromDrawing(city, drawing, 'inactive')
		drawingStateChanged = True
	elif (drawing.status == 'flagged' or drawing.status == 'flagged_pending') and unflag: 	# not accepted nor rejected: it was pending
		drawing.status = drawing.previousStatus
		actionName = u'modéré'
		drawing.save()
		layerName = 'inactive' if drawing.status == 'rejected' else 'active'
		updateRastersFromDrawing(city, drawing, layerName)
		drawingStateChanged = True

	if drawingStateChanged and actionName != '':

		try:
			userProfile = UserProfile.objects.get(username=drawing.owner)
			message = u'Votre dessin \"' + drawing.title + u'\" à été ' + actionName + u'.'
			queueEmail(userProfile, message)
		except UserProfile.DoesNotExist:
			pass

		# send_mail('[Comme un dessein] updateDrawingState', u'updateDrawingState ' + drawing.status + ' ' + str(drawing.pk), 'contact@commeundessein.co', ['idlv.contact@gmail.com'], fail_silently=True)

		# drawingValidated.send(sender=None, clientId=drawing.clientId, status=drawing.status)
		drawingChanged.send(sender=None, type='status', clientId=drawing.clientId, status=drawing.status, pk=str(drawing.pk), itemType='drawing', bounds=makeBoundsFromBox(city, drawing.box))

	return drawing

def updateTileState(tilePk=None, tile=None, unflag=False):
	if not tile and not tilePk:
		return

	if not tile:
		try:
			tile = Tile.objects.get(pk=tilePk)
		except Tile.DoesNotExist:
			return

	city = None
	try:
		city = City.objects.get(pk=tile.city)
		if city.finished:
			return
	except City.DoesNotExist:
		return

	(nPositiveVotes, nNegativeVotes) = computeVotes(tile)
	
	tileStateChanged = False

	if isTileValidated(city, nPositiveVotes, nNegativeVotes) and tile.status == 'pending':
		tile.status = 'validated'
		tile.save()
		tileStateChanged = True
	elif isTileRejected(city, nNegativeVotes) and tile.status == 'pending':
		pk = str(tile.pk)
		clientId = tile.clientId
		tile.delete()
		drawingChanged.send(sender=None, type='cancel', clientId=clientId, pk=pk, itemType='tile')
		tileStateChanged = True
		return tile
	elif (tile.status == 'flagged' or tile.status == 'flagged_pending') and unflag: 	# not accepted nor rejected: it was pending
		tile.status = tile.previousStatus
		tile.save()
		tileStateChanged = True

	if tileStateChanged:
		# send_mail('[Comme un dessein] updateDrawingState', u'updateDrawingState ' + tile.status + ' ' + str(tile.pk), 'contact@commeundessein.co', ['idlv.contact@gmail.com'], fail_silently=True)

		# tileValidated.send(sender=None, tileId=tile.clientId, status=tile.status)
		drawingChanged.send(sender=None, type='status', clientId=tile.clientId, status=tile.status, pk=str(tile.pk), itemType='tile', bounds=makeBoundsFromBox(city, tile.box))

	return tile

def isDrawingStatusValidated(drawing):
	return drawing.status == 'drawing' or drawing.status == 'drawn' or drawing.status == 'validated'

def hasOwnerDisabledEmail(owner):
	return hasattr(owner, 'disableEmail') and owner.disableEmail

@checkSimulateSlowResponse
@checkDebug
def vote(request, pk, date, positive, itemType='drawing'):

	if not request.user.is_authenticated():
		return json.dumps({'state': 'not_logged_in'})

	try:
		user = UserProfile.objects.get(username=request.user.username)
	except UserProfile.DoesNotExist:
		return json.dumps({'state': 'error', 'message': 'The user does not exist'})

	if user.banned:
		return json.dumps({'state': 'error', 'message': 'Your account has been suspended'})

	if not emailIsConfirmed(request, user):
		return json.dumps({'state': 'error', 'message': 'Please confirm your email'})

	item = None
	if itemType == 'drawing':
		try:
			item = Drawing.objects.get(pk=pk)
		except Drawing.DoesNotExist:
			return json.dumps({'state': 'error', 'message': 'Drawing does not exist', 'pk': pk})
	else:
		try:
			item = Tile.objects.get(pk=pk)
		except Drawing.DoesNotExist:
			return json.dumps({'state': 'error', 'message': 'Tile does not exist', 'pk': pk})

	try:
		city = City.objects.get(pk=item.city)
		if city.finished:
			return json.dumps({'state': 'info', 'message': "The installation is over"})
	except City.DoesNotExist:
		return json.dumps({'state': 'error', 'message': "The city does not exist"})

	if item.owner == request.user.username:
		return json.dumps({'state': 'error', 'message': 'You cannot vote for your own ' + itemType})

	if itemType == 'drawing' and isDrawingStatusValidated(item) and not user.admin:
		return json.dumps({'state': 'error', 'message': 'The drawing is already validated.'})

	# if drawing.status == 'emailNotConfirmed':
	# 	return json.dumps({'state': 'error', 'message': 'The owner of the drawing has not validated his account.'})
	
	if item.status == 'notConfirmed':
		return json.dumps({'state': 'error', 'message': 'The drawing has not been confirmed'})

	if item.status == 'draft':
		return json.dumps({'state': 'error', 'message': 'You cannot vote for a draft'})

	if itemType == 'drawings' and item.status != 'pending' or itemType == 'tile' and item.status != 'created':
		return json.dumps({'state': 'error', 'message': 'This ' + itemType + ' is not in vote state'})

	for vote in item.votes:
		try:
			if isinstance(vote, Vote) and vote.author.username == request.user.username:
				if vote.positive == positive:
					if datetime.datetime.now() - vote.date < datetime.timedelta(seconds=city.voteValidationDelay):
						return json.dumps({'state': 'error', 'message': 'You must wait before cancelling your vote', 'cancelled': False, 'voteValidationDelay': city.voteValidationDelay, 'messageOptions': ['voteValidationDelay'] })
					# cancel vote: delete vote and return:
					author = vote.author.username
					vote.author.votes.remove(vote)
					vote.author.save()
					item.votes.remove(vote)
					item.save()
					vote.delete()
					
					title = item.title if itemType == 'drawing' else str(item.number)
					drawingChanged.send(sender=None, type='cancel_vote', itemType=itemType, clientId=item.clientId, status=item.status, votes=item.votes, positive=positive, author=author, title=title)
					return json.dumps({'state': 'success', 'message': 'Your vote was cancelled', 'cancelled': True })
				else:
					# votes are different: delete vote and break (create a new one):
					vote.author.votes.remove(vote)
					vote.author.save()
					item.votes.remove(vote)
					item.save()
					vote.delete()
					break
		except DoesNotExist:
			pass

	# emailConfirmed = EmailAddress.objects.filter(user=request.user, verified=True).exists()
	# user.emailConfirmed = emailConfirmed

	vote = None
	if itemType == 'drawing':
		vote = Vote(author=user, drawing=item, positive=positive, date=datetime.datetime.fromtimestamp(date/1000.0))
	else:
		vote = Vote(author=user, tile=item, positive=positive, date=datetime.datetime.fromtimestamp(date/1000.0))

	vote.save()

	item.votes.append(vote)
	item.save()

	user.votes.append(vote)
	user.save()

	(nPositiveVotes, nNegativeVotes) = computeVotes(item)

	validates = None
	rejects = None

	if itemType == 'drawing':
		validates = isDrawingValidated(city, nPositiveVotes, nNegativeVotes)
		rejects = isDrawingRejected(city, nNegativeVotes)
	else:
		validates = isTileValidated(city, nPositiveVotes, nNegativeVotes)
		rejects = isTileRejected(city, nNegativeVotes)

	delay = city.voteValidationDelay

	votes = []
	for vote in item.votes:
		if isinstance(vote, Vote):
			try:
				votes.append( { 'vote': vote.to_json(), 'author': vote.author.username, 'authorPk': str(vote.author.pk), 'emailConfirmed': vote.author.emailConfirmed } )
			except DoesNotExist:
				pass

	title = item.title if itemType == 'drawing' else str(item.number)
	drawingChanged.send(sender=None, type='vote', itemType=itemType, clientId=item.clientId, status=item.status, votes=votes, positive=positive, author=vote.author.username, title=title)

	if validates or rejects:

		voteMinDurationDelta = datetime.timedelta(seconds=city.voteMinDuration)
		if datetime.datetime.now() - item.date < voteMinDurationDelta:
			delay = (item.date + voteMinDurationDelta - datetime.datetime.now()).total_seconds()

		t = None
		
		if itemType == 'drawing':
			t = Timer(delay, updateDrawingState, args=[pk])
		else:
			t = Timer(delay, updateTileState, args=[pk])

		t.start()
	
	owner = None
	try:
		owner = User.objects.get(username=item.owner)
	except User.DoesNotExist:
		print("Owner not found")
	
	if owner and not hasOwnerDisabledEmail(owner):
		forAgainst = 'pour'
		if not positive:
			forAgainst = 'contre'
		# send_mail('[Espero]' + request.user.username + u' a voté ' + forAgainst + u' votre dessin !', request.user.username + u' a voté ' + forAgainst + u' votre dessin \"' + drawing.title + u'\" sur Comme un Dessein !\n\nVisitez le resultat sur https://commeundessein.co/drawing-'+str(drawing.pk)+u'\nMerci d\'avoir participé à Comme un Dessein,\n\nPour ne plus recevoir de notifications, allez sur https://commeundessein.co/email/desactivation/\n\nLe collectif Indien dans la ville\nhttp://idlv.co/\nidlv.contact@gmail.com', 'contact@commeundessein.co', [owner.email], fail_silently=True)
		title = item.title if itemType == 'drawing' else str(item.number)
		itemName = 'dessin' if itemType == 'drawing' else 'case'
		applicationName = 'Comme un dessein' if settings.APPLICATION == 'COMME_UN_DESSEIN' else 'Espero'
		siteDomain = shortcuts.get_current_site(request).domain
		message = u'Quelqu\'un a voté ' + forAgainst + u' votre ' + itemName + u' \"' + title + u'\" sur ' + applicationName + u' !'
		if itemType == 'drawing':
			message += u' Retrouvez votre dessin sur https://' + siteDomain + '/drawing-'+str(item.pk)
		queueEmail(user, message)
		# send_mail(u'[Espero] Quelqu\'un a voté ' + forAgainst + u' votre dessin !', u'Quelqu\'un a voté ' + forAgainst + u' votre dessin \"' + title + u'\" sur Comme un Dessein !\n\nVisitez le resultat sur https://commeundessein.co/drawing-'+str(item.pk)+u'\nMerci d\'avoir participé à Comme un Dessein,\n\nPour ne plus recevoir de notifications, allez sur https://commeundessein.co/email/desactivation/\n\nLe collectif Indien dans la ville\nhttp://idlv.co/\nidlv.contact@gmail.com', 'contact@commeundessein.co', [owner.email], fail_silently=True)

	return json.dumps( {'state': 'success', 'owner': request.user.username, 'drawingPk':str(item.pk), 'votePk':str(vote.pk), 'positive': vote.positive, 'validates': validates, 'rejects': rejects, 'votes': votes, 'delay': delay, 'emailConfirmed': user.emailConfirmed } )

# --- Get Next Drawing To Be Drawn / Set Drawing Drawn --- #

# @checkDebug
# def loadItems(request, itemType, pks):

# 	if itemType not in ['Path', 'Div', 'Box', 'AreaToUpdate', 'Drawing']:
# 		return json.dumps({'state': 'error', 'message': 'Can only load Paths, Divs, Boxs, AreaToUpdates or Drawings.'})

# 	itemsQuerySet = globals()[itemType].objects(pk__in=pks)

# 	items = []
# 	for item in itemsQuerySet:
# 		items.append(item.to_json())

# 	return json.dumps( {'state': 'success', 'items': items } )

@checkSimulateSlowResponse
@checkDebug
def addComment(request, itemPk, comment, date, itemType, insertAfter=None):
	if not request.user.is_authenticated():
		return json.dumps({'state': 'not_logged_in'})

	if not emailIsConfirmed(request):
		return json.dumps({'state': 'error', 'message': 'Please confirm your email'})

	item = None
	if itemType == 'drawing':
		try:
			item = Drawing.objects.get(pk=itemPk)
		except Drawing.DoesNotExist:
			return json.dumps({'state': 'error', 'message': 'Drawing does not exist.', 'pk': itemPk})

		if item.status == 'draft' or item.status == 'emailNotConfirmed' or item.status == 'notConfirmed':
			return json.dumps({'state': 'error', 'message': 'Cannot comment on this drawing.'})
	else:
		try:
			item = Tile.objects.get(pk=itemPk)
		except Tile.DoesNotExist:
			return json.dumps({'state': 'error', 'message': 'Element does not exist'})

	user = None

	try:
		user = UserProfile.objects.get(username=request.user.username)
	except UserProfile.DoesNotExist:
		return json.dumps({'state': 'error', 'message': 'The user profile does not exist.'})
	
	if user.banned:
		return json.dumps({'state': 'error', 'message': 'Your account has been suspended'})

	emailConfirmed = EmailAddress.objects.filter(user=request.user, verified=True).exists()
	user.emailConfirmed = emailConfirmed

	if itemType == 'drawing':
		c = Comment(author=user, drawing=item, text=comment, date=datetime.datetime.fromtimestamp(date/1000.0))
	else:
		c = Comment(author=user, tile=item, text=comment, date=datetime.datetime.fromtimestamp(date/1000.0))
	c.save()

	item.comments.append(c)
	item.save()

	user.comments.append(c)
	user.save()
	
	owner = None
	try:
		owner = User.objects.get(username=item.owner)
	except User.DoesNotExist:
		print("Owner not found")
	if owner and not hasOwnerDisabledEmail(owner):

		title = item.title if itemType == 'drawing' else str(item.number)
		itemName = 'dessin' if itemType == 'drawing' else 'case'
		applicationName = 'Comme un dessein' if settings.APPLICATION == 'COMME_UN_DESSEIN' else 'Espero'
		siteDomain = shortcuts.get_current_site(request).domain
		message = request.user.username + u' a commenté votre ' + itemName + u' sur ' + applicationName + u' !'
		if itemType == 'drawing':
			message += u' Retrouvez votre dessin sur https://' + siteDomain + '/drawing-'+str(item.pk)
		queueEmail(user, message)

		# if itemType == 'drawing':
		# 	send_mail('[Espero] ' + request.user.username + u' a commenté votre dessin !', request.user.username + u' a commenté votre dessin \"' + item.title + u'\" sur Comme un Dessein !\n\nVisitez le resultat sur https://commeundessein.co/drawing-'+str(item.pk)+u'\nMerci d\'avoir participé à Espero,\nLe collectif Indien dans la ville\nhttp://idlv.co/\nidlv.contact@gmail.com', 'contact@commeundessein.co', [owner.email], fail_silently=True)
		# else:
		# 	send_mail('[Espero] ' + request.user.username + u' a commenté votre case !', request.user.username + u' a commenté votre case \"' + str(item.number) + u'\" sur Comme un Dessein !\n\nVisitez le resultat sur https://commeundessein.co/tile-'+str(item.pk)+u'\nMerci d\'avoir participé à Espero,\nLe collectif Indien dans la ville\nhttp://idlv.co/\nidlv.contact@gmail.com', 'contact@commeundessein.co', [owner.email], fail_silently=True)

	drawingChanged.send(sender=None, type='addComment', author=request.user.username, clientId=item.clientId, pk=str(item.pk), itemType=itemType, comment=c.text, commentPk= str(c.pk), date=unix_time_millis(c.date), itemPk= str(item.pk), insertAfter=insertAfter)

	return json.dumps( {'state': 'success', 'author': request.user.username, 'itemPk':str(item.pk), 'clientId': item.clientId, 'commentPk': str(c.pk), 'comment': c.to_json(), 'emailConfirmed': emailConfirmed, 'itemType': itemType } )

@checkSimulateSlowResponse
@checkDebug
def modifyComment(request, commentPk, comment):
	if not request.user.is_authenticated():
		return json.dumps({'state': 'not_logged_in'})
	
	try:
		user = UserProfile.objects.get(username=request.user.username)
	except UserProfile.DoesNotExist:
		return json.dumps({'state': 'error', 'message': 'The user profile does not exist.'})
	
	if user.banned:
		return json.dumps({'state': 'error', 'message': 'Your account has been suspended'})

	if not emailIsConfirmed(request, user):
		return json.dumps({'state': 'error', 'message': 'Please confirm your email'})

	c = None
	try:
		c = Comment.objects.get(pk=commentPk)
	except Comment.DoesNotExist:
		return json.dumps({'state': 'error', 'message': 'Comment does not exist.', 'pk': commentPk})

	if request.user.username != c.author.username and not isAdmin(request.user):
		return json.dumps({'state': 'error', 'message': 'User is not the author of the comment.'})

	c.text = comment
	c.save()

	itemPk = str(c.drawing.pk) if c.drawing else str(c.tile.pk)
	itemType = 'drawing' if c.drawing else 'tile'
	clientId = c.drawing.clientId if c.drawing else c.tile.clientId

	drawingChanged.send(sender=None, type='modifyComment', clientId=clientId, itemType=itemType, comment=c.text, commentPk=commentPk, itemPk=itemPk)

	return json.dumps( {'state': 'success', 'comment': comment, 'commentPk': str(c.pk), 'itemPk': itemPk, 'clientId': clientId, 'itemType': itemType } )

@checkSimulateSlowResponse
@checkDebug
def deleteComment(request, commentPk):
	if not request.user.is_authenticated():
		return json.dumps({'state': 'not_logged_in'})

	try:
		user = UserProfile.objects.get(username=request.user.username)
	except UserProfile.DoesNotExist:
		return json.dumps({'state': 'error', 'message': 'The user profile does not exist.'})
	
	if user.banned:
		return json.dumps({'state': 'error', 'message': 'Your account has been suspended'})

	if not emailIsConfirmed(request, user):
		return json.dumps({'state': 'error', 'message': 'Please confirm your email'})

	c = None
	try:
		c = Comment.objects.get(pk=commentPk)
	except Comment.DoesNotExist:
		return json.dumps({'state': 'error', 'message': 'Comment does not exist.', 'pk': commentPk})

	if request.user.username != c.author.username and not isAdmin(request.user):
		return json.dumps({'state': 'error', 'message': 'User is not the author of the comment.'})

	if c.drawing:
		c.drawing.comments.remove(c)
		c.drawing.save()
	elif c.tile:
		c.tile.comments.remove(c)
		c.tile.save()
	c.author.comments.remove(c)
	c.author.save()
	c.delete()
	
	itemPk = str(c.drawing.pk) if c.drawing else str(c.tile.pk)
	itemType = 'drawing' if c.drawing else 'tile'
	clientId = c.drawing.clientId if c.drawing else c.tile.clientId
	
	drawingChanged.send(sender=None, type='deleteComment', clientId=clientId, itemType=itemType, comment=c.text, commentPk=commentPk, itemPk=itemPk)

	return json.dumps( {'state': 'success', 'commentPk': str(c.pk), 'itemPk': itemPk, 'clientId': clientId, 'itemType': itemType } )


@checkSimulateSlowResponse
@checkDebug
def loadItems(request, itemsToLoad):
	items = []

	for itemToLoad in itemsToLoad:
		itemType = itemToLoad['itemType']
		pks = itemToLoad['pks']
		
		if itemType not in ['Path', 'Div', 'Box', 'AreaToUpdate', 'Drawing']:
			return json.dumps({'state': 'error', 'message': 'Can only load Paths, Divs, Boxs, AreaToUpdates or Drawings.'})

		itemsQuerySet = globals()[itemType].objects(pk__in=pks)
	
		for item in itemsQuerySet:
			items.append(item.to_json())

	return json.dumps( {'state': 'success', 'items': items } )


@checkDebug
def getNextValidatedDrawing(request, cityName, secret):
	
	if secret != TIPIBOT_PASSWORD:
		return json.dumps({'state': 'error', 'message': 'Secret invalid.'})

	city = getCity(cityName)
	if not city:
		return json.dumps( { 'state': 'error', 'message': 'The city does not exist', 'code': 'CITY_DOES_NOT_EXIST' } )
	
	drawings = Drawing.objects(status='validated', city=str(city.pk))

	drawingNames = []

	for drawing in drawings:
		for vote in drawing.votes:

			try:
				if isinstance(vote, Vote) and vote.author.admin:

					if drawing is not None:
						
						drawingNames.append(drawing.title)

						# get all path of the first drawing
						paths = []
						# for path in drawing.paths:
						# 	paths.append(path.to_json())
						for path in drawing.pathList:
							pJSON = json.loads(path)
							paths.append(json.dumps({'data': json.dumps({'points': pJSON['points'], 'data': pJSON['data'], 'planet': {'x': 0, 'y': 0}}), '_id': {'$oid': None} }))

						return  json.dumps( {'state': 'success', 'pk': str(drawing.pk), 'items': paths, 'svg': drawing.svg } )
			except DoesNotExist:
				pass
		
	if len(drawings) > 0:
		drawingChanged.send(sender=None, type='adminMessage', title='Drawing validated but no moderator', description='Drawing names: ' + json.dumps(drawingNames))

	#	 send_mail('[Comme un dessein] Drawing validated but no moderator voted for it', '[Comme un dessein] One or more drawing has been validated but no moderator voted for it', 'contact@commeundessein.co', ['idlv.contact@gmail.com'], fail_silently=True)
	return  json.dumps( {'state': 'success', 'message': 'no path' } )


@checkSimulateSlowResponse
@checkDebug
def setDrawingStatus(request, pk, status):

	if not isAdmin(request.user):
		return json.dumps( { 'state': 'error', 'message': 'You must be administrator to move a drawing.' } )
	
	try:
		drawing = Drawing.objects.get(pk=pk)
	except Drawing.DoesNotExist:
		return json.dumps({'state': 'error', 'message': 'Drawing does not exist.', 'pk': pk})
	
	drawing.status = status
	drawing.save()

	# send_mail('[Comme un dessein] Set drawing status', u'Set drawing status ' + status + ' ' + str(drawing.pk), 'contact@commeundessein.co', ['idlv.contact@gmail.com'], fail_silently=True)

	return json.dumps( {'state': 'success', 'message': 'Drawing status successfully updated.', 'pk': pk, 'status': status } )

@checkDebug
def setDrawingStatusDrawn(request, pk, secret):
	if secret != TIPIBOT_PASSWORD:
		return json.dumps({'state': 'error', 'message': 'Secret invalid.'})

	try:
		drawing = Drawing.objects.get(pk=pk)
	except Drawing.DoesNotExist:
		return json.dumps({'state': 'error', 'message': 'Drawing does not exist.', 'pk': pk})
	
	drawing.status = 'drawn'
	drawing.save()


	try:
		userProfile = UserProfile.objects.get(username=drawing.owner)
		message = u'Le Tipibot a terminé de dessiner votre dessin \"' + drawing.title + u'\" !'
		queueEmail(userProfile, message)
	except UserProfile.DoesNotExist:
		pass

	# send_mail('[Comme un dessein] Set drawing status drawn', u'Set drawing status drawn ' + str(drawing.pk), 'contact@commeundessein.co', ['idlv.contact@gmail.com'], fail_silently=True)

	# drawingValidated.send(sender=None, clientId=drawing.clientId, status=drawing.status)
	drawingChanged.send(sender=None, type='status', clientId=drawing.clientId, status=drawing.status, pk=str(drawing.pk))

	return json.dumps( {'state': 'success', 'message': 'Drawing status successfully updated.', 'pk': pk } )


# @checkSimulateSlowResponse
# @checkDebug
# def setDrawingToCity(request, pk, cityName):
	
# 	if not isAdmin(request.user):
# 		return json.dumps( { 'state': 'error', 'message': 'You must be administrator to move a drawing.' } )
	
# 	city = getCity(cityName)
# 	if not city:
# 		return json.dumps( { 'state': 'error', 'message': 'The city does not exist', 'code': 'CITY_DOES_NOT_EXIST' } )

# 	try:
# 		drawing = Drawing.objects.get(pk=pk)
# 	except Drawing.DoesNotExist:
# 		return json.dumps({'state': 'error', 'message': 'Element does not exist'})
	
# 	drawing.city = str(city.pk)
# 	drawing.save()

# 	for path in drawing.paths:
# 		if isinstance(path, Path):
# 			path.city = drawing.city
# 			path.save()

# 	return json.dumps( {'state': 'success' } )

def floorToMultiple(x, m):
	return int(floor(x/float(m))*m)

# warning: difference between ceil(x/m)*m and floor(x/m)*(m+1)
def ceilToMultiple(x, m):
	return int(ceil(x/float(m))*m)

def intersectRectangles(l1, t1, r1, b1, l2, t2, r2, b2):
	l = max(l1, l2)
	t = max(t1, t2)
	r = min(r1, r2)
	b = min(b1, b2)
	return (l, t, r, b)

def pasteImage2onImage1(image1, image2, box1, box2, scale = 1):

	union = intersectRectangles(box1[0], box1[1], box1[2], box1[3], box2[0], box2[1], box2[2], box2[3])

	subImage2 = image2.crop(( int( ( union[0] - box2[0] ) / scale ) , int( ( union[1] - box2[1] ) / scale) , int( ( union[2] -  box2[0] ) / scale), int( ( union[3] -  box2[1] ) / scale) ))
	
	image1.paste(subImage2, ( int( ( union[0] - box1[0] ) / scale ) , int( (union[1] - box1[1] ) / scale) ))

	return image1

def blendImages(image1, image2, box1, box2, scale = 1, overwrite = False):
	if overwrite:
		return pasteImage2onImage1(image1, image2, box1, box2, scale)

	union = intersectRectangles(box1[0], box1[1], box1[2], box1[3], box2[0], box2[1], box2[2], box2[3])

	subImage1 = image1.crop(( int( ( union[0] - box1[0] ) / scale ) , int( ( union[1] - box1[1] ) / scale) , int( ( union[2] -  box1[0] ) / scale), int( ( union[3] -  box1[1] ) / scale) ))
	subImage2 = image2.crop(( int( ( union[0] - box2[0] ) / scale ) , int( ( union[1] - box2[1] ) / scale) , int( ( union[2] -  box2[0] ) / scale), int( ( union[3] -  box2[1] ) / scale) ))

	alpha_composite = Image.alpha_composite(subImage1, subImage2)
	
	image1.paste(alpha_composite, ( int( ( union[0] - box1[0] ) / scale ) , int( (union[1] - box1[1] ) / scale) ))

	return alpha_composite

def boundsOverlap(b1, b2):
	ileft = max(b1['x'], b2['x'])
	itop = max(b1['y'], b2['y'])
	iright = min(b1['x'] + b1['width'], b2['x'] + b2['width'])
	ibottom = min(b1['y'] + b1['height'], b2['y'] + b2['height'])

	if (iright-ileft) <= 0 or (ibottom-itop) <= 0 or (iright-ileft) * (ibottom-itop) <= 0.001:
		return False

	return True

def boundsToBoxList(bounds):
	return [bounds['x'], bounds['y'], bounds['x'] + bounds['width'], bounds['y'] + bounds['height']]

def removeDrawingFromRasters(city, drawing, rasterType = 'active'):
	
	drawingBounds = makeBoundsFromBox(city, drawing.box)

	imageX = drawingBounds['x']
	imageY = drawingBounds['y']
	imageWidth = drawingBounds['width']
	imageHeight = drawingBounds['height']
	
	scaleFactor = 4

	pixelRatio = pow(scaleFactor, 3)

	l = int(floor(imageX / pixelRatio) * pixelRatio)
	t = int(floor(imageY / pixelRatio) * pixelRatio)
	r = int(ceil( (imageX + imageWidth) / pixelRatio) * pixelRatio)
	b = int(ceil( (imageY + imageHeight) / pixelRatio) * pixelRatio)

	imageWidth = r - l
	imageHeight = b - t
	
	newImage = Image.new("RGBA", (imageWidth, imageHeight), (255, 255, 255, 0))

	imageX = l
	imageY = t

	box = makeBoxFromBounds(city, {'x': imageX, 'y': imageY, 'width': imageWidth, 'height': imageHeight})

	statuses = ['pending', 'drawing', 'drawn', 'validated'] if rasterType == 'active' else ['rejected']
	# overlappingDrawings = Drawing.objects(pk__ne=drawing.pk, city=drawing.city, planetX=drawing.planetX, planetY=drawing.planetY, status__in=statuses, box__geo_within_box=geometry).order_by('+date')
	overlappingDrawings = Drawing.objects(pk__ne=drawing.pk, city=drawing.city, planetX=drawing.planetX, planetY=drawing.planetY, status__in=statuses, box__geo_intersects=box).order_by('+date')

	drawingBounds['x'] = l
	drawingBounds['y'] = t
	drawingBounds['width'] = r - l
	drawingBounds['height'] = b - t

	for overlappingDrawing in overlappingDrawings:

		dBounds = makeBoundsFromBox(city, overlappingDrawing.box)

		if boundsOverlap(drawingBounds, dBounds):

			imageName = 'Wetu/static/drawings/' + str(overlappingDrawing.pk) + '.png'
			try:
				dImage = Image.open(imageName)

				(clampedImage, dBounds['x'], dBounds['y'], dBounds['width'], dBounds['height']) = createClampedImage(dImage, dBounds)
				
				blendImages(newImage, clampedImage, boundsToBoxList(drawingBounds), boundsToBoxList(dBounds))

			except IOError:
				pass

	updateRastersFromImage(newImage, { 'x': imageX, 'y': imageY, 'width': imageWidth, 'height': imageHeight }, city, True, rasterType)

	return

def updateRasters(imageData, bounds, city):

	try:
		image = Image.open(StringIO.StringIO(imageData))				# Pillow version
	except IOError:
		return { 'state': 'error', 'message': 'impossible to read image.'}

	return updateRastersFromImage(image, bounds, city)

def updateRastersFromDrawing(city, drawing, rasterType = 'active'):

	try:
		image = Image.open('Wetu/static/drawings/'+str(drawing.pk)+'.png')
	except IOError:
		return { 'state': 'error', 'message': 'impossible to read the drawing image.'}

	return updateRastersFromImage(image, makeBoundsFromBox(city, drawing.box), city, False, rasterType)

def createClampedImage(image, bounds, scaleFactor=4):

	imageX = int(bounds['x'])
	imageY = int(bounds['y'])
	imageWidth = int(image.size[0])
	imageHeight = int(image.size[1])

	pixelRatio = pow(scaleFactor, 3)

	l = int(floor(imageX / pixelRatio) * pixelRatio)
	t = int(floor(imageY / pixelRatio) * pixelRatio)
	r = int(ceil( (imageX + imageWidth) / pixelRatio) * pixelRatio)
	b = int(ceil( (imageY + imageHeight) / pixelRatio) * pixelRatio)

	imageWidth = r - l
	imageHeight = b - t
	
	clampedImage = Image.new("RGBA", (imageWidth, imageHeight))
	clampedImage.paste(image, ( imageX - l, imageY - t ) )

	imageX = l
	imageY = t

	return (clampedImage, imageX, imageY, imageWidth, imageHeight)

def updateRastersFromImage(image, bounds, city, overwrite = False, rasterType = 'active'):

	# find top, left, bottom and right positions of the area in the quantized space
	
	scaleFactor = 4

	(clampedImage, imageX, imageY, imageWidth, imageHeight) = createClampedImage(image, bounds, scaleFactor)

	for n in range(0, 4):

		scale = pow(scaleFactor, n)
		nPixelsPerTile = 1000 * scale

		l = int(floor(imageX / nPixelsPerTile))
		t = int(floor(imageY / nPixelsPerTile))
		r = int(floor( (imageX + imageWidth) / nPixelsPerTile) + 1)
		b = int(floor( (imageY + imageHeight) / nPixelsPerTile) + 1)

		for xi in range(l, r):
			for yi in range(t, b):
				
				rasterName = 'Wetu/static/rasters/' + city.name + '/' + rasterType + '/zoom' + str(n) + '/' + str(xi) + ',' + str(yi) + '.png'
				rasterDir = os.path.abspath(os.path.join(rasterName, os.pardir))
				if not os.path.exists(rasterDir):
					os.makedirs(rasterDir)

				try:
					# raster = Image(filename=rasterName)  		# Wand version
					raster = Image.open(rasterName)				# Pillow version
				except IOError:
					# raster = Image(width=1000, height=1000) 	# Wand version
					raster = Image.new("RGBA", (1000, 1000)) 	# Pillow version

				x = xi * nPixelsPerTile
				y = yi * nPixelsPerTile

				blendImages(raster, clampedImage, [x, y, x + nPixelsPerTile, y + nPixelsPerTile], [imageX, imageY, imageX + imageWidth, imageY + imageHeight], scale, overwrite)
				
				raster.save(rasterName)
				raster.close()

		if n < 3:
			clampedImage = clampedImage.resize((max(0, clampedImage.size[0]/scaleFactor), max(0, clampedImage.size[1]/scaleFactor)), Image.LANCZOS)

	clampedImage.close()
	image.close()

	return { 'state': 'success' }

# --- images --- #

# @dajaxice_register
@checkSimulateSlowResponse
@checkDebug
def saveImage(request, image):

	imageData = re.search(r'base64,(.*)', image).group(1)

	imagePath = 'media/images/' + request.user.username + '/'

	try:
		os.mkdir(imagePath)
	except OSError as exception:
		if exception.errno != errno.EEXIST:
			raise

	date = str(datetime.datetime.now()).replace (" ", "_").replace(":", ".")
	imageName = imagePath + date + ".png"

	output = open(imageName, 'wb')
	output.write(imageData.decode('base64'))
	output.close()

	# to read the image
	# inputfile = open(imageName, 'rb')
	# imageData = inputfile.read().encode('base64')
	# inputfile.close()
	# return json.dumps( { 'image': imageData, 'url': imageName } )

	return json.dumps( { 'url': imageName } )

@checkSimulateSlowResponse
@checkDebug
def submitTilePhoto(request, pk, imageName, dataURL):
	
	if not request.user.is_authenticated():
		return json.dumps({'state': 'not_logged_in'})

	try:	
		tile = Tile.objects.get(pk=pk)
	except Tile.DoesNotExist:
		return json.dumps({'state': 'error', 'message': 'Element does not exist'})

	try:
		city = City.objects.get(pk=tile.city)
		if city.finished:
			return json.dumps({'state': 'info', 'message': "The installation is over"})
	except City.DoesNotExist:
		return json.dumps({'state': 'error', 'message': "The city does not exist"})

	try:
		user = UserProfile.objects.get(username=request.user.username)
	except UserProfile.DoesNotExist:
		return json.dumps({'state': 'error', 'message': 'The user profile does not exist.'})
	
	if user.banned:
		return json.dumps({'state': 'error', 'message': 'Your account has been suspended'})

	if request.user.username != tile.owner and not user.admin:
		return json.dumps({'state': 'error', 'message': 'Not owner of tile'})

	if tile.status != 'pending':
		return json.dumps({'state': 'error', 'message': 'The tile is not in pending state'})

	imgstr = re.search(r'base64,(.*)', dataURL).group(1)
	output = open('Wetu/media/images/'+imageName+'.jpg', 'wb')
	imageData = imgstr.decode('base64')
	output.write(imageData)
	output.close()

	tile.photoURL = imageName+'.jpg'
	tile.status = 'created'
	tile.dueDate = datetime.datetime.now()
	tile.save()

	drawingChanged.send(sender=None, type='status', clientId=tile.clientId, status=tile.status, pk=str(tile.pk), city=city.name, itemType='tile', photoURL=tile.photoURL, bounds=makeBoundsFromBox(city, tile.box))

	return json.dumps( { 'photoURL': tile.photoURL, 'x': tile.x, 'y': tile.y, 'status': tile.status } )	

# @checkDebug
# @checkSimulateSlowResponse
# def uploadImage(request, imageName, dataURL):

# 	imgstr = re.search(r'base64,(.*)', dataURL).group(1)
# 	output = open('Wetu/media/images/'+imageName+'.jpg', 'wb')
# 	imageData = imgstr.decode('base64')
# 	output.write(imageData)
# 	output.close()

# 	return json.dumps( { 'url': imageName } )

EMAIL_REGEX = re.compile(r"[^@]+@[^@]+\.[^@]+")

def updateAnswerCounts(question, questions, answerValues, removeValues=False):

	while len(question.answerCounts) < len(question.values):
		question.answerCounts.append(0)
	valueIndex = 0
	for value in question.values:
		if value in answerValues:
			question.answerCounts[valueIndex] += 1 if not removeValues else -1
		valueIndex += 1

	questions.append(question)
	return



@checkDebug
def submitSurvey(request, answers, email):

	answerObjects = []
	questions = []

	alreadyAnswered = False

	if not EMAIL_REGEX.match(email):
			return json.dumps({"status": "error", "message": "Your email is invalid"})

	printSize = 0
	printSizes = {
		'0': 0,
		'50cm': 0.25,
		'1m': 1,
		'2m': 2,
		'5m': 5,
		'10m': 10
	}

	for questionName, answerValues in answers.iteritems():
		
		try:
			question = Question.objects.get(name=questionName)
		except Question.DoesNotExist:
			return json.dumps({"status": "error", "message": "Some answers are not valid"})

		answersAreValid = all(answerValue in question.values for answerValue in answerValues)
		if answersAreValid:
			try:
				existingAnswer = Answer.objects.get(question=question, author=email)
				updateAnswerCounts(question, questions, existingAnswer.values, True)
				existingAnswer.values = answerValues
				updateAnswerCounts(question, questions, answerValues)
				existingAnswer.save()
				alreadyAnswered = True
			except Answer.DoesNotExist:
				answer = Answer(question=question, author=email, values=answerValues)
				updateAnswerCounts(question, questions, answerValues)
				answerObjects.append(answer)
				if questionName == 'print-size':
					printSize = printSizes[answerValues[0]]
		else:
			return json.dumps({"status": "error", "message": "Some answers are not valid"})

	for answer in answerObjects:
		answer.save()

	for question in questions:
		question.save()

	if not alreadyAnswered:
		try:
			city = City.objects.get(name='rennes')
			city.nParticipants += 1
			city.squareMeters += printSize
			city.save()
		except City.DoesNotExist:
			pass

	return json.dumps({"message": "Your participation was successfully updated" if alreadyAnswered else "success"})

def getSurveyResults(request):

	questions = Question.objects.all().order_by('order')

	results = []
	for question in questions:
		results.append({ 'name': question.name, 'values': question.values, 'answers': question.answerCounts, 'text': question.text, 'legends': question.legends })

	return json.dumps( results )

def projectToGeoJSON2(city, bounds):
	x = planetWidth * bounds['x'] / float(city.width)
	y = planetHeight * bounds['y'] / float(city.height)
	width = planetWidth * bounds['width'] / float(city.width)
	height = planetHeight * bounds['height'] / float(city.height)
	x = min(max(x, -planetWidth/2), planetWidth/2)
	y = min(max(y, -planetHeight/2), planetHeight/2)
	if x + width > planetWidth/2:
		width = planetWidth/2 - x
	if y + height > planetHeight/2:
		height = planetHeight/2 - y
	return { 'x': x, 'y': y, 'width': width, 'height': height }

def makeBox2(left, top, right, bottom):
	return { "type": "Polygon", "coordinates": [ [ [left, top], [right, top], [right, bottom], [left, bottom], [left, top] ] ] }

def makeBoxFromBounds2(city, bounds):
	bounds = projectToGeoJSON2(city, bounds)
	return makeBox2(bounds['x'], bounds['y'], bounds['x'] + bounds['width'], bounds['y'] + bounds['height'])


def importObject(path, name, Object):

	file = open(path + name + '.json', 'r')
	objectsString = file.read()
	objectsJson = json.loads(objectsString)
	for objectJson in objectsJson:
		objects = Object.from_json(json.dumps(objectJson))
		objects.save(force_insert=True)
	return

def importDB(path):

	importObject(path, 'users', UserProfile)
	importObject(path, 'cities', City)
	importObject(path, 'votes', Vote)
	importObject(path, 'comments', Comment)

	file = open(path + 'drawings.json', 'r')
	drawings = json.loads(file.read())
	n = 0
	for drawing in drawings:

		try:
			city = City.objects.get(pk=drawing['city'])
		except City.DoesNotExist:
			continue

		try:
			drawing = Drawing.objects.get(pk=drawing['_id']['$oid'])
			drawing['box'] = makeBoxFromBounds2(city, {'x': 0, 'y': 0, 'width': 10, 'height': 10})
			drawing.save()
			continue
		except Drawing.DoesNotExist:
			pass


		drawing['previousStatus'] = 'unknown'
		if 'bounds' in drawing:
			del drawing['bounds']
		xMin = None
		xMax = None
		yMin = None
		yMax = None
		
		if 'pathList' not in drawing:
			continue

		pathList = drawing['pathList']
		newPathList = []
		m = 0
		for pathString in pathList:
			# for point in path['points']:
			points = json.loads(pathString)
			# for i in range(0, len(points), 4):
			# 	if xMin == None or xMin > points[i]['x']:
			# 		xMin = points[i]['x']
			# 	if xMax == None or xMax < points[i]['x']:
			# 		xMax = points[i]['x']
				
			# 	if yMin == None or yMin > points[i]['y']:
			# 		yMin = points[i]['y']
			# 	if yMax == None or yMax < points[i]['y']:
			# 		yMax = points[i]['y']

			newPathList.append(json.dumps({'points': points, 'data': { 'strokeColor': 'black' } }))
			m += 1
		
		n += 1

		drawing['pathList'] = newPathList
		n += 1

		if drawing['status'] not in ['draft', 'pending', 'rejected', 'validated', 'drawing', 'drawn', 'flagged', 'flagged_pending']:
			print('Drawing status is not valid: ' + drawing['status'] + ', setting to rejected')
			drawing['status'] = 'rejected'

		# xMin *= 1000
		# yMin *= 1000
		# xMax *= 1000
		# yMax *= 1000

		# drawing['box'] = makeBoxFromBounds2(city, {'x': xMin, 'y': yMin, 'width': xMax-xMin, 'height': yMax-yMin})
		drawing['box'] = makeBoxFromBounds2(city, {'x': 0, 'y': 0, 'width': 10, 'height': 10})

		try:
			do = Drawing.from_json(json.dumps(drawing))
			do.save(force_insert=True)
		except NotUniqueError:
			continue

	return

# def autoTraceMultiChannels(request, png, colors):

# 	if not request.user.is_authenticated():
# 		return json.dumps({'state': 'not_logged_in'})
	
# 	try:
# 		userProfile = UserProfile.objects.get(username=request.user.username)
# 	except UserProfile.DoesNotExist:
# 		return json.dumps( { 'status': 'error', 'message': 'The user profile does not exist.' } )
	
# 	if userProfile.banned:
# 		return json.dumps({'state': 'error', 'message': 'Your account has been suspended'})

# 	if not emailIsConfirmed(request, userProfile):
# 		return json.dumps({'state': 'error', 'message': 'Please confirm your email'})

# 	imgstr = re.search(r'base64,(.*)', png).group(1)
# 	imageData = imgstr.decode('base64')
	
# 	try:
# 		image = Image.open(StringIO.StringIO(imageData))
# 		# image = image.convert('L', None, Image.FLOYDSTEINBERG) # Binarize image: not necessary if options --color-count 1 is specified to autotrace
# 		# hsv = image.convert('HSV') # WARNING: NOT WORKING, NOT SUPPORTED!!
# 		# h, s, v = hsv.split()
# 		# imageGrayscale = ImageChops.darker(ImageChops.invert(s), v)
# 		# blurredImage = imageGrayscale.filter(ImageFilter.GaussianBlur(15))
# 		# subtraction = ImageChops.subtract(imageGrayscale, blurredImage)
# 		# finalImage = subtraction.point(lambda i: 255 if i < 12 else 0)
		
# 		# In the future: Convert to closest colors

# 		r = np.arange(image.size[1])
# 		r2 = np.repeat(r[:, np.newaxis], image.size[0], axis=1)
# 		mask = np.where(r2 % 6 == 0, 255, 0)

# 		# mask = Image.fromarray(r3.astype(np.uint8))

# 		# "Stripe" the image
# 		# Convert each color in SVG
# 		data = np.asarray(image)
# 		svgs = []
# 		# import pdb; pdb.set_trace()
# 		for color in colors:
# 			# colorData = np.all(data != color, axis=-1).astype(np.uint8)
# 			distMax = 5
# 			colorData = (np.sum(abs(data-color), -1) < distMax).astype(np.uint8) * 255
# 			colorImage = Image.fromarray(colorData)

# 			eroded = colorImage.filter(ImageFilter.MaxFilter(5))
# 			erodedData = np.asarray(eroded)
# 			finalColorData = np.where(erodedData == 0, mask, colorData)
# 			finalColorImage = Image.fromarray(finalColorData.astype(np.uint8))
# 			finalColorImage.save('Wetu/media/imageToSVG.bmp', 'BMP')
# 			command = 'autotrace -centerline -output-format svg Wetu/media/imageToSVG.bmp'.split()
# 			process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
# 			stdout, stderr = process.communicate()
# 			svgs.append(stdout)
# 			if stderr:
# 				return json.dumps( {'state': 'error', 'svg': stdout, 'error': stderr } )

# 		# finalImage = image.point(lambda i: 255 if i > 128 else 0)
# 		# finalImage.save('Wetu/media/imageToSVG.bmp', 'BMP')
# 		# # command = 'autotrace -centerline -color-count 2 -output-format svg Wetu/media/imageToSVG.bmp'.split()
# 		# command = 'autotrace -centerline -output-format svg Wetu/media/imageToSVG.bmp'.split()

# 		# process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
# 		# stdout, stderr = process.communicate()

# 		return json.dumps( {'state': 'success', 'svgs': svgs, 'colors': colors} )

# 	except IOError:
# 		pass

# 	return json.dumps( { 'state': 'error', 'message': 'impossible to read image.'} )

def autoTrace(request, png, colors):

	if not request.user.is_authenticated():
		return json.dumps({'state': 'not_logged_in'})
	
	try:
		userProfile = UserProfile.objects.get(username=request.user.username)
	except UserProfile.DoesNotExist:
		return json.dumps( { 'status': 'error', 'message': 'The user profile does not exist.' } )
	
	if userProfile.banned:
		return json.dumps({'state': 'error', 'message': 'Your account has been suspended'})

	if not emailIsConfirmed(request, userProfile):
		return json.dumps({'state': 'error', 'message': 'Please confirm your email'})

	imgstr = re.search(r'base64,(.*)', png).group(1)
	imageData = imgstr.decode('base64')
	
	try:
		image = Image.open(StringIO.StringIO(imageData))
		image.save('Wetu/media/imageToSVG.bmp', 'BMP')
		# image.save('Wetu/media/imageToSVG.png', 'png')
		command = 'autotrace -centerline -background-color FFFFFF -color-count 0 -output-format svg Wetu/media/imageToSVG.bmp'.split()
		process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
		stdout, stderr = process.communicate()

		output = 'Wetu/media/output.html'

		with open(output, 'w') as out:
			
			out.write("""
			<html>
				<style>
					svg {
						stroke-width: 7px;
						stroke-linecap: round;
						stroke-linejoin: round;
					}
				</style>
				<body>
			""")

			out.write('<h4> image: </h4>')
			
			out.write(str(stdout) + '\n')

			out.write("""
				</body>
			</html>
			""")
			
		if stderr:
			return json.dumps( {'state': 'error', 'svg': stdout, 'error': stderr } )

		# finalImage = image.point(lambda i: 255 if i > 128 else 0)
		# finalImage.save('Wetu/media/imageToSVG.bmp', 'BMP')
		# # command = 'autotrace -centerline -color-count 2 -output-format svg Wetu/media/imageToSVG.bmp'.split()
		# command = 'autotrace -centerline -output-format svg Wetu/media/imageToSVG.bmp'.split()

		# process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
		# stdout, stderr = process.communicate()

		return json.dumps( {'state': 'success', 'svg': stdout, 'colors': colors} )

	except IOError:
		pass

	return json.dumps( { 'state': 'error', 'message': 'impossible to read image.'} )

