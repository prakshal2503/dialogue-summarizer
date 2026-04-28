"""
Custom middleware for security and authentication.
"""
from django.shortcuts import redirect
from django.conf import settings
from django.contrib import messages

EXEMPT_URLS = [
    '/login/',
    '/register/',
    '/logout/',
    '/static/',
    '/media/',
    '/captcha/',
    '/account-deleted/',
]


class LoginRequiredMiddleware:
    """Redirect unauthenticated users to login page."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path_info
        is_exempt = any(path.startswith(url) for url in EXEMPT_URLS)

        if not is_exempt and not request.session.get('user_id'):
            return redirect(settings.LOGIN_URL + f'?next={path}')

        response = self.get_response(request)
        return response


class SecurityHeadersMiddleware:
    """Add security headers to all responses."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-XSS-Protection'] = '1; mode=block'
        response['X-Frame-Options'] = 'DENY'
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        response['Permissions-Policy'] = 'geolocation=(), microphone=(), camera=()'
        return response
