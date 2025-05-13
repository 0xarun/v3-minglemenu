from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from .models import Store
from django.conf import settings
from django.utils.crypto import get_random_string

class CustomUserAdmin(UserAdmin):
    def login(self, request, extra_context=None):
        settings.SESSION_COOKIE_NAME = settings.ADMIN_SESSION_COOKIE_NAME
        # Ensure CSRF token is present
        if not request.session.get('CSRF_COOKIE'):
            request.session['CSRF_COOKIE'] = get_random_string(32)
        return super().login(request, extra_context)

admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)


@admin.register(Store)
class StoreAdmin(admin.ModelAdmin):
    list_display = ('store_id', 'store_name', 'owner')
    list_filter = ('owner',)
    search_fields = ('store_id', 'store_name', 'owner__username')
    ordering = ('-id',)