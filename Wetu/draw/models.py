
from mongoModels import *

from django.contrib.auth.models import User
from django.db import models
from allauth.account.models import EmailAddress
from allauth.socialaccount.models import SocialAccount
from allauth.account.signals import user_logged_in
from allauth.account.signals import user_signed_up
from django.dispatch import receiver

import urllib
import hashlib

from mongoengine import *
import datetime

# @receiver(user_signed_up, dispatch_uid="_allauth.user_signed_up")
# def createUserProfile(sender, user, **kwargs):
#     profile = UserProfile(username=user.username)
#     profile.save()
#     return

# class UserProfile(Document):
#     username = StringField(required=True, unique=True)
#     admin = BooleanField(default=False)
#     commeUnDesseinCoins = IntField(default=0)
#     votes = ListField(ReferenceField('Vote', reverse_delete_rule=PULL))

#     def profile_image_url(self):

#         user = User.objects.get(username=self.username)

#         socialAccount = SocialAccount.objects.filter(user_id=user.id).first()

#         if socialAccount:
#             if socialAccount.provider == 'facebook':
#                 return "http://graph.facebook.com/{}/picture?width=64&height=64".format(socialAccount.uid)
#             elif socialAccount.provider == 'google':
#                 return socialAccount.extra_data['picture']
#             else:
#                 defaultUrl = urllib.quote_plus("http://www.mediafire.com/convkey/7e65/v9zp48cdnsccr4d6g.jpg")
#                 return "http://www.gravatar.com/avatar/{}?s=64&d={}".format(hashlib.md5(user.email).hexdigest(), defaultUrl)

#     meta = {
#         'indexes': [[ ("username", 1)]]
#     }


# --- django-allauth : sqlite --- #

# import pdb; pdb.set_trace()
# object.__dict___

# to update the database after modifying model, use south:
# http://south.readthedocs.org/en/latest/tutorial/part1.html
# python manage.py schemamigration draw --auto
# python manage.py migrate draw

# class UserProfile(models.Model):
#     user = models.OneToOneField(User, related_name='profile')
#     admin = models.BooleanField(default=False)
#     commeUnDesseinCoins = models.IntegerField(default=0)

#     def __unicode__(self):
#         return "{}'s profile".format(self.user.userType)

#     class Meta:
#         db_table = 'user_profile'

#     def account_verified(self):
#         if self.user.is_authenticated:
#             result = EmailAddress.objects.filter(email=self.user.email)
#             if len(result):
#                 return result[0].verified
#         return False

#     def profile_image_url(self):

#         fb_uid = SocialAccount.objects.filter(user_id=self.user.id, provider='facebook')

#         if len(fb_uid):
#             return "http://graph.facebook.com/{}/picture?width=64&height=64".format(fb_uid[0].uid)

#         socialAccount = self.user.socialaccount_set.filter(provider='google')

#         if len(socialAccount)>0:
#             return socialAccount[0].extra_data['picture']

#         # google_uid = SocialAccount.objects.filter(user_id=self.user.id, provider='google')
#         # if len(google_uid):
#         #     return "https://plus.google.com/s2/photos/profile/{}?sz=64".format(google_uid[0].uid)

#         defaultUrl = urllib.quote_plus("http://www.mediafire.com/convkey/7e65/v9zp48cdnsccr4d6g.jpg")

#         return "http://www.gravatar.com/avatar/{}?s=64&d={}".format(hashlib.md5(self.user.email).hexdigest(), defaultUrl)

#     # @receiver(user_logged_in)
#     # def user_logged_in_(request, user, sociallogin, **kwargs):
#         # import pdb; pdb.set_trace()
#         # google image accessible via  sociallogin.account.extra_data['picture']
#         # return

# User.profile = property(lambda u: UserProfile.objects.get_or_create(user=u)[0])
