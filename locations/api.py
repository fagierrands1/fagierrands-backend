from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions
from django.conf import settings

class MapConfigView(APIView):
    """
    API endpoint that returns the map configuration for the frontend
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """
        Return the map configuration from settings
        """
        map_config = getattr(settings, 'MAP_CONFIG', {
            'DEFAULT_CENTER': (-1.2921, 36.8219),  # Nairobi coordinates
            'DEFAULT_ZOOM': 12,
            'MIN_ZOOM': 3,
            'MAX_ZOOM': 18,
        })
        
        # Add OpenStreetMap tile information for the frontend
        map_config['TILES'] = {
            'url': 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
            'attribution': '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        }
        
        return Response(map_config)