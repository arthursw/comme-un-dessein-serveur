# -*- coding: utf-8 -*-

from django.shortcuts import get_object_or_404, get_list_or_404, render_to_response, render
from django.http import HttpResponseRedirect, HttpResponse
from django.core.urlresolvers import reverse
from django.template import RequestContext
from django.shortcuts import redirect
from django.contrib.sites.models import Site
from django.contrib.sites import shortcuts

from allauth.account.views import SignupView
from allauth.account.forms import LoginForm

from draw import ajax
from ajax import getPositiveVoteThreshold, getNegativeVoteThreshold, getVoteMinDuration, makeBoundsFromBox
from math import floor
from django.views.decorators.csrf import csrf_exempt
from models import *

from Wetu import settings

# from django.http import JsonResponse
import json

# from socketio.namespace import BaseNamespace
# from sockets import ChatNamespace, DrawNamespace
# from socketio import socketio_manage

def addCityToResult(result, city):
	result['city'] = city.name
	result['cityFinished'] = city.finished
	result['cityEventDate'] = str(city.eventDate)
	result['cityEventLocation'] = city.eventLocation
	result['cityMessage'] = city.message
	result['cityStrokeWidth'] = str(city.strokeWidth)
	result['cityWidth'] = city.width
	result['cityHeight'] = city.height
	result['cityPixelPerMm'] = city.pixelPerMm
	result['cityUseSVG'] = city.useSVG
	result['cityMode'] = city.mode or 'CommeUnDessein'
	return

def index(request, site=None, owner=None, cityName=None, x=0, y=0, useDebugFiles=False, drawingMode=None, visit=False, pk=None, tilePk=None):

	# if not visit and not request.user.is_authenticated():
	# 	return render_to_response(	"welcome.html", {}, RequestContext(request) )
	
	result = {}
	profileImageURL = ''

	try:
		userProfile = UserProfile.objects.get(username=request.user.username)
		profileImageURL = userProfile.profile_image_url
		result['userIsAdmin'] = userProfile.admin
		result['emailConfirmed'] = userProfile.emailConfirmed
	except UserProfile.DoesNotExist:
		print 'user profile does not exist.'

	connectedToGithub = False
	githubLogin = ''
	# try:
	# 	socialAccount = SocialAccount.objects.filter(user_id=request.user.id, provider='github')[:1].get()
	# 	if socialAccount:
	# 		connectedToGithub = True
	# 		githubLogin = socialAccount.extra_data['login']
	# except:
	# 	print 'can not load social account.'

	
	if site:
		result = loadSite(request, site)

	# siteDomain = Site.objects.get_current().domain
	siteDomain = settings.DOMAIN # shortcuts.get_current_site(request).domain

	result['profileImageURL'] = 'static/images/face.png'
	# result['profileImageURL'] = profileImageURL
	result['connectedToGithub'] = connectedToGithub
	result['githubLogin'] = githubLogin
	result['drawingMode'] = drawingMode
	result['useDebugFiles'] = useDebugFiles
	result['application'] = settings.APPLICATION
	result['isCommeUnDessein'] = settings.APPLICATION == 'COMME_UN_DESSEIN'
	
	city = None
	if cityName:
		try:
			city = City.objects.get(name=cityName)
			addCityToResult(result, city)
		except:
			return redirect('http://' + siteDomain)
			print('City not found')

	if pk:
		result['drawingImageURL'] = siteDomain + '/static/drawings/' + pk + '.png'
		result['drawingPk'] = pk
		try:
			drawing = Drawing.objects.get(pk=pk)
			result['drawingTitle'] = drawing.title
			result['drawingDescription'] = drawing.title + ' by ' + drawing.owner + ' on Comme un Dessein.'
			result['drawingAuthor'] = drawing.owner
			try:
				city = City.objects.get(pk=drawing.city)
				addCityToResult(result, city)
				bounds = makeBoundsFromBox(city, drawing.box)
				result['bounds'] = json.dumps(bounds)
			except City.DoesNotExist:
				print('City not found')
			
		except:
			print('Drawing not found')
	elif tilePk:
		result['tilePk'] = tilePk
		try:
			tile = Tile.objects.get(pk=tilePk)
			try:
				city = City.objects.get(pk=tile.city)
				addCityToResult(result, city)
				bounds = makeBoundsFromBox(city, tile.box)
				result['bounds'] = json.dumps(bounds)
			except City.DoesNotExist:
				print('City not found')
			
		except:
			print('Tile not found')
	else:
		result['drawingImageURL'] = 'http://commeundessein.co/static/images/Wetu1200x630.png'
		result['drawingTitle'] = 'Comme un Dessein'
		result['drawingDescription'] = u'Comme un Dessein est un dispositif qui invite les citoyens à composer une œuvre collective et utopique, à l’aide d’une interface web connectée à un traceur vertical.'

	result['positiveVoteThreshold'] = getPositiveVoteThreshold(city)
	result['negativeVoteThreshold'] = getNegativeVoteThreshold(city)
	result['voteMinDuration'] = getVoteMinDuration(city)

	response = render_to_response(	"index.html", result, RequestContext(request) )
	return response

def live(request):
    return redirect('https://youtu.be/NDi77EhzS7k')

def disableEmail(request, activation=False):

	result = {}
	
	result['title'] = 'Desactivation des notifications email'

	try:
		userProfile = UserProfile.objects.get(username=request.user.username)
		userProfile.disableEmail = not activation
		userProfile.save()
		if activation:
			result['message'] = u'Votre receverez à nouveau des notifications de la part de Comme un Dessein.'
		else:
			result['message'] = u'Votre ne receverez plus de notification de la part de Comme un Dessein. Pour réactivez les notifications, allez sur https://commeundessein.co/email/reactivation/'
	except UserProfile.DoesNotExist:
		result['message'] = u"Votre compte n'a pas été trouvé, veuillez vous connecter sur la page d'accueil https://commeundessein.co/ puis revenir sur cette page ."
	
	return render_to_response(	"message.html", result, RequestContext(request) )

def about(request):
	return render_to_response(	"about.html", {}, RequestContext(request) )

def welcome(request):
	result = {}
	result['is_authenticated'] = request.user.is_authenticated()

	try:
		city = City.objects.get(name='rennes')
		result['nParticipants'] = city.nParticipants
		result['squareMeters'] = city.squareMeters
	except City.DoesNotExist:
		pass

	if settings.APPLICATION == 'COMME_UN_DESSEIN':
		return render_to_response(	"welcome-commeundessein.html", result, RequestContext(request) )

	return render_to_response(	"welcome.html", result, RequestContext(request) )

def termsOfService(request):
	return render_to_response(	"terms-of-service.html", {}, RequestContext(request) )

def privacyPolicy(request):
	return render_to_response(	"privacy-policy.html", {}, RequestContext(request) )

# def connections(request):
# 	if not request.user.is_authenticated():
# 		return render_to_response(	"connections.html", {}, RequestContext(request) )
# 	return index(request)

def ajaxCall(request):
	# import pdb; pdb.set_trace()
	if request.is_ajax():
		data = json.loads(request.POST.get('data'))
		function = data["function"]
		args = data["args"]

		print "ajaxCall"
		print function

		if args is None:
			args = {}
		args['request'] = request
		result = getattr(ajax, function)(**args)
		return HttpResponse(result, content_type="application/json")
		# return JsonResponse(result)
	else:
		return HttpResponse("Fail")

@csrf_exempt
def ajaxCallNoCSRF(request):
	data = json.loads(request.POST.get('data'))
	function = data["function"]
	if function == "getNextValidatedDrawing" or function == "setDrawingStatusDrawn":
		args = data["args"]
		print "ajaxCallNoCSRF"
		print function
		if args is None:
			args = {}
		args['request'] = request
		result = getattr(ajax, function)(**args)
		return HttpResponse(result, content_type="application/json")
	return HttpResponse("Fail")

# socketio_manage(request.environ, {'': BaseNamespace, '/chat': ChatNamespace, '/draw': DrawNamespace}, request)

# class CustomSignupView(SignupView):
#     # here we add some context to the already existing context
#     def get_context_data(self, **kwargs):
#         # we get context data from original view
#         context = super(CustomSignupView, self).get_context_data(**kwargs)
#         context['login_form'] = LoginForm() # add form to context
#         return context

# connection = CustomSignupView.as_view()

