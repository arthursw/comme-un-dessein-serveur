# import datetime
# import logging
# import os
# import json

# from dajaxice.decorators import dajaxice_register
# from django.core import serializers
# from dajaxice.core import dajaxice_functions
# from django.contrib.auth.models import User
# from models import *
# from pprint import pprint
# import time

# import base64
# from Wetu import settings

# # from github import Github
# from git import Repo
# import requests
# import json

# import functools

# logger = logging.getLogger(__name__)

# with open('/data/secret_github.txt') as f:
# 	PASSWORD = base64.b64decode(f.read().strip())

# with open('/data/client_secret_github.txt') as f:
# 	CLIENT_SECRET = f.read().strip()

# # github = Github("arthurpub.sw@gmail.com", PASSWORD)
# # mainRepo = github.get_repo('comme-un-dessein-client')

# r = requests.get('https://api.github.com/users/arthursw?client_id=4140c547598d6588fd37&client_secret=' + CLIENT_SECRET)
# if not r.ok:
# 	print 'Error: impossible to connect to github.'

# @dajaxice_register
# def githubRequest(request, githubRequest):
# 	r = requests.get('https://api.github.com/' + githubRequest)
# 	if(r.ok):
# 		return json.dumps(r)
# 	return json.dumps( { 'state': 'error', 'message': 'Invalid request.', 'request': r } )


# @dajaxice_register
# @checkDebug
# def connectToGithub(request):
# 	state = '' + str(random.random())
# 	r = requests.get('https://github.com/login/oauth/authorize', data={ 'client_id': '4140c547598d6588fd37', 'scope': ['user'], 'state': state } )

# 	rj = r.json()
# 	if 'state' not in rj or rj['state'] != state:
# 		print 'ERROR'

# 	code = rj['code']


# 	s = requests.Session()
# 	s.post('https://github.com/login/oauth/access_token', data={ 'client_id': '4140c547598d6588fd37', 'client_secret': CLIENT_SECRET, 'code': code } )
# 	r = requests.get('https://api.github.com/user', params={ 'arthursw': ACCESS_TOKEN })
# 	if not r.ok:
# 		print 'Error: impossible to connect to github.'

# 	return