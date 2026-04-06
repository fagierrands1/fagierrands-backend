from django.http import HttpResponse
from django.conf import settings

class CorsMiddleware:
    """
    Custom CORS middleware to handle preflight requests and CORS headers
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Handle preflight OPTIONS requests
        if request.method == 'OPTIONS':
            response = HttpResponse()
            response['Access-Control-Allow-Origin'] = self.get_allowed_origin(request)
            response['Access-Control-Allow-Methods'] = 'GET, POST, PUT, PATCH, DELETE, OPTIONS'
            response['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-Requested-With, Accept, Origin'
            response['Access-Control-Allow-Credentials'] = 'true'
            response['Access-Control-Max-Age'] = '86400'  # 24 hours
            return response
        
        # Process the request
        response = self.get_response(request)
        
        # Add CORS headers to all responses
        response['Access-Control-Allow-Origin'] = self.get_allowed_origin(request)
        response['Access-Control-Allow-Methods'] = 'GET, POST, PUT, PATCH, DELETE, OPTIONS'
        response['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-Requested-With, Accept, Origin'
        response['Access-Control-Allow-Credentials'] = 'true'
        
        return response
    
    def get_allowed_origin(self, request):
        """
        Get the allowed origin based on the request
        """
        origin = request.META.get('HTTP_ORIGIN')
        
        # Temporarily allow all origins for debugging
        if origin:
            return origin
        
        # List of allowed origins (for when we tighten security later)
        allowed_origins = [
            'https://fagierrands-website.onrender.com',
            'https://fagierrands-backend-xwqi.onrender.com',
            'https://fagierrands-x9ow.vercel.app',
            'https://fagierrands.vercel.app',
            'https://fagierrand.fagitone.com',
            'http://localhost:3000',
            'http://localhost:5173',
            'http://127.0.0.1:3000',
        ]
        
        if origin in allowed_origins:
            return origin
        
        # Check for vercel.app subdomains
        if origin and origin.endswith('.vercel.app'):
            return origin
            
        # Default fallback
        return '*'  # Temporarily allow all
