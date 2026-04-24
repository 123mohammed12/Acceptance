import os
from django.http import JsonResponse

class AppSecretMiddleware:
    """
    Middleware to ensure that requests to the API come from the legitimate mobile app
    by checking for a specific custom header.
    """
    def __init__(self, get_response):
        self.get_response = get_response
        self.secret_key = os.environ.get('JAMATY_APP_SECRET', 'JAMATY_SECURE_API_2026_V1')

    def __call__(self, request):
        # We only want to protect API endpoints
        if request.path.startswith('/api/'):
            # The header 'X-App-Secret' becomes 'HTTP_X_APP_SECRET' in Django's request.META
            client_secret = request.META.get('HTTP_X_APP_SECRET')
            
            # For local development or admin panel we might want to bypass,
            # but since it's /api/, we enforce it.
            if client_secret != self.secret_key:
                return JsonResponse(
                    {'error': 'Unauthorized access. App secret is missing or invalid.', 'code': 'INVALID_APP_SECRET'},
                    status=403
                )

        response = self.get_response(request)
        return response
