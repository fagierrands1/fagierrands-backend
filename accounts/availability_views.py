from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions, status
from django.contrib.auth import get_user_model

User = get_user_model()

class AssistantAvailabilityView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        if getattr(user, 'user_type', 'user') != 'assistant':
            return Response({'error': 'Only assistants can access availability'}, status=status.HTTP_403_FORBIDDEN)
        return Response({'is_online': getattr(user, 'is_online', False)})

    def patch(self, request):
        user = request.user
        if getattr(user, 'user_type', 'user') != 'assistant':
            return Response({'error': 'Only assistants can update availability'}, status=status.HTTP_403_FORBIDDEN)
        is_online = request.data.get('is_online')
        if isinstance(is_online, bool):
            # Persist field if present, otherwise return an error indicating migration needed
            if not hasattr(user, 'is_online'):
                return Response({'error': 'Server not updated for availability yet. Please run migrations.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            user.is_online = is_online
            user.save(update_fields=['is_online'])
            return Response({'is_online': user.is_online})
        return Response({'error': 'is_online must be boolean'}, status=status.HTTP_400_BAD_REQUEST)