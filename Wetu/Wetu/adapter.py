
from django.conf import settings
from allauth.account.adapter import DefaultAccountAdapter
from django.core.exceptions import ValidationError

class AccountAdapterCD(DefaultAccountAdapter):
    
    def clean_password(self, password, user):
        if len(password) > 4:
            return password
        else:
            raise ValidationError("The password is too short.")
    
    # def get_login_redirect_url(self, request):
    # 	print(request)
    # 	import pdb; pdb.set_trace();
    #     path = "/accounts/{username}/"
    #     return path.format(username=request.user.username)