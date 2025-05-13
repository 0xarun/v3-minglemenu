from allauth.account.adapter import DefaultAccountAdapter
from django.conf import settings

class CustomAccountAdapter(DefaultAccountAdapter):
    def login(self, request, user):
        # Set the session cookie name to the app session
        settings.SESSION_COOKIE_NAME = 'app_sessionid'
        super().login(request, user)