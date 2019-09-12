import datetime
import urllib
import hashlib

from django.contrib.auth.models import User
from django.db import models
from allauth.account.models import EmailAddress
from allauth.socialaccount.models import SocialAccount
from allauth.account.signals import user_logged_in
from allauth.account.signals import user_signed_up
from django.dispatch import receiver

from mongoengine import *

class Vote(Document):
    author = ReferenceField('UserProfile', required=True)   #, reverse_delete_rule=CASCADE) # see register_delete_rule after UserProfile
    drawing = ReferenceField('Drawing')                     #, reverse_delete_rule=CASCADE) # see register_delete_rule after Drawing
    positive = BooleanField(default=True)
    date = DateTimeField(default=datetime.datetime.now, required=True)
    emailConfirmed = BooleanField(default=False)

    meta = {
        'indexes': [ "#author", "emailConfirmed" ]
    }

class Comment(Document):
    author = ReferenceField('UserProfile', required=True)   #, reverse_delete_rule=CASCADE) # see register_delete_rule after UserProfile
    drawing = ReferenceField('Drawing')                     #, reverse_delete_rule=CASCADE) # see register_delete_rule after Drawing
    date = DateTimeField(default=datetime.datetime.now, required=True)
    emailConfirmed = BooleanField(default=False)
    text = StringField(required=True)

    meta = {
        'indexes': [ "#author", "emailConfirmed" ]
    }

@receiver(user_signed_up, dispatch_uid="_allauth.user_signed_up")
def createUserProfile(sender, user, **kwargs):
    profile = UserProfile(username=user.username)
    profile.save()
    return

class UserProfile(Document):
    username = StringField(required=True, unique=True)
    admin = BooleanField(default=False)
    commeUnDesseinCoins = IntField(default=0)
    emailConfirmed = BooleanField(default=False)
    disableEmail = BooleanField(default=False)
    votes = ListField(ReferenceField('Vote', reverse_delete_rule=PULL))
    comments = ListField(ReferenceField('Comment', reverse_delete_rule=PULL))
    banned = BooleanField(default=False)

    def profile_image_url(self):

        user = User.objects.get(username=self.username)

        socialAccount = SocialAccount.objects.filter(user_id=user.id).first()

        if socialAccount:
            if socialAccount.provider == 'facebook':
                return "http://graph.facebook.com/{}/picture?width=64&height=64".format(socialAccount.uid)
            elif socialAccount.provider == 'google':
                return socialAccount.extra_data['picture']
            else:
                defaultUrl = urllib.quote_plus("http://www.mediafire.com/convkey/7e65/v9zp48cdnsccr4d6g.jpg")
                return "http://www.gravatar.com/avatar/{}?s=64&d={}".format(hashlib.md5(user.email).hexdigest(), defaultUrl)

    meta = {
        'indexes': [ "#username" ]
    }

UserProfile.register_delete_rule(Vote, 'author', CASCADE)
UserProfile.register_delete_rule(Comment, 'author', CASCADE)

class Drawing(Document):
    clientId = StringField(required=True, unique=True)

    city = StringField(required=True)
    planetX = DecimalField(required=True)
    planetY = DecimalField(required=True)
    box = PolygonField()
    rType = StringField(default='Drawing')
    owner = StringField(required=True)
    status = StringField(default='draft', required=True)
    paths = ListField(ReferenceField('Path')) # UNUSED, to be deleted (but error when delete?)
    svg = StringField()
    pathList = ListField(StringField())
    bounds = StringField()

    date = DateTimeField(default=datetime.datetime.now, required=True)
    votes = ListField(ReferenceField('Vote', reverse_delete_rule=PULL))
    comments = ListField(ReferenceField('Comment', reverse_delete_rule=PULL))
    
    title = StringField()
    description = StringField()

    discussionId = IntField()

    # lastUpdate = DateTimeField(default=datetime.datetime.now)
    
    meta = {
        'indexes': [
            "city",
            "owner",
            "status",
            [ ("planetX", 1), ("planetY", 1), ("box", "2dsphere") ]
        ]
    }

Drawing.register_delete_rule(Vote, 'drawing', CASCADE)
Drawing.register_delete_rule(Comment, 'drawing', CASCADE)

class Path(Document):
    clientId = StringField(required=True, unique=True)

    city = StringField(required=True)
    planetX = DecimalField(required=True)
    planetY = DecimalField(required=True)
    box = PolygonField(required=True)
    points = LineStringField()
    rType = StringField(default='Path')
    owner = StringField(required=True)
    
    date = DateTimeField(default=datetime.datetime.now)
    lastUpdate = DateTimeField(default=datetime.datetime.now)
    object_type = StringField(default='brush')
    lock = StringField(default=None)
    needUpdate = BooleanField(default=False)

    isDraft = BooleanField(default=True)
    drawing = ReferenceField('Drawing', reverse_delete_rule=NULLIFY)

    # areas = ListField(ReferenceField('Area'))

    data = StringField(default='')

    meta = {
        'indexes': [
            "city",
            "drawing",
            "owner",
            [ ("planetX", 1), ("planetY", 1), ("points", "2dsphere") ]
        ]
    }

Path.register_delete_rule(Drawing, 'paths', PULL)

class Box(Document):
    clientId = StringField(required=True, unique=True)

    city = StringField(required=True)
    planetX = DecimalField(required=True)
    planetY = DecimalField(required=True)
    box = PolygonField(required=True)
    rType = StringField(default='Box')
    owner = StringField()
    date = DateTimeField(default=datetime.datetime.now)
    lastUpdate = DateTimeField(default=datetime.datetime.now)
    object_type = StringField()

    url = URLField(required=True, unique=True)
    restrictedArea = BooleanField(default=False)
    disableToolbar = BooleanField(default=False)
    loadEntireArea = BooleanField(default=False)

    # module = ReferenceField('Module')

    # deprecated: put in data
    # url = URLField(verify_exists=True, required=False)

    # message = StringField()
    # areas = ListField(ReferenceField('Area'))

    data = StringField(default='')

    meta = {
        'indexes': [
            "city",
            "owner",
            [ ("planetX", 1), ("planetY", 1), ("box", "2dsphere") ]
        ]
    }

class AreaToUpdate(Document):
    city = StringField(required=True)
    planetX = DecimalField(required=True)
    planetY = DecimalField(required=True)
    box = PolygonField(required=True)

    rType = StringField(default='AreaToUpdate')
    # areas = ListField(ReferenceField('Area'))

    meta = {
        'indexes': [
            "city",
            [ ("planetX", 1), ("planetY", 1), ("box", "2dsphere") ]
        ]
    }

class Div(Document):
    clientId = StringField(required=True, unique=True)

    city = StringField(required=True)
    planetX = DecimalField(required=True)
    planetY = DecimalField(required=True)
    box = PolygonField(required=True)
    rType = StringField(default='Div')
    owner = StringField()
    date = DateTimeField(default=datetime.datetime.now)
    lastUpdate = DateTimeField(default=datetime.datetime.now)
    object_type = StringField()
    lock = StringField(default=None)

    # deprecated: put in data
    url = StringField(required=False)
    message = StringField()

    # areas = ListField(ReferenceField('Area'))

    data = StringField(default='')

    meta = {
        'indexes': [
            "city",
            "owner",
            [ ("planetX", 1), ("planetY", 1), ("box", "2dsphere") ]
        ]
    }

class Tool(Document):
    name = StringField(unique=True)
    className = StringField(unique=True)
    originalName = StringField()
    originalClassName = StringField()
    owner = StringField()
    source = StringField()
    compiledSource = StringField()
    nRequests = IntField(default=0)
    isTool = BooleanField()
    # requests = ListField(StringField())
    accepted = BooleanField(default=False)

    meta = {
        'indexes': [ "accepted", "name" ]
    }

class Module(Document):
    name = StringField(unique=True)
    moduleType = StringField()
    category = StringField()
    description = StringField()
    repoName = StringField(unique=True)
    owner = StringField()
    url = StringField()
    githubURL = URLField()
    iconURL = StringField()
    thumbnailURL = StringField()
    source = StringField()
    compiledSource = StringField()
    local = BooleanField()
    # lock = ReferenceField('Box', required=False)
    lastUpdate = DateTimeField(default=datetime.datetime.now)

    accepted = BooleanField(default=False)

    meta = {
        'indexes': [ "accepted", "moduleType", "name" ]
    }

class Site(Document):
    name = StringField(unique=True, required=True)
    box = ReferenceField(Box, required=True, reverse_delete_rule=CASCADE)

    # deprecated: put in data
    restrictedArea = BooleanField(default=False)
    disableToolbar = BooleanField(default=False)
    loadEntireArea = BooleanField(default=False)

    data = StringField(default='')

    meta = {
        'indexes': [ "name" ]
    }

class City(Document):
    owner = StringField(required=True)
    name = StringField(required=True)
    message = StringField(required=False)
    public = BooleanField(default=False)
    strokeWidth = DecimalField(default=7)
    width = DecimalField(default=4000)
    height = DecimalField(default=3000)
    finished = BooleanField(default=False)

    meta = {
        'indexes': [ "owner", "public", "name" ]
    }

# class Area(Document):
#     x = DecimalField()
#     y = DecimalField()
#     items = ListField(GenericReferenceField())
#     # paths = ListField(ReferenceField(Path))
#     # boxes = ListField(ReferenceField(Box))
#     # divs = ListField(ReferenceField(Div))
#     # areasToUpdate = ListField(ReferenceField(AreaToUpdate))

#     meta = {
#         'indexes': [[ ("x", 1), ("y", 1) ]]
#     }
