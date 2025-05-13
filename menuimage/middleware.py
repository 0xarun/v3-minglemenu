from django.contrib.sessions.middleware import SessionMiddleware
from django.conf import settings
from django.urls import resolve
from django.utils.crypto import get_random_string

class SeparateAdminSessionMiddleware(SessionMiddleware):
    def process_request(self, request):
        resolved = resolve(request.path)
        if resolved.app_name == 'admin':
            settings.SESSION_COOKIE_NAME = settings.ADMIN_SESSION_COOKIE_NAME
        else:
            settings.SESSION_COOKIE_NAME = 'app_sessionid'
        
        # Call the parent method to process the session
        super().process_request(request)
        
        # Ensure CSRF token is present
        if not request.session.get('CSRF_COOKIE'):
            request.session['CSRF_COOKIE'] = get_random_string(32)

    def process_response(self, request, response):
        # Ensure the CSRF cookie is set in the response
        if request.session.get('CSRF_COOKIE'):
            response.set_cookie('csrftoken', request.session['CSRF_COOKIE'], httponly=True)
        return super().process_response(request, response)